from pyflink.datastream import StreamExecutionEnvironment, CheckpointingMode
from pyflink.table import EnvironmentSettings, StreamTableEnvironment  
from env import CASSANDRA_CONTACT_POINTS, CASSANDRA_PORT, CASSANDRA_KEYSPACE, CASSANDRA_TABLE, CASSANDRA_USERNAME, CASSANDRA_PASSWORD, KAFKA_BOOTSTRAP_SERVERS, POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, DEBEZIUM_CONNECT_URL, DEBEZIUM_CONNECTOR_CONFIG_FILE, FLINK_CONNECTOR_KAFKA_JAR, FLINK_CONNECTOR_CASSANDRA_JAR, FLINK_JSON_JAR
import psycopg2
import json
import requests
from fastapi import HTTPException
from enums import JobName
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from confluent_kafka import Producer
from config import FlinkJobConfig
from logger import logger
import pathlib

## Connect to cassandra
def get_cassandra_session():
    cluster = Cluster(
        CASSANDRA_CONTACT_POINTS, 
        port=CASSANDRA_PORT,
        auth_provider=PlainTextAuthProvider(
            username=CASSANDRA_USERNAME,
            password=CASSANDRA_PASSWORD
        )
    )
    session = cluster.connect()
    return session


def get_kafka_producer():
    return Producer({'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS})

def run_flink_job(config: FlinkJobConfig):
    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_parallelism(config.parallelism)
    env.enable_checkpointing(config.checkpoint_interval, CheckpointingMode.EXACTLY_ONCE)

    ## Create table environment
    settings = EnvironmentSettings.new_instance() \
    .in_streaming_mode() \
    .build()

    table_env = StreamTableEnvironment.create(env, environment_settings=settings)

    ### add reqd. jar files
    JAR_FILE_PREFIX = "file://flink-connectors"
    table_env.get_config().get_configuration().set_string(
        "pipeline.jars", 
        f"{JAR_FILE_PREFIX}/{FLINK_CONNECTOR_KAFKA_JAR};"
        f"{JAR_FILE_PREFIX}/{FLINK_CONNECTOR_CASSANDRA_JAR};"
        f"{JAR_FILE_PREFIX}/{FLINK_JSON_JAR}"
    )
    job_name = config.job_name

    if config.job_name == JobName.KAFKA_TO_CASSANDRA.value:
        # Create a table for each source table
        for table in ['likes', 'shards', 'followers', 'comments']:
            table_env.execute_sql(f"""
                CREATE TABLE kafka_source_{table} (
                    user_id STRING,
                    activity_type STRING,
                    timestamp BIGINT,
                    target_id STRING,
                    target_type STRING,
                    metadata MAP<STRING, STRING>,
                    source_table STRING,
                    proctime AS PROCTIME()
                ) WITH (
                    'connector' = 'kafka',
                    'topic' = 'postgres.codeshard.{table}',
                    'properties.bootstrap.servers' = '{KAFKA_BOOTSTRAP_SERVERS}',
                    'properties.group.id' = 'flink-group',
                    'scan.startup.mode' = 'latest-offset',
                    'format' = 'json'
                )
            """)

        # Create a view that unions all source tables
        table_env.execute_sql("""
            CREATE VIEW kafka_source AS
            SELECT * FROM kafka_source_likes
            UNION ALL
            SELECT * FROM kafka_source_shards
            UNION ALL
            SELECT * FROM kafka_source_users
            UNION ALL
            SELECT * FROM kafka_source_comments
        """)

        table_env.execute_sql(f"""
            CREATE TABLE cassandra_sink (
                user_id STRING,
                activity_id STRING,
                activity_type STRING,
                timestamp TIMESTAMP(3),
                target_id STRING,
                target_type STRING,
                metadata MAP<STRING, STRING>,
                PRIMARY KEY (user_id, activity_id) NOT ENFORCED
            ) WITH (
                'connector' = 'cassandra',
                'hosts' = '{','.join(CASSANDRA_CONTACT_POINTS)}',
                'port' = '{CASSANDRA_PORT}',
                'keyspace' = '{CASSANDRA_KEYSPACE}',
                'table' = '{CASSANDRA_TABLE}'
                {',' + f"'username' = '{CASSANDRA_USERNAME}'" if CASSANDRA_USERNAME else ""},
                {',' + f"'password' = '{CASSANDRA_PASSWORD}'" if CASSANDRA_PASSWORD else ""}
            )
        """)

        table_env.execute_sql(f"""
            INSERT INTO cassandra_sink
            SELECT 
                user_id,
                CAST(UUID() AS STRING) AS activity_id,
                activity_type,
                TO_TIMESTAMP(FROM_UNIXTIME(timestamp / 1000)),
                target_id,
                target_type,
                metadata
            FROM kafka_source
        """).wait()
    else:
        raise ValueError(f"Invalid job name: {job_name}")


def get_postgres_connection():
    try: 
        conn = psycopg2.connect(
            host= POSTGRES_HOST,
            port= POSTGRES_PORT,
            user= POSTGRES_USER,
            password= POSTGRES_PASSWORD,
            dbname= POSTGRES_DB
            ) 
        return conn
    except Exception as e:
        print(f"Error connecting to postgres: {e}")
        raise HTTPException(status_code=500, detail="Failed to connect to postgres : {str(e)}")
    
async def setup_debezium_connector():
    try: 
        # First verify Debezium Connect is available
        health_check = requests.get(f"{DEBEZIUM_CONNECT_URL}/")
        if health_check.status_code != 200:
            raise Exception(f"Debezium Connect is not healthy. Status code: {health_check.status_code}")

        with open(DEBEZIUM_CONNECTOR_CONFIG_FILE, "r") as f:
            config = json.load(f)
            
        # Update configuration with environment variables
        config["config"]["database.hostname"] = POSTGRES_HOST
        config["config"]["database.port"] = POSTGRES_PORT
        config["config"]["database.user"] = POSTGRES_USER
        config["config"]["database.password"] = POSTGRES_PASSWORD
        config["config"]["database.dbname"] = POSTGRES_DB
        
        # Check if connector already exists
        response = requests.get(f"{DEBEZIUM_CONNECT_URL}/connectors/postgres-connector")
        if response.status_code == 200:
            print("Debezium connector already exists")
            return {"status": "success", "message": "Debezium connector already exists"}
            
        # Create new connector
        response = requests.post(
            f"{DEBEZIUM_CONNECT_URL}/connectors",
            headers={"Content-Type": "application/json"},
            json=config
        )
        
        if response.status_code not in [200, 201]:
            raise Exception(f"Failed to create connector. Status: {response.status_code}, Response: {response.text}")
            
        return {"status": "success", "message": "Debezium connector created successfully"}
        
    except requests.exceptions.ConnectionError as e:
        print(f"Connection error to Debezium Connect: {e}")
        raise Exception(f"Failed to connect to Debezium Connect: {str(e)}")
    except Exception as e:
        print(f"Error setting up Debezium connector: {e}")
        raise Exception(f"Failed to set up Debezium connector: {str(e)}")


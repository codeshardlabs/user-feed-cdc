
from pyflink.datastream import StreamExecutionEnvironment, CheckpointingMode
from pyflink.table import EnvironmentSettings, StreamTableEnvironment  
import env
import psycopg2
import json
import requests
from fastapi import HTTPException
from enums import JobName
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from confluent_kafka import Producer
from config import FlinkJobConfig

## Connect to cassandra
def get_cassandra_session():
    cluster = Cluster(
        env.CASSANDRA_CONTACT_POINTS, 
        port=env.CASSANDRA_PORT,
        auth_provider=PlainTextAuthProvider(
            username=env.CASSANDRA_USERNAME,
            password=env.CASSANDRA_PASSWORD
        )
    )
    session = cluster.connect()
    
    ### Create Keyspace
    session.execute(f"""
        CREATE KEYSPACE IF NOT EXISTS {env.CASSANDRA_KEYSPACE} 
        WITH REPLICATION = { 'class' : 'SimpleStrategy', 'replication_factor' : 1 };
    """)
    ### create table
    session.execute(f"""
    CREATE TABLE IF NOT EXISTS {env.CASSANDRA_KEYSPACE}.{env.CASSANDRA_TABLE} (
    user_id UUID,
    activity_id TIMEUUID,
    activity_type TEXT,
    timestamp TIMESTAMP,
    target_id UUID,
    target_type TEXT,
    metadata MAP<TEXT, TEXT>,
    PRIMARY KEY ((user_id), activity_id))
    WITH CLUSTERING ORDER BY (activity_id DESC);
    """)
    return session


def get_kafka_producer():
    return Producer({'bootstrap.servers': env.KAFKA_BOOTSTRAP_SERVERS})

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
    table_env.get_config().get_configuration().set_string(
        "pipeline.jars", 
        "file:///opt/flink/lib/flink-sql-connector-kafka_2.12-1.15.0.jar;"
        "file:///opt/flink/lib/flink-connector-cassandra_2.12-1.15.0.jar;"
        "file:///opt/flink/lib/flink-json-1.15.0.jar"
    )
    job_name = config.job_name

    if config.job_name == JobName.KAFKA_TO_CASSANDRA.value:
        table_env.execute_sql(f"""
            CREATE TABLE kafka_source (
                user_id STRING,
                activity_type STRING,
                timestamp BIGINT,
                target_id STRING,
                target_type STRING,
                metadata MAP<STRING, STRING>,
                proctime AS PROCTIME()
            ) WITH (
                'connector' = 'kafka',
                'topic' = '{env.KAFKA_TOPIC}',
                'properties.bootstrap.servers' = '{env.KAFKA_BOOTSTRAP_SERVERS}',
                'properties.group.id' = 'flink-group',
                'scan.startup.mode' = 'latest-offset',
                'format' = 'json'
            )
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
                'hosts' = '{','.join(env.CASSANDRA_CONTACT_POINTS)}',
                'port' = '{env.CASSANDRA_PORT}',
                'keyspace' = '{env.CASSANDRA_KEYSPACE}',
                'table' = '{env.CASSANDRA_TABLE}'
                {',' + f"'username' = '{env.CASSANDRA_USERNAME}'" if env.CASSANDRA_USERNAME else ""},
                {',' + f"'password' = '{env.CASSANDRA_PASSWORD}'" if env.CASSANDRA_PASSWORD else ""}
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
            host= env.POSTGRES_HOST,
            port= env.POSTGRES_PORT,
            user= env.POSTGRES_USER,
            password= env.POSTGRES_PASSWORD,
                dbname= env.POSTGRES_DB
            ) 
        return conn
    except Exception as e:
        print(f"Error connecting to postgres: {e}")
        raise HTTPException(status_code=500, detail="Failed to connect to postgres : {str(e)}")
    
def setup_debezium_connector():
    try: 
        with open(env.DEBEZIUM_CONNECTOR_CONFIG_FILE, "r") as f:
            config = json.load(f)
        response = requests.get(f"{env.DEBEZIUM_CONNECT_URL}/connectors/postgres-connector")
        if response.status_code == 200:
            return {"status": "success", "message": "Debezium connector already exists"}
        else:
            response = requests.post(f"{env.DEBEZIUM_CONNECT_URL}/connectors", json=config)
            if response.status_code == 200:
                return {"status": "success", "message": "Debezium connector created successfully"}
            else:
                return {"status": "error", "message": "Failed to create debezium connector"}
    except Exception as e:
        print(f"Error setting debezium connector: {e}")
        raise HTTPException(status_code=500, detail="Failed to set debezium connector : {str(e)}")
    
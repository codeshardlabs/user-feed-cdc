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
from flink_strategy import DataStreamStrategyFactory
from enums import ActivityType

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
        strategy_factory = DataStreamStrategyFactory()
        likes_strategy = strategy_factory.get_strategy(ActivityType.LIKE)
        shards_strategy = strategy_factory.get_strategy(ActivityType.SHARD)
        followers_strategy = strategy_factory.get_strategy(ActivityType.FOLLOW)
        comments_strategy = strategy_factory.get_strategy(ActivityType.COMMENT)
        
        table_env.execute_sql(likes_strategy.get_create_table_query())
        table_env.execute_sql(shards_strategy.get_create_table_query())
        table_env.execute_sql(followers_strategy.get_create_table_query())
        table_env.execute_sql(comments_strategy.get_create_table_query())

        table_env.execute_sql(likes_strategy.get_transform_data_query())
        table_env.execute_sql(shards_strategy.get_transform_data_query())
        table_env.execute_sql(followers_strategy.get_transform_data_query())
        table_env.execute_sql(comments_strategy.get_transform_data_query())
        
        
        # Create a table for each source table
        # for table in ['likes', 'shards', 'followers', 'comments']:
        #     table_env.execute_sql(f"""
        #          CREATE TABLE kafka_source_{table} (
        #             before MAP<STRING, STRING>,
        #             after MAP<STRING, STRING>,
        #             source MAP<STRING, STRING>,
        #             op STRING,
        #             ts_ms BIGINT,
        #             transaction MAP<STRING, STRING>,
        #             proctime AS PROCTIME()
        #         ) WITH (
        #             'connector' = 'kafka',
        #             'topic' = 'postgres.public.{table}',
        #             'properties.bootstrap.servers' = '{KAFKA_BOOTSTRAP_SERVERS}',
        #             'properties.group.id' = '1',
        #             'scan.startup.mode' = 'latest-offset',
        #             'format' = 'json'
        #         )
        #     """)

        # table_env.execute_sql("""
        #     CREATE VIEW transformed_likes AS
        #     SELECT
        #         after['liked_by'] AS user_id,
        #         'like' AS activity_type,
        #         ts_ms AS timestamp,
        #         after['shard_id'] AS target_id,
        #         'shard' AS target_type,
        #         CAST(NULL AS MAP<STRING, STRING>) AS metadata,
        #         'likes' AS source_table
        #     FROM kafka_source_likes
        #     WHERE op IN ('c', 'r') AND after IS NOT NULL
        # """)

        # table_env.execute_sql("""
        #     CREATE VIEW transformed_shards AS
        #     SELECT
        #         after['user_id'] AS user_id,
        #         'create_shard' AS activity_type,
        #         ts_ms AS timestamp,
        #         after['id'] AS target_id,
        #         'shard' AS target_type,
        #         MAP['title', after['title'], 'mode', after['mode'], 'type', after['type']] AS metadata,
        #         'shards' AS source_table
        #     FROM kafka_source_shards
        #     WHERE op IN ('c', 'r') AND after IS NOT NULL
        # """)

        # table_env.execute_sql("""
        #     CREATE VIEW transformed_followers AS
        #     SELECT
        #         after['follower_id'] AS user_id,
        #         'follow' AS activity_type,
        #         ts_ms AS timestamp,
        #         after['following_id'] AS target_id,
        #         'user' AS target_type,
        #         CAST(NULL AS MAP<STRING, STRING>) AS metadata,
        #         'followers' AS source_table
        #     FROM kafka_source_followers
        #     WHERE op IN ('c', 'r') AND after IS NOT NULL
        # """)

        # table_env.execute_sql("""
        #     CREATE VIEW transformed_comments AS
        #     SELECT
        #         after['user_id'] AS user_id,
        #         'comment' AS activity_type,
        #         ts_ms AS timestamp,
        #         after['shard_id'] AS target_id,
        #         'shard' AS target_type,
        #         MAP['message', after['message']] AS metadata,
        #         'comments' AS source_table
        #     FROM kafka_source_comments
        #     WHERE op IN ('c', 'r') AND after IS NOT NULL
        # """)


        table_env.execute_sql("""
            CREATE VIEW kafka_source AS
            SELECT * FROM transformed_likes
            UNION ALL
            SELECT * FROM transformed_shards
            UNION ALL
            SELECT * FROM transformed_followers
            UNION ALL
            SELECT * FROM transformed_comments
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


async def delete_debezium_connector():
    try:
        response = requests.delete(f"{DEBEZIUM_CONNECT_URL}/connectors/postgres-connector")
        if response.status_code == 200:
            print("Debezium connector deleted successfully")
            return {"status": "success", "message": "Debezium connector deleted successfully"}
        else:
            raise Exception(f"Failed to delete connector. Status: {response.status_code}, Response: {response.text}")
    except Exception as e:
        print(f"Error deleting Debezium connector: {e}")
        raise Exception(f"Failed to delete Debezium connector: {str(e)}")

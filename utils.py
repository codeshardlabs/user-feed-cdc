from pyflink.datastream import StreamExecutionEnvironment, CheckpointingMode
from pyflink.table import EnvironmentSettings, StreamTableEnvironment
from pyflink.common.typeinfo import Types
from pyflink.datastream.connectors.cassandra import CassandraSink
from env import CASSANDRA_CONTACT_POINTS, CASSANDRA_PORT, CASSANDRA_USERNAME, CASSANDRA_PASSWORD, KAFKA_BOOTSTRAP_SERVERS, POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, DEBEZIUM_CONNECT_URL, DEBEZIUM_CONNECTOR_CONFIG_FILE, FLINK_CONNECTOR_KAFKA_JAR, FLINK_CONNECTOR_CASSANDRA_JAR, FLINK_JSON_JAR, KAFKA_CLIENT_JAR
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
from flink_strategy import DataStreamAdaptorStrategyFactory
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
    JAR_FILE_PREFIX = "file:///flink-connectors"
    jar_paths = [
        f"{JAR_FILE_PREFIX}/{FLINK_CONNECTOR_KAFKA_JAR}",
        f"{JAR_FILE_PREFIX}/{FLINK_CONNECTOR_CASSANDRA_JAR}",
        f"{JAR_FILE_PREFIX}/{FLINK_JSON_JAR}",
        f"{JAR_FILE_PREFIX}/{KAFKA_CLIENT_JAR}"
    ]
    logger.info(f"JAR paths: {jar_paths}")      

    # Then join them with semicolons
    jar_paths_str = ";".join(jar_paths)
    logger.info(f"Final pipeline.jars value: {jar_paths_str}")
    table_env.get_config().get_configuration().set_string(
        "pipeline.jars", 
        jar_paths_str
    )
    job_name = config.job_name

    if config.job_name == JobName.KAFKA_TO_CASSANDRA.value:
        strategy_factory = DataStreamAdaptorStrategyFactory()
        for activity_type in ActivityType:

            strategy = strategy_factory.get_strategy(activity_type)
            table_env.execute_sql(strategy.get_create_table_query())
            table_env.execute_sql(strategy.get_transform_data_query())
            logger.info(f"Created table for {activity_type}")

        logger.info("Creating kafka source")

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

        result_table = table_env.sql_query("""
            SELECT 
                user_id,
                CAST(UUID() AS STRING) AS activity_id,
                activity_type,
                TO_TIMESTAMP(FROM_UNIXTIME(event_timestamp / 1000)) AS event_timestamp,
                target_id,
                target_type,
                metadata
            FROM kafka_source
        """)

        data_stream = table_env.to_append_stream(
            result_table, 
            Types.ROW([
                Types.STRING(), Types.STRING(), Types.STRING(), 
                Types.SQL_TIMESTAMP(), Types.STRING(), Types.STRING(),
                Types.MAP(Types.STRING(), Types.STRING())
            ])
        )
        
        CassandraSink.add_sink(data_stream) \
            .set_host("cassandra", 9042) \
            .set_query("INSERT INTO codeshard.user_activity (user_id, activity_id, activity_type, event_timestamp, target_id, target_type, metadata) VALUES (?, ?, ?, ?, ?, ?, ?)") \
            .build()
        env.execute("Kafka to Cassandra Job")
        logger.info("Created cassandra sink view")
        

      
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

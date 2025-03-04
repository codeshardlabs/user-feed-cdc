from fastapi import FastAPI
from typing import Union
from cassandra.cluster import Cluster 
import os
from confluent_kafka import Producer
from pydantic import BaseModel
from pyflink.datastream import StreamExecutionEnvironment, CheckpointingMode
from pyflink.table import EnvironmentSettings, StreamTableEnvironment  

cluster = Cluster()

app = FastAPI(title="user-feed")

class FlinkJobConfig(BaseModel):
    job_name: str
    parallelism: int = 1
    checkpoint_interval: int = 10000 ## in milliseconds

CASSANDRA_CONTACT_POINTS = os.environ.get("CASSANDRA_CONTACT_POINTS", "localhost").split(",")
CASSANDRA_PORT = int(os.environ.get("CASSANDRA_PORT", "9042"))
CASSANDRA_KEYSPACE = os.environ.get("CASSANDRA_KEYSPACE", "mykeyspace")
CASSANDRA_TABLE = os.environ.get("CASSANDRA_TABLE", "mytable")
CASSANDRA_USERNAME = os.environ.get("CASSANDRA_USERNAME", "")
CASSANDRA_PASSWORD = os.environ.get("CASSANDRA_PASSWORD", "")
KAFKA_BOOTSTRAP_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS")
KAFKA_TOPIC = os.environ.get("KAFKA_TOPIC")

## Connect to cassandra
def get_cassandra_session():
    cluster = Cluster()
    session = cluster.connect()
    
    ### Create Keyspace
    session.execute(f"""
        CREATE KEYSPACE IF NOT EXISTS {CASSANDRA_KEYSPACE} 
        WITH REPLICATION = { 'class' : 'SimpleStrategy', 'replication_factor' : 1 };
    """)
    ### create table
    session.execute(f"""
    CREATE TABLE IF NOT EXISTS {CASSANDRA_KEYSPACE}.{CASSANDRA_TABLE} (
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
    table_env.get_config().get_configuration().set_string(
        "file:///opt/flink/lib/flink-connector-cassandra_2.12-1.15.0.jar;"
        "file:///opt/flink/lib/flink-json-1.15.0.jar"
    )
    job_name = config.job_name

    if config.job_name == "kafka-cassandra-sink":
        table_env.execute_sql(f"""
            CREATE TABLE kafka_source (
                id STRING,
                value DOUBLE,
                timestamp BIGINT,
                proctime AS PROCTIME()
            ) WITH (
                'connector' = 'kafka',
                'topic' = '{KAFKA_TOPIC}',
                'properties.bootstrap.servers' = '{KAFKA_BOOTSTRAP_SERVERS}',
                'properties.group.id' = 'flink-group',
                'scan.startup.mode' = 'latest-offset',
                'format' = 'json'
            )
        """)

        table_env.execute_sql(f"""
            CREATE TABLE cassandra_sink (
                id STRING,
                value DOUBLE,
                timestamp BIGINT,
                PRIMARY KEY (id) NOT ENFORCED
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
            SELECT id, value, timestamp
            FROM kafka_source
        """).wait()

        
    else:
        raise ValueError(f"Invalid job name: {job_name}")

@app.get("/")
def read_root():
    return {"Hello" : "World"};

@app.get("/items/{item_id}")
def read_items(item_id: int, q: Union[str,None] = None):
    return {"item_id": item_id,"q": q }



from env import  POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, DEBEZIUM_CONNECT_URL, DEBEZIUM_CONNECTOR_CONFIG_FILE
import psycopg2
import json
import requests
from fastapi import HTTPException
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from config import CassandraConfig
## Connect to cassandra
def get_cassandra_session(cassandra_config: CassandraConfig):
    cluster = Cluster(
        cassandra_config.contact_points, 
        port=cassandra_config.port,
        auth_provider=PlainTextAuthProvider(
            username=cassandra_config.username,
            password=cassandra_config.password
        )
    )
    session = cluster.connect()
    return session


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
    

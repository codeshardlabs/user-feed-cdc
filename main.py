from fastapi import FastAPI
from typing import Union
from cassandra.cluster import Cluster 
import os

cluster = Cluster()

app = FastAPI(title="user-feed")

CASSANDRA_KEYSPACE = os.environ.get("CASSANDRA_KEYSPACE")
CASSANDRA_TABLE = os.environ.get("CASSANDRA_TABLE")


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


    

@app.get("/")
def read_root():
    return {"Hello" : "World"};

@app.get("/items/{item_id}")
def read_items(item_id: int, q: Union[str,None] = None):
    return {"item_id": item_id,"q": q }



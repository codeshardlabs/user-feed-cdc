from fastapi import FastAPI, HTTPException, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from typing import Union, Optional, Dict
import os
from confluent_kafka import Producer
from pydantic import BaseModel
from env import  DEBEZIUM_CONNECT_URL, CASSANDRA_KEYSPACE, CASSANDRA_TABLE, KAFKA_BOOTSTRAP_SERVERS, KAFKA_GROUP_ID, KAFKA_AUTO_OFFSET_RESET, KAFKA_ENABLE_AUTO_COMMIT, CASSANDRA_CONTACT_POINTS, CASSANDRA_PORT, CASSANDRA_USERNAME, CASSANDRA_PASSWORD, POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, DEBEZIUM_CONNECTOR_CONFIG_FILE
import json
import requests
from services.debezium import setup_debezium_connector, delete_debezium_connector
from services.cassandra import get_cassandra_session
from services.postgres import get_postgres_connection
from config import  FollowUserRequestBody, AppConfig, KafkaConfig, CassandraConfig, DebeziumConfig, PostgresConfig
from cache import cache
from event_processor import EventProcessor
from connection_state import connection_state, ConnectionState
import asyncio
from enums import TableType

@asynccontextmanager
async def lifespan(app: FastAPI):
    tables = [table.value for table in TableType]
    app_config = AppConfig(
        kafka=KafkaConfig(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            group_id=KAFKA_GROUP_ID,
            auto_offset_reset=KAFKA_AUTO_OFFSET_RESET,
            enable_auto_commit=KAFKA_ENABLE_AUTO_COMMIT,
            topics=[f"postgres.public.{table}" for table in tables]
        ),
        cassandra=CassandraConfig(
            contact_points=[CASSANDRA_CONTACT_POINTS],
            port=CASSANDRA_PORT,
            username=CASSANDRA_USERNAME,
            password=CASSANDRA_PASSWORD,
        ),
        debezium=DebeziumConfig(
            url=DEBEZIUM_CONNECT_URL,
            connector_config_file=DEBEZIUM_CONNECTOR_CONFIG_FILE,
        ),
        postgres=PostgresConfig(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            username=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            dbname=POSTGRES_DB,
        )
    )

    processor = EventProcessor(app_config)
    kafka_connected = await processor.connect_kafka()
    cassandra_connected = await processor.connect_cassandra()

    app.state.config = app_config
    app.state.processor = processor
    if kafka_connected and cassandra_connected:
        print("Connected to Kafka and Cassandra")
        asyncio.create_task(processor.process_events())
    yield
    if hasattr(app.state, 'processor'):
        app.state.processor.stop()
    await processor.close()

app = FastAPI(title="user-feed", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"Hello" : "World"};


@app.get("/status", response_model=ConnectionState)
async def get_status():
    """Get the current status of the CDC processor."""
    return connection_state

@app.post("/start", status_code=status.HTTP_202_ACCEPTED)
async def start_processing(background_tasks: BackgroundTasks):
    """Start CDC processing if it's not already running."""
    if connection_state.processing_active:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "Processing is already active"}
        )
    
    processor = app.state.processor
    
    # Reconnect if needed
    if not connection_state.kafka_connected:
        await processor.connect_kafka()
    
    if not connection_state.cassandra_connected:
        await processor.connect_cassandra()
    
    if connection_state.kafka_connected and connection_state.cassandra_connected:
        background_tasks.add_task(processor.process_events)
        return {"message": "Processing started"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to connect to Kafka or Cassandra"
        )

@app.post("/stop", status_code=status.HTTP_202_ACCEPTED)
async def stop_processing():
    """Stop CDC processing."""
    if not connection_state.processing_active:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "Processing is not active"}
        )
    
    app.state.processor.stop()
    return {"message": "Processing stopped"}

@app.get("/config", response_model=AppConfig)
async def get_config():
    """Get the current configuration."""
    return app.state.config

@app.post("/reset_counter", status_code=status.HTTP_200_OK)
async def reset_counter():
    """Reset the processed events counter."""
    connection_state.processed_events = 0
    connection_state.last_processed = None
    return {"message": "Counter reset"}


@app.get("/cassandra/activities", tags=["cassandra"])
def get_cassandra_activities(user_id: str, limit: int = 100, offset: int = 0):
    """
     Generate user feed for a specific user by returning activities from cassandra of the user that the user follows
    """
    try: 
        ## Check cache first 
        cache_key = f"user_feed:{user_id}:{limit}:{offset}"
        cached_activities = cache.get(cache_key)
        if cached_activities:
            return {"data": cached_activities, "count": len(cached_activities)}
        
        # get user followers from postgres
        conn = get_postgres_connection()
        cur = conn.cursor()
        cur.execute(f"SELECT following_id FROM followers WHERE follower_id = '{user_id}'")
        followers = [follower.following_id for follower in cur]
        cur.close()
        conn.close()

        # get activities from cassandra
        cassandra_session = get_cassandra_session()
        
        # Convert all follower IDs to UUIDs
        try:
            # Convert list of follower IDs to list of UUIDs
            follower_uuids = []
            for follower_id in followers:
                uuid_result = cassandra_session.execute(f"SELECT UUID('{follower_id}') AS uuid")[0]
                follower_uuids.append(uuid_result.uuid)
        except Exception as e:
            cassandra_session.shutdown()
            raise HTTPException(status_code=404, detail=f"Invalid UUID format in follower IDs: {str(e)}")
        
        ## query with prepared statement for security
        prepared_stmt = cassandra_session.prepare(
            f"""
                SELECT * FROM {CASSANDRA_KEYSPACE}.{CASSANDRA_TABLE}
                WHERE user_id in ?
                LIMIT ?
                OFFSET ?
            """)
        
        result = cassandra_session.execute(prepared_stmt, (follower_uuids, limit, offset))
        results = []
        for row in result:
                # Handle potential None values and proper UUID conversion
            temp = {
                "user_id": str(row.user_id) if row.user_id else None,
                "activity_id": str(row.activity_id) if row.activity_id else None,
                "activity_type": row.activity_type,
                "timestamp": row.timestamp.isoformat() if row.timestamp else None,
                "target_id": str(row.target_id) if row.target_id else None,
                "target_type": row.target_type if row.target_type else None,
                "metadata": dict(row.metadata) if row.metadata else {}
            }
            results.append(temp)
        
        cassandra_session.shutdown()
        ## cache the results
        cache.set(cache_key, results)
        cache.shutdown()
        return {"data": results, "count": len(results)}
    except Exception as e:
        print(f"Error getting cassandra activities: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get cassandra activities: {str(e)}")
    
#### Debezium setup
@app.get("/debezium/setup", tags=["debezium"])
async def setup_debezium():
    """
    Set up the Debezium connector for PostgreSQL CDC.
    
    This creates a Debezium connector that monitors the PostgreSQL database
    for changes and publishes them to Kafka topics.
    """
    max_retries = 5
    retry_delay = 5  # seconds
    
    for attempt in range(max_retries):
        try:
            result = await setup_debezium_connector(app.state.config.debezium, app.state.config.postgres)
            return {"data": result, "status": "success", "message": "Debezium connector setup completed"}
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Attempt {attempt + 1} failed. Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                continue
            print(f"Error setting up debezium connector after {max_retries} attempts: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to setup debezium connector after {max_retries} attempts: {str(e)}"
            )

@app.delete("/debezium/setup", tags=["debezium"])
async def delete_debezium():
    """
    Delete the Debezium connector.
    """
    try:
        await delete_debezium_connector()
        return {"status": "success", "message": "Debezium connector deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete debezium connector: {str(e)}")
    
@app.get("/debezium/status", tags=["debezium"])
async def get_connector_status():
    """
    Get the status of the Debezium connector.
    
    Returns information about the connector's configuration and tasks.
    """
    try:
        response = requests.get(f"{DEBEZIUM_CONNECT_URL}/connectors/postgres-connector/status")
        if response.status_code != 200:
            return {
                "status": "not_found",
                "message": "Connector not found or not yet configured"
            }
        return response.json()
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to get connector status: {str(e)}"
        )
    
### Follow User Activity in postgres table 
@app.post("/follow/user", tags=["activity"])
async def follow_user(body: FollowUserRequestBody):
    """
    Follow a user.
    """
    try: 
        print("postgres config", app.state.config.postgres)
        conn = get_postgres_connection(app.state.config.postgres)
        cur = conn.cursor()
        cur.execute(f"INSERT INTO followers (follower_id, following_id) VALUES ('{body.user_id}', '{body.other_user_id}')")
        conn.commit()
        return {"status": "success", "message": "User followed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to follow user: {str(e)}")
    finally:
        cur.close()
        conn.close()
    
### Create New Post Activity in postgres table 
@app.post("/create/post", tags=["activity"])
async def create_post(user_id: str, title: str):
    """
    Create a new post.
    """
    try: 
        session = get_postgres_connection(app.state.config.postgres)
        title = title if title else "Untitled"
        session.execute(f"INSERT INTO shards (user_id, title, mode, type) VALUES ('{user_id}', '{title}', 'normal', 'public')")
        return {"status": "success", "message": "Post created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create post: {str(e)}")

### Comment on Post Activity in postgres table 
@app.post("/comment/post", tags=["activity"])
async def comment_on_post(user_id: str, shard_id: str, message: str):
    """
    Comment on a post.
    """
    try: 
        session = get_postgres_connection(app.state.config.postgres)
        session.execute(f"INSERT INTO comments (user_id, shard_id, comment) VALUES ('{user_id}', '{shard_id}', '{message}')")
        return {"status": "success", "message": "Comment created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to comment on post: {str(e)}")
    
### Like Post Activity in postgres table 
@app.post("/like/post", tags=["activity"])
async def like_post(user_id: str, shard_id: str):
    """
    Like a post.
    """
    try: 
        session = get_postgres_connection(app.state.config.postgres)
        session.execute(f"INSERT INTO likes (user_id, shard_id) VALUES ('{user_id}', '{shard_id}')")
        return {"status": "success", "message": "Post liked successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to like post: {str(e)}")

# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    Returns a simple response to indicate the API is running.
    """
    return {"status": "healthy", "message": "API is running"}

# Documentation customization
app.swagger_ui_parameters = {
    "deepLinking": True,
    "persistAuthorization": True,
    "displayRequestDuration": True,
    "filter": True,
    "syntaxHighlight.theme": "monokai"
}
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
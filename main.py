from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import Union, Optional, Dict
import os
from confluent_kafka import Producer
from pydantic import BaseModel
from env import  KAFKA_TOPIC, DEBEZIUM_CONNECT_URL, FLINK_REST_API_URL, CASSANDRA_KEYSPACE, CASSANDRA_TABLE
from enums import JobName
import json
import requests
from utils import get_kafka_producer, run_flink_job, setup_debezium_connector, get_cassandra_session, get_postgres_connection
from config import FlinkJobConfig


app = FastAPI(title="user-feed")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DataRecord(BaseModel):
    user_id: str
    activity_type: str
    timestamp: int
    target_id: Optional[str] = None
    target_type: Optional[str] = None
    metadata: Dict[str, str]
    source_table: Optional[str] = None




@app.get("/")
def read_root():
    return {"Hello" : "World"};

@app.post("/activity", tags=["activity"])
async def send_activity(data: DataRecord):
    """
    send user activity to kafka topic
    This endpoint accepts the user activity data and sends it to the configured kafka topic
    The data will be consumed by flink job and written to cassandra
    """
    try: 
        data_dict = data.model_dump()
        producer = get_kafka_producer()
        
        # Determine the topic based on source_table
        topic = f"postgres.codeshard.{data.source_table}" if data.source_table else KAFKA_TOPIC
        
        producer.produce(
            topic,
            key=data.user_id,
            value=json.dumps(data_dict)
        )
        producer.flush()
        return {"status": "success", "message": f"Activity sent to Kafka topic {topic}"}
    except Exception as e:
        print(f"Error sending activity to Kafka: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send activity to Kafka: {str(e)}")
    

@app.post("/job/start", tags=["flink"])
def start_job(config: FlinkJobConfig, background_tasks: BackgroundTasks):
    """
    Start a flink job with the given configuration
    The job will be started in the background and the response will return immediately
    The job status can be checked using the /job/status endpoint
    """
    try: 
        valid_job_names = [job.value for job in JobName]
        if config.job_name not in valid_job_names:
            raise HTTPException(status_code=400, detail=f"Invalid job name: {config.job_name}")
        
        background_tasks.add_task(run_flink_job, config)
        return {"status": "success", "message": f"Job {config.job_name} started"}
    except Exception as e:
        print(f"Error starting job: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start job: {str(e)}")
    
@app.get("/flink/jobs", tags=["flink"])
def get_flink_jobs():
    """
    Get the status of all flink jobs
    This endpoint queries the Flink JobManager API to get information about all running jobs.
    It returns a list of jobs with their status, name, and other details.
    """
    try: 
        response = requests.get(f"{FLINK_REST_API_URL}/jobs/overview")
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Failed to get flink jobs: {response.text}")
        return response.json()
    except Exception as e:
        print(f"Error getting flink jobs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get flink jobs: {str(e)}")

@app.get("/cassandra/activities", tags=["cassandra"])
def get_cassandra_activities(user_id: str, limit: int = 100, offset: int = 0):
    """
     Generate user feed for a specific user by returning activities from cassandra of the user that the user follows
    """
    try: 
        # get user followers from postgres
        session = get_postgres_connection()
        followers = session.execute(f"SELECT following_id FROM followers WHERE follower_id = '{user_id}'")
        followers = [follower.following_id for follower in followers]

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
        return {"data": results, "count": len(results)}
    except Exception as e:
        print(f"Error getting cassandra activities: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get cassandra activities: {str(e)}")
    
#### Debezium setup
@app.post("/debezium/setup", tags=["debezium"])
async def setup_debezium():
    """
    Set up the Debezium connector for PostgreSQL CDC.
    
    This creates a Debezium connector that monitors the PostgreSQL database
    for changes and publishes them to Kafka topics.
    """
    try:
        result = await setup_debezium_connector()
        return {"data" : result, "status": "success", "message": "Debezium connector setup completed"}
    except Exception as e:
        print(f"Error setting up debezium connector: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to setup debezium connector: {str(e)}")

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
async def follow_user(user_id: str, other_user_id: str):
    """
    Follow a user.
    """
    try: 
        session = get_postgres_connection()
        session.execute(f"INSERT INTO followers (follower_id, following_id) VALUES ('{user_id}', '{other_user_id}')")
        return {"status": "success", "message": "User followed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to follow user: {str(e)}")
    
### Create New Post Activity in postgres table 
@app.post("/create/post", tags=["activity"])
async def create_post(user_id: str, title: str):
    """
    Create a new post.
    """
    try: 
        session = get_postgres_connection()
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
        session = get_postgres_connection()
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
        session = get_postgres_connection()
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
from fastapi import FastAPI, HTTPException, BackgroundTasks
from typing import Union, Optional, Dict
import os
from confluent_kafka import Producer
from pydantic import BaseModel
from env import  KAFKA_TOPIC, DEBEZIUM_CONNECT_URL, FLINK_REST_API_URL, CASSANDRA_KEYSPACE, CASSANDRA_TABLE
from enums import JobName
import json
import requests
from utils import get_kafka_producer, run_flink_job, setup_debezium_connector, get_cassandra_session
from config import FlinkJobConfig
import uuid


app = FastAPI(title="user-feed")

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
def get_cassandra_activities(user_id: str, limit: int = 100):
    """
     Retrieve user activities from Cassandra for a specific user.
    """
    try: 
        session = get_cassandra_session()
        try: 
            user_uuid = session.execute(f"SELECT UUID('{user_id}') AS uuid")[0].uuid
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Invalid UUID format: {str(e)}")
        
        ## query with prepared statement for security
        prepared_stmt = session.prepare(
            f"""
                SELECT * FROM {CASSANDRA_KEYSPACE}.{CASSANDRA_TABLE}
                WHERE user_id = ?
                LIMIT ?
            """)
        
        result = session.execute(prepared_stmt, (user_uuid, limit))
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

@app.get("/debezium/status", tags=["Debezium"])
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
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
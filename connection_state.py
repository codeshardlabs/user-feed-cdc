from pydantic import BaseModel
from datetime import datetime
from typing import Optional
class ConnectionState(BaseModel):
    kafka_connected: bool = False
    cassandra_connected: bool = False
    processing_active: bool = False
    processed_events: int = 0
    last_processed_event: Optional[datetime] = None


connection_state = ConnectionState()
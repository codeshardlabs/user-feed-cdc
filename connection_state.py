from config import AppConfig
from datetime import datetime
class ConnectionState:
    def __init__(self):
        self.kafka_connected = False
        self.cassandra_connected = False
        self.processing_active = False
        self.processed_events = 0
        self.last_processed_event = None


connection_state = ConnectionState()
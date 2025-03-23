from confluent_kafka import Consumer, KafkaException
from config import AppConfig
from confluent_kafka.error import  KafkaException
from connection_state import connection_state
from logger import logger
import asyncio
from enums import TableType
from strategy import SchemaAdapterStrategyFactory
import json
from cassandra.query import BatchStatement
from datetime import datetime
from services.cassandra import get_cassandra_session
from services.kafka import get_kafka_consumer
class EventProcessor:
    def __init__(self, config: AppConfig):
        self.config = config

    async def connect_kafka(self):
        try:
            self.consumer = get_kafka_consumer(self.config.kafka)
            connection_state.kafka_connected = True
            return True
        except KafkaException as e:
            connection_state.kafka_connected = False
            print(f"Error connecting to Kafka: {e}")
            return False
        
    async def connect_cassandra(self):
        try:
            self.cassandra_session = get_cassandra_session(self.config.cassandra)
            connection_state.cassandra_connected = True
            return True
        except Exception as e:
            connection_state.cassandra_connected = False
            print(f"Error connecting to Cassandra: {e}")
            return False
        
    async def process_events(self):
        if not connection_state.kafka_connected or not connection_state.cassandra_connected:
            logger.error("Kafka or Cassandra not connected")
            return
        
        self.running = True
        connection_state.processing_active = True
        batch_size = 1
        batch_events = []
        while self.running:
            if not self.consumer:
                self.consumer = get_kafka_consumer(self.config.kafka)
            message = self.consumer.poll(1.0)
            if message is None:
                await asyncio.sleep(0.1)
                continue
            if message.error():
                logger.error(f"Kafka error: {message.error()}")
                continue
            topic_name = message.topic()
            table_name = topic_name.split(".")[-1]
            try:
                print(f"Received message: {message.value().decode('utf-8')}")
                strategy = SchemaAdapterStrategyFactory.get_strategy(TableType(table_name))
                # data = strategy.transform(json.loads(message.value().decode('utf-8')))
                # batch_events.append(data)
                # if len(batch_events) >= batch_size:
                #     await self.process_batch(batch_events)
                #     batch_events = []
                connection_state.processed_events += 1
                connection_state.last_processed_event = datetime.now()
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                connection_state.running = False
                continue
            finally:
                connection_state.processing_active = False

    async def close(self):
        self.running = False
        if self.consumer:
            self.consumer.close()
        if self.cassandra_session:
            self.cassandra_session.shutdown()
        connection_state.processing_active = False
    
    async def process_batch(self, batch_events: list):
        print(f"Insert batch of {len(batch_events)} events to cassandra")
        batch = BatchStatement()
        if not self.cassandra_session:
            self.cassandra_session = get_cassandra_session(self.config.cassandra)
        insert_query = self.cassandra_session.prepare("""
            INSERT INTO codeshard.user_activity 
            (user_id, activity_id, activity_type, event_timestamp, target_id, target_type, metadata) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """)
        for event in batch_events:
            batch.add(insert_query, (
                event['user_id'],
                event['activity_id'],
                event['activity_type'],
                event['event_timestamp'],
                event['target_id'],
                event['target_type'],
                event['metadata']
            ))
        
        self.cassandra_session.execute(batch)
        
            
    
    

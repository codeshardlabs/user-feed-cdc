from kafka import KafkaConsumer
from fastapi import HTTPException
from config import KafkaConfig
import logging

logger = logging.getLogger(__name__)

def get_kafka_consumer(kafka_config: KafkaConfig):
    try:
        logger.info(f"Connecting to Kafka with config: {kafka_config}")
        consumer = KafkaConsumer(
            bootstrap_servers=[kafka_config.bootstrap_servers],
            group_id=kafka_config.group_id,
            auto_offset_reset=kafka_config.auto_offset_reset,
            enable_auto_commit=kafka_config.enable_auto_commit
        )
        
        if not kafka_config.topics:
            raise ValueError("No topics configured for Kafka consumer")
            
        consumer.subscribe(kafka_config.topics)
        logger.info(f"Successfully connected to Kafka and subscribed to topics: {kafka_config.topics}")
        return consumer
    except Exception as e:
        logger.error(f"Error connecting to Kafka: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to connect to Kafka: {str(e)}")
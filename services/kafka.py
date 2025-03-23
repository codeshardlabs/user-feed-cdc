from confluent_kafka import Consumer
from fastapi import HTTPException
from config import KafkaConfig

def get_kafka_consumer(kafka_config: KafkaConfig):
    try:
        consumer = Consumer({
            'bootstrap.servers': kafka_config.bootstrap_servers,
            'group.id': kafka_config.group_id,
            'auto.offset.reset': kafka_config.auto_offset_reset,
            'enable.auto.commit': kafka_config.enable_auto_commit
        })           
        consumer.subscribe(kafka_config.topics)
        return consumer
    except Exception as e:
        print(f"Error connecting to Kafka: {e}")
        raise HTTPException(status_code=500, detail="Failed to connect to Kafka: {str(e)}")
from kafka import KafkaConsumer
from fastapi import HTTPException
from config import KafkaConfig

def get_kafka_consumer(kafka_config: KafkaConfig):
    try:
        print("kafka config", kafka_config)
        consumer = KafkaConsumer(
            'postgres.public.followers',
            bootstrap_servers=[kafka_config.bootstrap_servers],
            group_id=kafka_config.group_id,
            auto_offset_reset=kafka_config.auto_offset_reset,
            enable_auto_commit=kafka_config.enable_auto_commit
        )  
        consumer.subscribe(kafka_config.topics)         
        print("consumer", consumer)
        return consumer
    except Exception as e:
        print(f"Error connecting to Kafka: {e}")
        raise HTTPException(status_code=500, detail="Failed to connect to Kafka: {str(e)}")
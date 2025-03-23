from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime

class FlinkJobConfig(BaseModel):
    job_name: str
    parallelism: int = 1
    checkpoint_interval: int = 10000 ## in milliseconds


class FollowUserRequestBody(BaseModel):
    user_id: str
    other_user_id: str

class CreatePostRequestBody(BaseModel):
    user_id: str
    title: str

class DataRecord(BaseModel):
    user_id: str
    activity_type: str
    timestamp: int
    target_id: Optional[str] = None
    target_type: Optional[str] = None
    metadata: Dict[str, str]
    source_table: Optional[str] = None


class KafkaConfig(BaseModel):
    bootstrap_servers: str = Field(..., description="Kafka bootstrap servers")
    group_id: str = Field(..., description="Consumer group ID")
    topics: List[str] = Field(..., description="Topics to consume from")
    auto_offset_reset: str = Field("earliest", description="Auto offset reset")
    enable_auto_commit: bool = Field(True, description="Enable auto commit")

class CassandraConfig(BaseModel):
    contact_points: List[str] = Field(..., description="Cassandra contact points")
    port: int = Field(..., description="Cassandra port")
    username: str = Field(..., description="Cassandra username")
    password: str = Field(..., description="Cassandra password")

class PostgresConfig(BaseModel):
    host: str = Field(..., description="Postgres host")
    port: int = Field(..., description="Postgres port")
    username: str = Field(..., description="Postgres username")
    password: str = Field(..., description="Postgres password")
    dbname: str = Field(..., description="Postgres database name")


class DebeziumConfig(BaseModel):
    url: str = Field(..., description="Debezium URL")
    connector_config_file: str = Field(..., description="Debezium connector config file")


class AppConfig(BaseModel):
    kafka: KafkaConfig = Field(..., description="Kafka configuration")
    cassandra: CassandraConfig = Field(..., description="Cassandra configuration")
    debezium: DebeziumConfig = Field(..., description="Debezium configuration")
    postgres: PostgresConfig = Field(..., description="Postgres configuration")



import os

### Cassandra
CASSANDRA_CONTACT_POINTS = os.environ.get("CASSANDRA_CONTACT_POINTS", "localhost").split(",")
CASSANDRA_PORT = int(os.environ.get("CASSANDRA_PORT", "9042"))
CASSANDRA_KEYSPACE = os.environ.get("CASSANDRA_KEYSPACE", "codeshard")
CASSANDRA_TABLE = os.environ.get("CASSANDRA_TABLE", "user_activity")
CASSANDRA_USERNAME = os.environ.get("CASSANDRA_USERNAME", "cassandra")
CASSANDRA_PASSWORD = os.environ.get("CASSANDRA_PASSWORD", "cassandra")

### Kafka
KAFKA_BOOTSTRAP_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

### Postgres
POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.environ.get("POSTGRES_PORT", "5432"))
POSTGRES_USER = os.environ.get("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "postgres")
POSTGRES_DB = os.environ.get("POSTGRES_DB", "codeshard")

### Debezium Connector
DEBEZIUM_CONNECT_URL = os.environ.get("DEBEZIUM_CONNECT_URL", "http://debezium-connect:8083")
DEBEZIUM_CONNECTOR_CONFIG_FILE = os.environ.get("DEBEZIUM_CONNECTOR_CONFIG_FILE", "debezium-postgres-connector.config.json")

### Flink
FLINK_REST_API_URL = os.environ.get("FLINK_REST_API_URL", "http://jobmanager:8081")
FLINK_CONNECTOR_CASSANDRA_JAR = os.environ.get("FLINK_CONNECTOR_CASSANDRA_JAR", "flink-connector-cassandra_2.12-3.2.0-1.19.jar")
FLINK_CONNECTOR_KAFKA_JAR = os.environ.get("FLINK_CONNECTOR_KAFKA_JAR", "flink-connector-kafka-3.4.0-1.20.jar")
FLINK_JSON_JAR = os.environ.get("FLINK_JSON_JAR", "flink-json-1.20.1.jar")

### Redis
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
REDIS_DB = int(os.environ.get("REDIS_DB", "0"))
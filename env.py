import os

### Cassandra
CASSANDRA_CONTACT_POINTS = os.environ.get("CASSANDRA_CONTACT_POINTS", "cassandra")
CASSANDRA_PORT = int(os.environ.get("CASSANDRA_PORT", "9042"))
CASSANDRA_KEYSPACE = os.environ.get("CASSANDRA_KEYSPACE", "codeshard")
CASSANDRA_TABLE = os.environ.get("CASSANDRA_TABLE", "user_activity")
CASSANDRA_USERNAME = os.environ.get("CASSANDRA_USERNAME", "cassandra")
CASSANDRA_PASSWORD = os.environ.get("CASSANDRA_PASSWORD", "cassandra")

### Kafka
KAFKA_BOOTSTRAP_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_GROUP_ID = os.environ.get("KAFKA_GROUP_ID", "user-feed")
KAFKA_AUTO_OFFSET_RESET = os.environ.get("KAFKA_AUTO_OFFSET_RESET", "earliest")
KAFKA_ENABLE_AUTO_COMMIT = os.environ.get("KAFKA_ENABLE_AUTO_COMMIT", "true")

### Postgres
POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.environ.get("POSTGRES_PORT", "5432"))
POSTGRES_USER = os.environ.get("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "postgres")
POSTGRES_DB = os.environ.get("POSTGRES_DB", "codeshard")

### Debezium Connector
DEBEZIUM_CONNECT_URL = os.environ.get("DEBEZIUM_CONNECT_URL", "http://debezium-connect:8083")
DEBEZIUM_CONNECTOR_CONFIG_FILE = os.environ.get("DEBEZIUM_CONNECTOR_CONFIG_FILE", "debezium-connectors/debezium-postgres-connector.config.json")


### Redis
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
REDIS_DB = int(os.environ.get("REDIS_DB", "0"))
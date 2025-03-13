import os

### Cassandra
CASSANDRA_CONTACT_POINTS = os.environ.get("CASSANDRA_CONTACT_POINTS", "localhost").split(",")
CASSANDRA_PORT = int(os.environ.get("CASSANDRA_PORT", "9042"))
CASSANDRA_KEYSPACE = os.environ.get("CASSANDRA_KEYSPACE", "mykeyspace")
CASSANDRA_TABLE = os.environ.get("CASSANDRA_TABLE", "mytable")
CASSANDRA_USERNAME = os.environ.get("CASSANDRA_USERNAME", "")
CASSANDRA_PASSWORD = os.environ.get("CASSANDRA_PASSWORD", "")

### Kafka
KAFKA_BOOTSTRAP_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS")
KAFKA_TOPIC = os.environ.get("KAFKA_TOPIC")

### Postgres
POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.environ.get("POSTGRES_PORT", "5432"))
POSTGRES_USER = os.environ.get("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "postgres")
POSTGRES_DB = os.environ.get("POSTGRES_DB", "inventory")

### Debezium Connector
DEBEZIUM_CONNECT_URL = os.environ.get("DEBEZIUM_CONNECT_URL", "http://localhost:8083")
DEBEZIUM_CONNECTOR_CONFIG_FILE = os.environ.get("DEBEZIUM_CONNECTOR_CONFIG_FILE", "debezium-connector.config.json")

### Flink
FLINK_REST_API_URL = os.environ.get("FLINK_REST_API_URL", "http://jobmanager:8081")
FLINK_CONNECTOR_CASSANDRA_JAR = os.environ.get("FLINK_CONNECTOR_CASSANDRA_JAR", "flink-connector-cassandra_2.12-3.2.0-1.19.jar")
FLINK_CONNECTOR_KAFKA_JAR = os.environ.get("FLINK_CONNECTOR_KAFKA_JAR", "flink-connector-kafka-3.4.0-1.20.jar")
FLINK_JSON_JAR = os.environ.get("FLINK_JSON_JAR", "flink-json-1.20.1.jar")
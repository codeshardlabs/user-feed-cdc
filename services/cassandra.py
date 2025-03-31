from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from config import CassandraConfig
import logging

logger = logging.getLogger(__name__)

def get_cassandra_session(cassandra_config: CassandraConfig):
    try:
        logger.info(f"Connecting to Cassandra with config: {cassandra_config}")
        cluster = Cluster(
            cassandra_config.contact_points, 
            port=cassandra_config.port,
            auth_provider=PlainTextAuthProvider(
                username=cassandra_config.username,
                password=cassandra_config.password
            )
        )
        session = cluster.connect()
        logger.info("Successfully connected to Cassandra")
        return session
    except Exception as e:
        logger.error(f"Error connecting to Cassandra: {e}")
        raise Exception(f"Failed to connect to Cassandra: {str(e)}")
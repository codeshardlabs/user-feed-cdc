from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from config import CassandraConfig

def get_cassandra_session(cassandra_config: CassandraConfig):
    cluster = Cluster(
        cassandra_config.contact_points, 
        port=cassandra_config.port,
        auth_provider=PlainTextAuthProvider(
            username=cassandra_config.username,
            password=cassandra_config.password
        )
    )
    session = cluster.connect()
    return session
from redis import Redis
from env import REDIS_HOST, REDIS_PORT, REDIS_DB

# Initialize Redis with connection parameters
cache = Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    decode_responses=True
)

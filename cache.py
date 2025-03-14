from redis import Redis, StrictRedis 

cache = Redis(redis_client=StrictRedis(host='localhost', port=6379, db=0))

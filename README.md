
### User feed Change Data Capture

### Local Development
#### Cassandra DB

```bash
#!/bin/bash
docker network create cassandra
docker run --rm -d --name cassandra -p 9042:9042 --hostname cassandra --network cassandra cassandra
docker exec -it cassandra cqlsh

### create new keyspace
CREATE KEYSPACE IF NOT EXISTS user_activity 
WITH REPLICATION = { 'class' : 'SimpleStrategy', 'replication_factor' : 1 };

USE user_activity;

### create new table
CREATE TABLE IF NOT EXISTS user_feed (
    user_id UUID,
    activity_id TIMEUUID,
    activity_type TEXT,
    timestamp TIMESTAMP,
    target_id UUID,
    target_type TEXT,
    metadata MAP<TEXT, TEXT>,
    PRIMARY KEY ((user_id), activity_id)
) WITH CLUSTERING ORDER BY (activity_id DESC);
```

#### Local server

1. Create new virtual environment
```bash
python -m venv venv
```

2. Activate that environment
```bash
./venv/Scripts/activate
```

3. Run the development server
```bash
uvicorn main:app --reload
```
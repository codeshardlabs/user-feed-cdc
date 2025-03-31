## User Feed using Debezium Change Data Capture 

### Problem Statement 
This project implements a scalable user feed system that processes user activities in real-time while ensuring at least-once semantics and high availability. The system handles user interactions like follows, posts, comments and likes through a multi-stage data pipeline.

### Workflow

 ![Workflow](/public/workflow.png)

### Overview
This project implements a real-time data pipeline using Debezium for Change Data Capture (CDC) from PostgreSQL. At its core, Debezium monitors PostgreSQL's Write Ahead Log (WAL) for any data modifications, which requires configuring PostgreSQL with logical WAL level. When changes occur in the source PostgreSQL tables, Debezium captures these changes from the WAL and streams them to dedicated Kafka topics. A Kafka consumer service continuously polls these topics for new messages, processing them using a SchemaAdapterStrategyFactory that leverages Factory and Strategy patterns to transform the data into Cassandra's schema format. The transformed data is then batch inserted into Cassandra, chosen specifically for its distributed architecture and high write throughput capabilities. Cassandra's Log-Structured Merge (LSM) tree data structure optimizes write performance by first storing data in memory before flushing to disk, making it ideal for data ingestion scenarios.



### Technical Components

1. Source System (PostgreSQL)
- Primary database storing user activities and interactions
- Configured with logical replication (wal_level=logical) to enable Change Data Capture
- Handles transactional writes for user activities through REST API endpoints
- Tables are configured with primary keys and appropriate indexes

2. Change Data Capture (Debezium)
- Monitors PostgreSQL Write-Ahead Logs (WAL) for DML changes
- Ensures reliable capture of all data modifications
- Publishes changes to dedicated Kafka topics

3. Message Queue (Apache Kafka)
- Provides durable storage of change events
- Maintains strict ordering within partitions
- Enables parallel processing through multiple partitions
- Topics configured with appropriate retention and replication

4. Polling System (Kafka Consumer)
- Polls kafka topic for new message.
- When we receive new message/event, it modifies the data according to the reqd. format. 
- Saves the data in cassandra DB.

5. Cache Layer (Redis)
- In-memory caching of frequently accessed feeds
- Provides sub-millisecond read latency for hot data
- Falls back to Cassandra for cache misses

6. Sink System (Apache Cassandra)
- Log-Structured Merge (LSM) tree based storage
- Optimized for high-throughput writes
- Partitioned by user_id for efficient reads
- Stores feed items in time-sorted order
- Supports efficient pagination queries

### Data Flow
1. User performs activity (follow/post/comment/like) via REST API
2. Activity is recorded in PostgreSQL tables
3. Debezium captures change events from PostgreSQL WAL
4. Events are published to corresponding Kafka topics
5. Kafka consumer polls the kafka topic for new event messages and if there is one, it modifies and ingests data to Cassandra DB.
8. Redis caches frequently accessed feed segments
9. Feed API serves requests from cache with Cassandra fallback



 ### Possible Activity types to be listed on user feed
 - Follow User ("FOLLOWERS")
 - User Create New Post ("SHARDS")
 - User Comment on Post ("COMMENTS")
 - User Likes a post ("LIKES")

### Local Development
#### Start all the services

```bash
#!/bin/bash
docker-compose down -v
docker-compose pull
docker-compose up -d 
docker-compose ps 
```

#### Local server

1. Create new virtual environment
```bash
python3 -m venv venv
```

2. Activate that environment
```bash
source venv/bin/activate
```

3. Run the development server
```bash
uvicorn main:app --reload
```
4. Test the setup using a shell script
```bash
#!/bin/bash
chmod +x test_setup.sh
./test-setup.sh
```

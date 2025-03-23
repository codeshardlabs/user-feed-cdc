## User Feed using Debezium Change Data Capture and KFC(Kafka, Flink, Cassandra) Stack

### Problem Statement 
This project implements a scalable user feed system that processes user activities in real-time while ensuring exactly-once semantics and high availability. The system handles user interactions like follows, posts, comments and likes through a multi-stage data pipeline.

Key Technical Components:

1. Source System (PostgreSQL)
- Primary database storing user activities and interactions
- Configured with logical replication (wal_level=logical) to enable Change Data Capture
- Handles transactional writes for user activities through REST API endpoints
- Tables are configured with primary keys and appropriate indexes

2. Change Data Capture (Debezium)
- Monitors PostgreSQL Write-Ahead Logs (WAL) for DML changes
- Creates change events in Avro format with before/after states
- Ensures reliable capture of all data modifications
- Maintains offset tracking for exactly-once delivery
- Publishes changes to dedicated Kafka topics

3. Message Queue (Apache Kafka)
- Provides durable storage of change events
- Maintains strict ordering within partitions
- Enables parallel processing through multiple partitions
- Handles back-pressure and provides buffer capacity
- Topics configured with appropriate retention and replication

4. Change Data Capture (DataStax)
- Uses DataStax CDC Source Connector to capture changes from Kafka
- Automatically maps Kafka events to Cassandra table structures
- Maintains exactly-once delivery semantics
- Handles schema evolution and data type conversions
- Built-in dead letter queue for error handling
- Configurable batching and throughput control
- Native integration with Cassandra authentication and security
- Provides detailed monitoring and metrics
- Supports automatic offset management
- Handles backpressure natively through Cassandra driver

5. Cache Layer (Redis)
- In-memory caching of frequently accessed feeds
- Implements sliding window cache invalidation
- Provides sub-millisecond read latency for hot data
- Uses sorted sets for feed pagination
- Falls back to Cassandra for cache misses

6. Storage Layer (Apache Cassandra)
- Log-Structured Merge (LSM) tree based storage
- Optimized for high-throughput writes
- Partitioned by user_id for efficient reads
- Stores feed items in time-sorted order
- Supports efficient pagination queries

Data Flow:
1. User performs activity (follow/post/comment/like) via REST API
2. Activity is recorded in PostgreSQL tables
3. Debezium captures change events from PostgreSQL WAL
4. Events are published to corresponding Kafka topics
5. Datastax CDC captures change events from Kafka topics and transfer them to Cassandra DB. 
8. Redis caches frequently accessed feed segments
9. Feed API serves requests from cache with Cassandra fallback

The architecture ensures:
- Exactly-once processing semantics
- Horizontal scalability at each layer
- High write throughput for activity ingestion
- Low latency reads for feed serving
- Fault tolerance and high availability
- Efficient pagination support


### Workflow

 ![Workflow](/public/workflow.png)

 ### Possible Activity types to be listed on user feed
 - Follow User ("FOLLOW")
 - User Create New Post ("SHARD")
 - User Comment on Post ("COMMENT")
 - User Likes a post ("LIKE")

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

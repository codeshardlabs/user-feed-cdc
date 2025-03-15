#!/bin/bash

echo "Setting up test scenario..."

# Setup Debezium connector
echo "Setting up Debezium connector..."
curl -X GET "http://localhost:8000/debezium/setup" 
echo -e "\nDebezium connector setup completed!"

# User 3 follows user 2
echo "Making user 3 follow user 2..."
curl -X POST "http://localhost:8000/follow/user" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "3",
    "other_user_id": "2"
  }'

echo -e "\nWaiting for follow relationship to be established..."
sleep 2

echo -e "\nWaiting for CDC to process the changes..."
sleep 10

### Setup flink job
echo "Setting up Flink job..."
curl -X POST "http://localhost:8000/job/start" \
  -H "Content-Type: application/json" \
  -d '{
    "job_name": "kafka-to-cassandra"
  }'
echo -e "\nFlink job setup completed!"

sleep 10

# Get user 1's feed
echo "Getting user 1's feed (should see user 3's activities)..."
curl -X GET "http://localhost:8000/cassandra/activities?user_id=1&limit=10" \
  -H "Content-Type: application/json" | json_pp

echo -e "\nTest scenario completed!"  
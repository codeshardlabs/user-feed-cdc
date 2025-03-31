#!/bin/bash

echo "Setting up test scenario..."

# Setup Debezium connector
echo "Setting up Debezium connector..."
curl -X GET "http://localhost:8000/debezium/setup" 
echo -e "\nDebezium connector setup completed!"

# User 2 follows user 1
echo "Making user 2 follow user 1..."
curl -X POST "http://localhost:8000/follow/user" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "2",
    "other_user_id": "1"
  }'

echo -e "\nWaiting for follow relationship to be established..."
sleep 2

echo -e "\nWaiting for CDC to process the changes..."
sleep 10

echo -e "\nStart processing activities..."
curl -X POST "http://localhost:8000/start"

sleep 30

# Get user 1's feed
echo "Getting user 1's feed (should see user 2's activities)..."
curl -X GET "http://localhost:8000/cassandra/activities?user_id=1&limit=10" \
  -H "Content-Type: application/json" | json_pp

echo -e "\nTest scenario completed!"  
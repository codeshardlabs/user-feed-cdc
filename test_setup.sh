#!/bin/bash

echo "Setting up test scenario..."

# Setup Debezium connector
echo "Setting up Debezium connector..."
curl -X POST "http://localhost:8000/setup/debezium" \
  -H "Content-Type: application/json"

# Get Debezium connector status
echo -e "\nGetting Debezium connector status..."
curl -X GET "http://localhost:8083/connectors/postgres-connector/status" \
  -H "Content-Type: application/json" | json_pp

echo -e "\nWaiting for Debezium connector to initialize..."
sleep 5

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
sleep 5

# Get user 1's feed
echo "Getting user 1's feed (should see user 3's activities)..."
curl -X GET "http://localhost:8000/cassandra/activities?user_id=1&limit=10" \
  -H "Content-Type: application/json" | json_pp

echo -e "\nTest scenario completed!"  
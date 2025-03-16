-- Create the keyspace
CREATE KEYSPACE IF NOT EXISTS codeshard 
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

-- Create the user activity table
CREATE TABLE IF NOT EXISTS codeshard.user_activity (
    user_id UUID,
    activity_id TIMEUUID,
    activity_type TEXT,
    event_timestamp TIMESTAMP,
    target_id UUID,
    target_type TEXT,
    metadata MAP<TEXT, TEXT>,
    PRIMARY KEY ((user_id), activity_id)
) WITH CLUSTERING ORDER BY (activity_id DESC);

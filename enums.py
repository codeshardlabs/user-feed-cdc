from enum import Enum


class JobName(Enum): 
    KAFKA_TO_CASSANDRA = "kafka-to-cassandra"


class ActivityType(Enum): 
    FOLLOW = "follow"
    LIKE = "like"
    COMMENT = "comment"
    SHARD = "shard"


class TableName(Enum): 
    FOLLOWERS = "followers"
    LIKES = "likes"
    COMMENTS = "comments"
    SHARDS = "shards"

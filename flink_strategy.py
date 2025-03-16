from abc import ABC, abstractmethod
from logger import logger
from typing import List
from enums import ActivityType, TableName
from env import KAFKA_BOOTSTRAP_SERVERS

class DataStreamAdaptorStrategy(ABC): 
    @abstractmethod
    def get_create_table_query(self) -> str: 
        logger.error("Method not implemented")
        pass
    @abstractmethod
    def get_transform_data_query(self) -> str: 
        logger.error("Method not implemented")
        pass
    
    
class DataStreamAdaptorStrategy1(DataStreamAdaptorStrategy): 
    def __init__(self): 
        self.activity_type = ActivityType.FOLLOW.value
        self.table_name = TableName.FOLLOWERS.value
        self.kafka_topic = f"postgres.public.{self.table_name}"
        
    
    def get_create_table_query(self) -> str: 
        logger.info(f"get_create_table_query for {self.table_name}: invoked")
        return f"""
                 CREATE TABLE kafka_source_{self.table_name} (
                    id STRING, 
                    follower_id STRING,
                    following_id STRING,
                    created_at BIGINT,
                    updated_at BIGINT,
                    __deleted BOOLEAN, 
                    __op STRING,
                    __table STRING, 
                    __source_ts_ms BIGINT, 
                    proctime AS PROCTIME()
                ) WITH (
                    'connector' = 'kafka',
                    'topic' = '{self.kafka_topic}',
                    'properties.bootstrap.servers' = '{KAFKA_BOOTSTRAP_SERVERS}',
                    'properties.group.id' = '1',
                    'scan.startup.mode' = 'latest-offset',
                    'format' = 'json'
                )
            """

    def get_transform_data_query(self) -> str: 
        logger.info(f"get_transform_data_query for {self.table_name}: invoked")
        return f"""
            CREATE VIEW transformed_{self.table_name} AS
            SELECT
                follower_id AS user_id,
                '{self.activity_type}' AS activity_type,
                __source_ts_ms AS timestamp,
                following_id AS target_id,
                'user' AS target_type,
                CAST(MAP[
                    'source_table', '{self.table_name}',
                    'activity_type', '{self.activity_type}'
                ]  AS MAP<STRING, STRING>) AS \metadata,
                '{self.table_name}' AS source_table
            FROM kafka_source_{self.table_name}
            WHERE __op IN ('c', 'r') AND __deleted = FALSE
        """
    
class DataStreamAdaptorStrategy2(DataStreamAdaptorStrategy): 
    def __init__(self): 
        self.activity_type = ActivityType.LIKE.value
        self.table_name = TableName.LIKES.value
        self.kafka_topic = f"postgres.public.{self.table_name}"
        
    def get_create_table_query(self) -> str: 
        logger.info(f"get_create_table_query for {self.table_name}: invoked")
        return f"""
            CREATE TABLE kafka_source_{self.table_name} (
                id STRING, 
                user_id STRING,
                shard_id STRING,
                created_at BIGINT,
                updated_at BIGINT,
                __deleted BOOLEAN, 
                __op STRING,
                __table STRING, 
                __source_ts_ms BIGINT,   
                proctime AS PROCTIME()      
            ) WITH (
                'connector' = 'kafka',
                'topic' = '{self.kafka_topic}',
                'properties.bootstrap.servers' = '{KAFKA_BOOTSTRAP_SERVERS}',
                'properties.group.id' = '1',
                'scan.startup.mode' = 'latest-offset',
                'format' = 'json'
            )
        """
    
    def get_transform_data_query(self) -> str: 
        logger.info(f"get_transform_data_query for {self.table_name}: invoked")
        return f""" 
            CREATE VIEW transformed_{self.table_name} AS
            SELECT
                user_id AS user_id,
                '{self.activity_type}' AS activity_type,
                __source_ts_ms AS timestamp,
                shard_id AS target_id,  
                'shard' AS target_type,
                CAST(MAP[
                    'source_table', '{self.table_name}',
                    'activity_type', '{self.activity_type}'
                ]  AS MAP<STRING, STRING>) AS \metadata,
                '{self.table_name}' AS source_table
            FROM kafka_source_{self.table_name}
            WHERE __op IN ('c', 'r') AND __deleted = FALSE
        """
    
class DataStreamAdaptorStrategy3(DataStreamAdaptorStrategy): 
    def __init__(self): 
        self.activity_type = ActivityType.COMMENT.value
        self.table_name = TableName.COMMENTS.value
        self.kafka_topic = f"postgres.public.{self.table_name}"
        
    def get_create_table_query(self) -> str: 
        logger.info(f"get_create_table_query for {self.table_name}: invoked")
        return f"""
            CREATE TABLE kafka_source_{self.table_name} (
                id STRING, 
                user_id STRING,
                shard_id STRING,
                content STRING,
                created_at BIGINT,
                updated_at BIGINT,
                __deleted BOOLEAN, 
                __op STRING,
                __table STRING, 
                __source_ts_ms BIGINT, 
                proctime AS PROCTIME()
            ) WITH (
                'connector' = 'kafka',
                'topic' = '{self.kafka_topic}',
                'properties.bootstrap.servers' = '{KAFKA_BOOTSTRAP_SERVERS}',
                'properties.group.id' = '1',
                'scan.startup.mode' = 'latest-offset',
                'format' = 'json'
            )
        """
    
    def get_transform_data_query(self) -> str: 
        logger.info(f"get_transform_data_query for {self.table_name}: invoked")
        return f""" 
            CREATE VIEW transformed_{self.table_name} AS
            SELECT
                user_id AS user_id,
                '{self.activity_type}' AS activity_type,
                __source_ts_ms AS timestamp,
                shard_id AS target_id,
                'shard' AS target_type,
                CAST(MAP[
                    'source_table', '{self.table_name}',
                    'activity_type', '{self.activity_type}'
                ]  AS MAP<STRING, STRING>) AS \metadata,
                '{self.table_name}' AS source_table
            FROM kafka_source_{self.table_name}
            WHERE __op IN ('c', 'r') AND __deleted = FALSE
        """
    
class DataStreamAdaptorStrategy4(DataStreamAdaptorStrategy): 
    def __init__(self): 
        self.activity_type = ActivityType.SHARD.value
        self.table_name = TableName.SHARDS.value
        self.kafka_topic = f"postgres.public.{self.table_name}"
        
    def get_create_table_query(self) -> str: 
        logger.info(f"get_create_table_query for {self.table_name}: invoked")
        return f"""
            CREATE TABLE kafka_source_{self.table_name} (
                id STRING, 
                user_id STRING,
                title STRING,
                mode STRING,
                type STRING,
                created_at BIGINT,
                updated_at BIGINT,
                __deleted BOOLEAN, 
                __op STRING,
                __table STRING, 
                __source_ts_ms BIGINT, 
                proctime AS PROCTIME()
            ) WITH (
                'connector' = 'kafka',
                'topic' = '{self.kafka_topic}',
                'properties.bootstrap.servers' = '{KAFKA_BOOTSTRAP_SERVERS}',
                'properties.group.id' = '1',
                'scan.startup.mode' = 'latest-offset',
                'format' = 'json'
            )
        """
    
    def get_transform_data_query(self) -> str: 
        logger.info(f"get_transform_data_query for {self.table_name}: invoked")
        return f""" 
            CREATE VIEW transformed_{self.table_name} AS
            SELECT  
                user_id AS user_id,
                '{self.activity_type}' AS activity_type,
                __source_ts_ms AS timestamp,
                id AS target_id,
                'shard' AS target_type,
                CAST(MAP[
                    'source_table', '{self.table_name}',
                    'activity_type', '{self.activity_type}'
                ]  AS MAP<STRING, STRING>) AS \metadata,
                '{self.table_name}' AS source_table
            FROM kafka_source_{self.table_name}
            WHERE __op IN ('c', 'r') AND __deleted = FALSE
        """


class DataStreamAdaptorStrategyFactory: 
    def get_strategy(self, activity_type: ActivityType) -> DataStreamAdaptorStrategy: 
        if activity_type == ActivityType.FOLLOW: 
            return DataStreamAdaptorStrategy1()
        elif activity_type == ActivityType.LIKE: 
            return DataStreamAdaptorStrategy2()
        elif activity_type == ActivityType.COMMENT: 
            return DataStreamAdaptorStrategy3()
        elif activity_type == ActivityType.SHARD: 
            return DataStreamAdaptorStrategy4()
        else: 
            logger.error(f"No strategy found for activity type: {activity_type}")
            raise ValueError(f"No strategy found for activity type: {activity_type}")
from abc import ABC, abstractmethod
from enums import TableType
from config import CassandraRecord
import uuid 
from typing import Union

class  SchemaAdapterStrategy(ABC): 
    @abstractmethod
    def transform(self, data: dict) -> CassandraRecord: 
        pass 

    def validate_data(self, data: dict) -> bool:
        print("validate_data: invoked", data)
        if  "__op" not in data or "__table" not in data or "__source_ts_ms" not in data:
            return False
        if data["__op"] != 'c':
            return False
        return True
        

class SchemaAdapterStrategy1(SchemaAdapterStrategy):
    def __init__(self):
        self.table_name = TableType.LIKES
    def transform(self, data: dict) -> CassandraRecord:
        if not self.validate_data(data):
            return None
        print("transform type 1: invoked", data)
        
        src_table = data["__table"];
        ts_ms = data["__source_ts_ms"]
        activity_type = "LIKE_SHARD" 
        user_id = data["liked_by"]
        shard_id = str(data["shard_id"])
        return CassandraRecord(
            user_id=user_id,
            activity_id=uuid.uuid1(), 
            activity_type=activity_type,
            event_timestamp=ts_ms,
            target_id=shard_id,
            target_type="shard",
            metadata={
                "source_table" : src_table,
                 "primary_key_value" : str(data["id"]),
                "primary_key_field" : "id",
                "primary_key_type" : "integer"
            }
        )

class SchemaAdapterStrategy2(SchemaAdapterStrategy):
    def __init__(self):
        self.table_name = TableType.COMMENTS
    def transform(self, data: dict) -> CassandraRecord:
        if not self.validate_data(data):
            return None
        print("transform type 2: invoked", data)
        
        src_table = data["__table"];
        ts_ms = data["__source_ts_ms"]
        activity_type = "COMMENT_SHARD" 
        user_id = data["user_id"]
        shard_id = str(data["shard_id"])
        return CassandraRecord(
            user_id=user_id,
            activity_id=uuid.uuid1(), 
            activity_type=activity_type,    
            event_timestamp=ts_ms,
            target_id=shard_id,
            target_type="shard",
            metadata={
                "message" : data["message"],
                "source_table": src_table,
                "primary_key_value" : str(data["id"]),
                "primary_key_field" : "id",
                "primary_key_type" : "integer"
            }
        )

class SchemaAdapterStrategy3(SchemaAdapterStrategy):
    def __init__(self):
        self.table_name = TableType.SHARDS
    def transform(self, data: dict) -> CassandraRecord:
        if not self.validate_data(data):
            return None
        print("transform type 3: invoked", data)
        
        src_table = data["__table"];
        ts_ms = data["__source_ts_ms"]
        activity_type = "CREATE_SHARD" 
        user_id = data["user_id"]
        shard_id = str(data["id"])
        return CassandraRecord(
            user_id=user_id,
            activity_id=uuid.uuid1(), 
            activity_type=activity_type,
            event_timestamp=ts_ms,
            target_id=shard_id,
            target_type="shard",
            metadata={
                "template_type": data["templateType"],
                "mode": data["mode"],
                "type" : data["type"],
                "title": data["title"],
                "source_table": src_table,
                "primary_key_value" : str(data["id"]),
                "primary_key_field" : "id",
                "primary_key_type" : "integer"
            }
        )

class SchemaAdapterStrategy4(SchemaAdapterStrategy):
    def __init__(self):
        self.table_name = TableType.FOLLOWERS
    def transform(self, data: dict) -> CassandraRecord:
        if not self.validate_data(data):
            return None
        print("transform type 4: invoked", data)
        src_table = data["__table"];
        ts_ms = data["__source_ts_ms"]
        activity_type = "FOLLOW_USER" 
        follower_id = data["follower_id"]
        following_id = data["following_id"]
        return CassandraRecord(
            user_id=follower_id,
            activity_id=uuid.uuid1(), 
            activity_type=activity_type,  
            event_timestamp=ts_ms,
            target_id=following_id,
            target_type="user",
            metadata={
                "source_table": src_table,
                 "primary_key_value" : str(data["id"]),
                "primary_key_field" : "id",
                "primary_key_type" : "integer"
            }
        )

class SchemaAdapterStrategyFactory:
    @staticmethod
    def get_strategy(strategy_name: TableType) -> SchemaAdapterStrategy:
        if strategy_name == TableType.LIKES:
            return SchemaAdapterStrategy1()
        elif strategy_name == TableType.COMMENTS:
            return SchemaAdapterStrategy2()
        elif strategy_name == TableType.SHARDS:
            return SchemaAdapterStrategy3()
        elif strategy_name == TableType.FOLLOWERS:
            return SchemaAdapterStrategy4()
        else:
            raise ValueError(f"Invalid strategy name: {strategy_name}")
        


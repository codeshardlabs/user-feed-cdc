from abc import ABC, abstractmethod
from enums import TableType
from config import CassandraRecord
class  SchemaAdapterStrategy(ABC): 
    @abstractmethod
    def transform(self, data: dict) -> CassandraRecord: 
        pass 

    def validate_data(self, data: dict) -> bool:
        if not hasattr(data, "__op") or not hasattr(data, "__table") or not hasattr(data, "__source_ts_ms"):
            return False
        if data["__op"] != "c":
            return False
        return True

class SchemaAdapterStrategy1(SchemaAdapterStrategy):
    def __init__(self):
        self.table_name = TableType.LIKES
    def transform(self, data: dict) -> CassandraRecord:
        if not self.validate_data(data):
            return None
        
        src_table = data["__table"];
        ts_ms = data["__source_ts_ms"]
        activity_type = "LIKE_SHARD" 
        return CassandraRecord(
            user_id=data["liked_by"],
            activity_type=activity_type,
            timestamp=ts_ms,
            target_id=str(data["shard_id"]),
            target_type="shard",
            metadata={
                "source_table" : src_table,
                "primary_key": str(data["id"])
            },
            source_table=src_table
        )

class SchemaAdapterStrategy2(SchemaAdapterStrategy):
    def __init__(self):
        self.table_name = TableType.COMMENTS
    def transform(self, data: dict) -> CassandraRecord:
        if not self.validate_data(data):
            return None
        
        src_table = data["__table"];
        ts_ms = data["__source_ts_ms"]
        activity_type = "COMMENT_SHARD" 
        return CassandraRecord(
            user_id=data["user_id"],
            activity_type=activity_type,    
            timestamp=ts_ms,
            target_id=str(data["shard_id"]),
            target_type="shard",
            metadata={
                "message" : data["message"],
                "source_table": src_table,
                "primary_key": str(data["id"])
            },
            source_table=src_table
        )

class SchemaAdapterStrategy3(SchemaAdapterStrategy):
    def __init__(self):
        self.table_name = TableType.SHARDS
    def transform(self, data: dict) -> CassandraRecord:
        if not self.validate_data(data):
            return None
        
        src_table = data["__table"];
        ts_ms = data["__source_ts_ms"]
        activity_type = "CREATE_SHARD" 
        return CassandraRecord(
            user_id=data["user_id"],
            activity_type=activity_type,
            timestamp=ts_ms,
            target_id=str(data["id"]),
            target_type="shard",
            metadata={
                "template_type": data["templateType"],
                "mode": data["mode"],
                "type" : data["type"],
                "title": data["title"],
                "source_table": src_table,
                "primary_key" : str(data["id"])
            },
            source_table=src_table
        )

class SchemaAdapterStrategy4(SchemaAdapterStrategy):
    def __init__(self):
        self.table_name = TableType.FOLLOWERS
    def transform(self, data: dict) -> CassandraRecord:
        if not self.validate_data(data):
            return None
        
        src_table = data["__table"];
        ts_ms = data["__source_ts_ms"]
        activity_type = "FOLLOW_USER" 
        return CassandraRecord(
            user_id=data["follower_id"],
            activity_type=activity_type,  
            timestamp=ts_ms,
            target_id=str(data["following_id"]),
            target_type="user",
            metadata={
                "source_table": src_table,
                "primary_key": str(data["id"])
            },
            source_table=src_table
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
        


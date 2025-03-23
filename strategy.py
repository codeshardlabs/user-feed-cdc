from abc import ABC, abstractmethod
from enums import TableType

class  SchemaAdapterStrategy(ABC): 
    @abstractmethod
    def transform(self, data: dict) -> dict: 
        pass 

class SchemaAdapterStrategy1(SchemaAdapterStrategy):
    def __init__(self):
        self.table_name = TableType.LIKES
    def transform(self, data: dict) -> dict:
        pass

class SchemaAdapterStrategy2(SchemaAdapterStrategy):
    def __init__(self):
        self.table_name = TableType.COMMENTS
    def transform(self, data: dict) -> dict:
        pass

class SchemaAdapterStrategy3(SchemaAdapterStrategy):
    def __init__(self):
        self.table_name = TableType.SHARDS
    def transform(self, data: dict) -> dict:
        pass

class SchemaAdapterStrategy4(SchemaAdapterStrategy):
    def __init__(self):
        self.table_name = TableType.FOLLOWERS
    def transform(self, data: dict) -> dict:
        pass

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

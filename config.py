from pydantic import BaseModel
from typing import Optional, Dict
class FlinkJobConfig(BaseModel):
    job_name: str
    parallelism: int = 1
    checkpoint_interval: int = 10000 ## in milliseconds


class FollowUserRequestBody(BaseModel):
    user_id: str
    other_user_id: str

class CreatePostRequestBody(BaseModel):
    user_id: str
    title: str

class DataRecord(BaseModel):
    user_id: str
    activity_type: str
    timestamp: int
    target_id: Optional[str] = None
    target_type: Optional[str] = None
    metadata: Dict[str, str]
    source_table: Optional[str] = None
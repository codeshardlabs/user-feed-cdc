from pydantic import BaseModel
class FlinkJobConfig(BaseModel):
    job_name: str
    parallelism: int = 1
    checkpoint_interval: int = 10000 ## in milliseconds

from fastapi import FastAPI
from typing import Union

from cassandra.cluster import Cluster 

cluster = Cluster()
session = cluster.connect('user_activity')

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello" : "World"};

@app.get("/items/{item_id}")
def read_items(item_id: int, q: Union[str,None] = None):
    return {"item_id": item_id,"q": q }



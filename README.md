
### User feed using Change Data Capture and  KFC(Kafka, Flink, Cassandra) Stack

### Local Development
#### Cassandra DB

```bash
#!/bin/bash
docker network create cassandra
docker run --rm -d --name cassandra -p 9042:9042 --hostname cassandra --network cassandra cassandra
```
#### Local server

1. Create new virtual environment
```bash
python3 -m venv venv
```

2. Activate that environment
```bash
source venv/bin/activate
```

3. Run the development server
```bash
uvicorn main:app --reload
```

### Workflow

 ![Workflow](/public/workflow.png)
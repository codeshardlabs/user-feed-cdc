
### User feed using Change Data Capture and  KFC(Kafka, Flink, Cassandra) Stack

### Local Development
#### Start all the services

```bash
#!/bin/bash
docker-compose pull
docker-compose up -d 
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

 ### Possible Activity types to be listed on user feed
 - Follow User ("FOLLOW")
 - User Create New Post ("SHARD")
 - User Comment on Post ("COMMENT")
 - User Likes a post ("LIKE")
import psycopg2
from fastapi import HTTPException
from config import PostgresConfig

def get_postgres_connection(postgres_config: PostgresConfig):
    try: 
        conn = psycopg2.connect(
            host= postgres_config.host,
            port= postgres_config.port,
            user= postgres_config.username,
            password= postgres_config.password,
            dbname= postgres_config.dbname
            ) 
        return conn
    except Exception as e:
        print(f"Error connecting to postgres: {e}")
        raise HTTPException(status_code=500, detail="Failed to connect to postgres : {str(e)}")
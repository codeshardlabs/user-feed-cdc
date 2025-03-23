import requests
import json
from config import DebeziumConfig, PostgresConfig
async def setup_debezium_connector(debezium_config: DebeziumConfig, postgres_config: PostgresConfig):
    try: 
        # First verify Debezium Connect is available
        health_check = requests.get(f"{debezium_config.url}/")
        if health_check.status_code != 200:
            raise Exception(f"Debezium Connect is not healthy. Status code: {health_check.status_code}")

        with open(debezium_config.connector_config_file, "r") as f:
            config = json.load(f)
            
        # Update configuration with environment variables
        config["config"]["database.hostname"] = postgres_config.host
        config["config"]["database.port"] = postgres_config.port
        config["config"]["database.user"] = postgres_config.username
        config["config"]["database.password"] = postgres_config.password
        config["config"]["database.dbname"] = postgres_config.dbname
        
        # Check if connector already exists
        response = requests.get(f"{debezium_config.url}/connectors/postgres-connector")
        if response.status_code == 200:
            print("Debezium connector already exists")
            return {"status": "success", "message": "Debezium connector already exists"}
            
        # Create new connector
        response = requests.post(
            f"{debezium_config.url}/connectors",
            headers={"Content-Type": "application/json"},
            json=config
        )
        
        if response.status_code not in [200, 201]:
            raise Exception(f"Failed to create connector. Status: {response.status_code}, Response: {response.text}")
            
        return {"status": "success", "message": "Debezium connector created successfully"}
        
    except requests.exceptions.ConnectionError as e:
        print(f"Connection error to Debezium Connect: {e}")
        raise Exception(f"Failed to connect to Debezium Connect: {str(e)}")
    except Exception as e:
        print(f"Error setting up Debezium connector: {e}")
        raise Exception(f"Failed to set up Debezium connector: {str(e)}")


async def delete_debezium_connector(debezium_config: DebeziumConfig):
    try:
        response = requests.delete(f"{debezium_config.url}/connectors/postgres-connector")
        if response.status_code == 200:
            print("Debezium connector deleted successfully")
            return {"status": "success", "message": "Debezium connector deleted successfully"}
        else:
            raise Exception(f"Failed to delete connector. Status: {response.status_code}, Response: {response.text}")
    except Exception as e:
        print(f"Error deleting Debezium connector: {e}")
        raise Exception(f"Failed to delete Debezium connector: {str(e)}")

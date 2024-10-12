import os
import json
from datetime import datetime
from pymongo.mongo_client import MongoClient


MONGO_URI = os.environ.get("MONGO_URI")


client = MongoClient(MONGO_URI)
database = client["management"]
sensors_data_collection = database['sensors_data']
users_collection = database['users']

users = {}

def lambda_handler(event, context):
    message = None
    try:
        api_key = event['headers']['x-api-key']
        
        if api_key not in users.keys():
            print("Voy a buscar el user a mongo")
            cursor = users_collection.find( { "apikey": api_key } )
            user = list(cursor)
            users[api_key] = str(user[0]['_id'])
        
        print(f"Los usuarios son: {str(users)}")
        
        sensors_data = json.loads(event["body"])
        
        for key in sensors_data.keys():
            if type(sensors_data[key]) == float:
                sensors_data[key] = round(sensors_data[key], 2)
        
        print(f"Data: {str(sensors_data)}")
        
        sensors_data['timestamp'] = datetime.now()
        sensors_data['user_id'] = users[api_key]
        
        result = sensors_data_collection.insert_one(sensors_data)
        
        if result.inserted_id:
            message = "Document inserted successfully"
        else:
            message = "Failed to insert document"
        
    except Exception as e:
        print(e)
        message = str(e)
        
    print(message)
    return {
        'statusCode': 200,
        'body': message
    }

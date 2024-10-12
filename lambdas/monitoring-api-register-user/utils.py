import os
import logging
import json
from pymongo.mongo_client import MongoClient

logger = logging.getLogger()
logger.setLevel('INFO')


MONGO_URI = os.environ.get("MONGO_URI")


def get_field_from_headers(event, field):
    data = None
    if event['headers'] and field in event['headers']:
        data = event['headers'][field]
    else:
        raise ValueError(f'The {field} header does not exist.')
    return data

def get_field_from_body(event, field):
    data = None
    body = json.loads(event['body'])
    if body and field in body:
        data = body[field]
    else:
        raise ValueError(f'The {field} body attribute does not exist.')
    return data


def query_mongo(query_field, data_field):
    client = MongoClient(MONGO_URI)
    database = client["management"]
    users_collection = database['users']
    
    cursor = users_collection.find({query_field: data_field})
        
    client.close()

    return list(cursor)
    

def insert_mongo(apikey, user, email):
    result = None
    client = MongoClient(MONGO_URI)
    database = client["management"]
    users_collection = database['users']
    
    result = users_collection.insert_one({'apikey': apikey, 'user': user, 'email': email})
    
    if not result.inserted_id:
        raise ValueError('User could not be registered.')
    
    return result
    
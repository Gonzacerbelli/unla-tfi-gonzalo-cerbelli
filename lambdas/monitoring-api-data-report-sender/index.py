import os
import json
from pymongo.mongo_client import MongoClient
from utils import get_sensors_data, send_request_to_cohere, send_email, html_report


MONGO_URI = os.environ.get("MONGO_URI")


def lambda_handler(event, context):
    
    try:
        client = MongoClient(MONGO_URI)
        database = client["management"]
        users_collection = database['users']
        users_cursor = users_collection.find()
        users = list(users_cursor)
    
        for user in users:
            user_id = user['_id']
            user_email = user['email']
    
            results = get_sensors_data(database, user_id)
    
            if results:
                cohere_response = send_request_to_cohere(html_report, results)
                mailgun_response = send_email(cohere_response['text'], user_email)

                message = mailgun_response.json()
                status_code = mailgun_response.status_code

    except Exception as e:
        print(f"Ocurrió un error: {e}")
        message = {"error": e}
        status_code = 500
    
    
    return {
        'statusCode': status_code,
        'body': json.dumps(message)
    }

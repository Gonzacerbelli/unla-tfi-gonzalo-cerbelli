import json
import logging
import traceback
import boto3
from utils import get_field_from_body, query_mongo, insert_mongo

logger = logging.getLogger()
logger.setLevel('INFO')

apigw = boto3.client('apigateway')

def lambda_handler(event, context):
    message = None
    try:
        user = get_field_from_body(event, 'user')
        email = get_field_from_body(event, 'email')

        results = query_mongo('email', email)
        logger.info(f'results: {results}')
        
        if len(results) and results[0]['email'] == email:
            message = {'message': 'email is already registered.'}
            
        else:
            results = query_mongo('user', user)
            logger.info(f'results: {results}')
            
            if len(results) and results[0]['user'] == user:
                message = {'message': 'user is already registered.'}
        
        if not message:
            apikey_response = apigw.create_api_key(
                name='monitoring-api-'+user,
                enabled=True
            )
            
            api_key_id = apikey_response['id']
            usage_plan_id = '1drykn'
            key_type = 'API_KEY' 
            
            usage_plan_response= apigw.create_usage_plan_key(
                 usagePlanId= usage_plan_id,
                 keyId=api_key_id,
                 keyType=key_type
             )
            
            insert_mongo(apikey_response['value'], user, email)
            message = {'message':'user registered successfully, remember to save your apikey.', 'apikey': apikey_response['value']}
        
    except Exception as e:
        message = {'message': str(e)}
        print(traceback.format_exc())
        logger.error(f'Error: {message}')
        
    print(message)
    return {
        'statusCode': 200,
        'body': json.dumps(message)
    }


import awsgi
from app import app 

def handler(event, context):
    """
    AWS Lambda handler to forward API Gateway events to Flask app via awsgi.
    """
    return awsgi.response(app, event, context)



    
    
def lambda_handler(event, context):
    return awsgi.response(app, event, context)
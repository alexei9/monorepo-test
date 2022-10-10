import boto3
import configparser
from salesforce_prototype_app.config.config_values import get_config_value

def get_boto3():
    session = boto3.Session(
        aws_access_key_id=get_config_value('AWS_Dev', 'aws_access_key_id'),
        aws_secret_access_key=get_config_value('AWS_Dev', 'aws_secret_access_key'),
        aws_session_token=get_config_value('AWS_Dev', 'aws_session_token')
    )
    s3 = session.client('s3')
    return s3
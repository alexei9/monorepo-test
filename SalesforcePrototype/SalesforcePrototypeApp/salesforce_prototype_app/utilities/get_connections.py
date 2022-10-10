# import pyodbc
import boto3
from salesforce_prototype_app.config.config_values import get_config_value
import salesforce_prototype_app.utilities.app_environment as app_env
from simple_salesforce import Salesforce

def get_boto3():
    if app_env.is_running_in_aws():
        session = boto3.Session()
        s3 = session.client('s3')
        return s3

    else:
        session = boto3.Session(
            aws_access_key_id=get_config_value('AWS_Dev', 'aws_access_key_id'),
            aws_secret_access_key=get_config_value('AWS_Dev', 'aws_secret_access_key'),
            aws_session_token=get_config_value('AWS_Dev', 'aws_session_token')
        )
        s3 = session.client('s3')
        return s3


def get_salesforce():
    sf = Salesforce(
        username = get_config_value('Salesforce', 'username'),
        password = get_config_value('Salesforce', 'password'),
        security_token = get_config_value('Salesforce', 'security_token'),
        domain = get_config_value('Salesforce', 'domain'))

    return sf




# import pyodbc
import boto3
import snowflake.connector
from sandbox_salesforce.config.config_values import get_config_value



def get_boto3():
    session = boto3.Session(
        aws_access_key_id=get_config_value('AWS_Sandbox', 'aws_access_key_id'),
        aws_secret_access_key=get_config_value('AWS_Sandbox', 'aws_secret_access_key'),
        aws_session_token=get_config_value('AWS_Sandbox', 'aws_session_token')
    )
    s3 = session.client('s3')
    return s3

def get_boto3_session():
    if app_env.is_running_in_aws():
        return boto3.Session()
    else:
        return boto3.Session(
            aws_access_key_id=app_env.get_env_var_value(app_env.EnvironmentVariableNames.AWS_ACCESS_KEY_ID),
            aws_secret_access_key=app_env.get_env_var_value(app_env.EnvironmentVariableNames.AWS_SECRET_ACCESS_KEY),
            aws_session_token=app_env.get_env_var_value(app_env.EnvironmentVariableNames.AWS_SESSION_TOKEN)
        )

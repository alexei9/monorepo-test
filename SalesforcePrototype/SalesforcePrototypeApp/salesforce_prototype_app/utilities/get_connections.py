import boto3
from salesforce_prototype_app.config.config_values import get_config_value
import salesforce_prototype_app.utilities.app_environment as app_env
from simple_salesforce import Salesforce

def get_boto3():
    if app_env.is_running_in_aws():
        session = boto3.Session()
        return session

    else:
        aws_profile_name = app_env.get_env_var_value(app_env.EnvironmentVariableNames.AWS_PROFILE_NAME)
        aws_region_name = app_env.get_env_var_value(app_env.EnvironmentVariableNames.AWS_REGION_NAME)
        session = boto3.Session(profile_name=aws_profile_name, region_name=aws_region_name)
        return session

        # session = boto3.Session(
        #     aws_access_key_id=get_config_value('AWS_Dev', 'aws_access_key_id'),
        #     aws_secret_access_key=get_config_value('AWS_Dev', 'aws_secret_access_key'),
        #     aws_session_token=get_config_value('AWS_Dev', 'aws_session_token')
        # )
        # return session


def get_s3():
    session = get_boto3()
    s3 = session.client('s3')
    return s3


def get_secretsmanager():
    session = get_boto3()
    secretsmanager = session.client('secretsmanager')
    return secretsmanager



def get_salesforce():
    if app_env.is_running_in_aws():
        sf = Salesforce(
            username=get_user_secret_from_aws("ageorge-dev-salesforce-prototype-username"),
            password=get_user_secret_from_aws("ageorge-dev-salesforce-prototype-password"),
            security_token=get_user_secret_from_aws("ageorge-dev-salesforce-prototype-security_token"),
            domain=get_user_secret_from_aws("ageorge-dev-salesforce-prototype-domain"))
        return sf
    else:
        sf = Salesforce(
            username = get_config_value('Salesforce', 'username'),
            password = get_config_value('Salesforce', 'password'),
            security_token = get_config_value('Salesforce', 'security_token'),
            domain = get_config_value('Salesforce', 'domain'))
    return sf

def get_user_secret_arn_from_aws(aws_secret_name: str) -> str:
    client = get_secretsmanager()

    response = client.list_secrets(
        MaxResults=10,
        Filters=[
            {
                'Key': 'name',
                'Values': [aws_secret_name]
            },
        ]
    )

    existing_secret_arn = None
    if 'SecretList' in response:
        matching_secrets = response['SecretList']
        if matching_secrets is not None and len(matching_secrets) > 0:
            existing_secret_arn = matching_secrets[0]['ARN']

    return existing_secret_arn

def get_user_secret_from_aws(aws_secret_name):

    client = get_secretsmanager()
    existing_secret_arn = get_user_secret_arn_from_aws(aws_secret_name)
    # Read secret
    response = client.get_secret_value(SecretId=existing_secret_arn)
    secret_json = response['SecretString']
    ## user_secret = SnowflakeUserSecret(aws_secret_name=aws_secret_name, secret_json=secret_json)
    ## print(len(secret_json))
    user_secret = secret_json
    x = len(user_secret)
    y = (user_secret.find(":"))
    z = user_secret[y + 2:-2]
    return z



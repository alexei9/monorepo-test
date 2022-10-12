import boto3
import json
import snowflake.connector
import uuid
from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend as crypto_default_backend
from cryptography.hazmat.primitives import serialization
from datetime import datetime

AWS_REGION_NAME = "eu-west-2"
AWS_PROFILE_NAME = "crukbidev"
AWS_SECRET_NAME = "ageorge_dev_salesforce_snowflake_secret"
# AWS_SECRET_DESC = get_config_value('AWS', 'AWS_SECRET_DESC')
SNOWFLAKE_ACCOUNT_NAME = "cruk.eu-west-2.privatelink"
# SNOWFLAKE_SSO_USER_NAME = get_config_value('Snowflake', 'SNOWFLAKE_SSO_USER_NAME') # the user used when creating/dropping the service user
SNOWFLAKE_USE_ROLE_NAME = "DEV_AG_SALESFORCE_ADMIN"

#SNOWFLAKE_USE_ROLE_NAME = "ADMIN - DEV - DEVELOPER"

SNOWFLAKE_SVC_USER_NAME = "DEV_AGEORGE_SALESFORCE_SNOWFLAKE_USER"
SNOWFLAKE_WAREHOUSE = "NON_PROD_ALL"

#SNOWFLAKE_SVC_USER_NAME = "SVC_DEV_AG_SALESFORCE"


def get_user_secret_arn_from_aws(client, aws_secret_name: str) -> str:
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


def get_user_secret_from_aws() -> dict:
    session = boto3.Session(region_name=AWS_REGION_NAME, profile_name=AWS_PROFILE_NAME)
    client = session.client('secretsmanager')
    existing_secret_arn = get_user_secret_arn_from_aws(client, AWS_SECRET_NAME)
    if existing_secret_arn is None or len(existing_secret_arn) == 0:
        raise ValueError('Unable to find secret with name ' + AWS_SECRET_NAME)
    response = client.get_secret_value(SecretId=existing_secret_arn)
    secret_json = json.loads(response['SecretString'])
    return secret_json


def get_private_key_bytes(private_key: str) -> bytes:
    private_key = '-----BEGIN PRIVATE KEY-----\n' + private_key + '\n-----END PRIVATE KEY-----'
    private_key_bytes = private_key.encode('utf-8')
    p_key = serialization.load_pem_private_key(
        private_key_bytes,
        password=None,
        backend=None)
    pkb = p_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption())
    return pkb


def get_snowflake_rsa_keys_connection(secret_dict: dict):
    private_key_bytes = get_private_key_bytes(secret_dict['private-key'])
    con = snowflake.connector.connect(
        account=SNOWFLAKE_ACCOUNT_NAME,
        user=secret_dict['user-name'],
        private_key=private_key_bytes,
        role=SNOWFLAKE_USE_ROLE_NAME,
        warehouse=SNOWFLAKE_WAREHOUSE
    )
    return con



def test_snowflake_service_user_authentication():
    # get existing user secret
    secret_dict = get_user_secret_from_aws()
    # connect to snowflake as service user and read Snowflake version
    con = get_snowflake_rsa_keys_connection(secret_dict)
    cursor = con.cursor()
    cursor.execute("SELECT CURRENT_VERSION()")
    value = cursor.fetchone()[0]
    print('Snowflake version: ' + value)
    print('Service user successfully established connection to Snowflake.')


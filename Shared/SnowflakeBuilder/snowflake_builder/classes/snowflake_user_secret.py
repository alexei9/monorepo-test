import json
import logging
import uuid
from datetime import datetime
import snowflake_builder.utilities.aws_utilities as aws_utilities


class SnowflakeUserSecret:
    """
    A class that represents a set of Snowflake user credentials using RSA key-pair authentication in JSON format
    that can be stored in AWS Secrets Manager.
    """
    def __init__(self, aws_secret_name: str, secret_json: str = None,
                 user_name: str = None, private_key: str = None, public_key: str = None, active_key: int = None,
                 created_utc: datetime = None, last_updated_utc: datetime = None):
        """
        Create a user-secret object, i.e. a set of Snowflake user credentials compatible with AWS Secrets Manager.
        When creating the object, specify either the JSON for an existing user-secret or the constituent parameters
        to create a new user-secret.

        Parameters
        ----------
        aws_secret_name : str
            The name of the secret in AWS Secrets Manager.
        secret_json : str
            The parameters for a user-secret encoded in JSON.
        user_name : str
            The name of a user in Snowflake.
        private_key : str
            The text representation of the private key associate with a user in Snowflake.
        public_key : str
            The text representation of the public key associated with a user in Snowflake.
        active_key : int
            Either 1 or 2, indicating which public key is the active for the user in Snowflake.
        created_utc : datetime
            The time when the user-secret was created.
        last_updated_utc : datetime
            The time when the user-secret was last updated - usually when the keys were last rotated.
        """
        self.aws_secret_name = aws_secret_name
        if secret_json is not None:
            secret_dict = json.loads(secret_json)
            self.user_name = secret_dict['user-name'] if 'user-name' in secret_dict else None
            self.private_key = secret_dict['private-key'] if 'private-key' in secret_dict else None
            self.public_key = secret_dict['public-key'] if 'public-key' in secret_dict else None
            self.key_number = secret_dict['active-key'] if 'active-key' in secret_dict else None
            if 'created-utc' in secret_dict:
                self.created_utc = datetime.strptime(secret_dict['created-utc'], '%Y-%m-%d %H:%M:%S.%f')
            if 'last-updated-utc' in secret_dict:
                self.last_updated_utc = datetime.strptime(secret_dict['last-updated-utc'], '%Y-%m-%d %H:%M:%S.%f')

        if user_name is not None:
            self.user_name = user_name
        if private_key is not None:
            self.private_key = private_key
        if public_key is not None:
            self.public_key = public_key
        if active_key is not None:
            self.key_number = active_key
        if created_utc is not None:
            self.created_utc = created_utc
        if last_updated_utc is not None:
            self.last_updated_utc = last_updated_utc

    def to_json(self):
        secret_dict = {
            'user-name': self.user_name,
            'private-key': self.private_key,
            'public-key': self.public_key,
            'active-key': self.key_number,
            'created-utc': self.created_utc.strftime('%Y-%m-%d %H:%M:%S.%f'),
            'last-updated-utc': self.last_updated_utc.strftime('%Y-%m-%d %H:%M:%S.%f')
        }
        return json.dumps(secret_dict)

    def set_user_secret_to_aws(self, aws_secret_desc: str = None,
                               aws_region_name: str = None, aws_profile_name: str = None):
        logging.info('Setting snowflake credentials...')

        # does secret already exist?

        client = aws_utilities.get_aws_client('secretsmanager', aws_region_name, aws_profile_name)
        existing_secret_arn = get_user_secret_arn_from_aws(client, self.aws_secret_name)

        if existing_secret_arn is None or len(existing_secret_arn) == 0:
            logging.debug('Secret does not exist.')
        else:
            logging.debug('Secret exists.')

        # create/update the secret

        if existing_secret_arn is None:
            logging.debug('Creating AWS secret...')
            self.created_utc = datetime.utcnow()
            self.last_updated_utc = self.created_utc
            client.create_secret(
                Name=self.aws_secret_name,
                ClientRequestToken=str(uuid.uuid4()),
                Description=aws_secret_desc,
                SecretString=self.to_json()
            )
        else:
            logging.debug('Updating AWS secret...')
            self.last_updated_utc = datetime.utcnow()
            client.put_secret_value(
                SecretId=existing_secret_arn,
                ClientRequestToken=str(uuid.uuid4()),
                SecretString=self.to_json()
            )

        logging.info('Set snowflake credentials.')


def get_user_secret_arn_from_aws(client, aws_secret_name: str) -> str:
    """
    Perform a lookup in AWS Secrets Manager to check if a secret exists with the specified name and retrieve the AWS ARN
    of the existing secret.

    Parameters
    ----------
    client : client
        A boto3 client object that can be used to make API requests to AWS Secrets Manager.
    aws_secret_name : str
        The name of the secret in AWS Secrets Manager.

    Returns
    -------
    str|None
        If the specified secret exists, then the ARN of an existing secret in AWS Secrets Manager, otherwise None.
    """
    logging.debug('Checking whether AWS secret exists...')

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
            logging.debug('Existing secret ARN: ' + existing_secret_arn)

    logging.debug('Checked whether AWS secret exists, result:' + str((existing_secret_arn is not None)))

    return existing_secret_arn


def get_user_secret_from_aws(aws_secret_name: str,
                             aws_region_name: str = None, aws_profile_name: str = None) -> SnowflakeUserSecret:
    """
    Read an existing user secret from AWS Secrets Manager.

    Parameters
    ----------
    aws_secret_name : str
        The name of the secret in AWS Secrets Manager.
    aws_region_name : str
        The name of the AWS region where the secret is located, e.g. eu-west-2.
        If the CI/CD process is running inside AWS (e.g. in AWS CodeBuild) then this can be left blank.
    aws_profile_name : str
        The name of a profile in the AWS credentials file that specifies the credentials to be used when connecting
        to AWS.  If the CI/CD process is running inside AWS (e.g. in AWS CodeBuild) then this can be left blank.

    Returns
    -------
    SnowflakeUserSecret
        The Snowflake user credentials read from the secret in AWS Secrets Manager.
    """
    logging.info('Getting snowflake credentials...')

    # lookup whether secret already exists

    client = aws_utilities.get_aws_client('secretsmanager', aws_region_name, aws_profile_name)
    existing_secret_arn = get_user_secret_arn_from_aws(client, aws_secret_name)

    if existing_secret_arn is None or len(existing_secret_arn) == 0:
        raise ValueError('Unable to find secret with name ' + aws_secret_name)

    logging.debug('Secret exists.')

    # Read secret

    logging.debug('Reading secret...')

    response = client.get_secret_value(SecretId=existing_secret_arn)
    secret_json = response['SecretString']
    user_secret = SnowflakeUserSecret(aws_secret_name=aws_secret_name, secret_json=secret_json)

    if user_secret.user_name is None:
        raise ValueError('Error reading secret ' + aws_secret_name + ': \'user-name\' missing from secret.')
    if user_secret.private_key is None:
        raise ValueError('Error reading secret ' + aws_secret_name + ': \'private-key\' missing from secret.')

    logging.info('Got Snowflake credentials.')

    return user_secret

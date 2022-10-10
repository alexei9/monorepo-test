

def get_user_secret_from_aws(aws_secret_name: str,
                             aws_region_name: str = None, aws_profile_name: str = None):



    client = session.client(aws_service_name)

    return client

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

    # lookup whether secret already exists

    client = aws_utilities.get_aws_client('secretsmanager', aws_region_name, aws_profile_name)


    response = client.get_secret_value(SecretId=existing_secret_arn)
    secret_json = response['SecretString']
    user_secret = SnowflakeUserSecret(aws_secret_name=aws_secret_name, secret_json=secret_json)

    if user_secret.user_name is None:
        raise ValueError('Error reading secret ' + aws_secret_name + ': \'user-name\' missing from secret.')
    if user_secret.private_key is None:
        raise ValueError('Error reading secret ' + aws_secret_name + ': \'private-key\' missing from secret.')

    logging.info('Got Snowflake credentials.')

    return user_secret

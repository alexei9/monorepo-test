import boto3
import logging


def check_aws_credentials(aws_region_name: str, aws_profile_name: str):
    """
    A simple function to validate AWS connectivity and AWS credentials.  An exception is raised if it isn't possible
    to successfully connect to AWS and authenticate with AWS.

    Parameters
    ----------
        aws_region_name : str
            The name of the AWS region being deployed to, e.g. eu-west-2.
            If the CI/CD process is running inside AWS (e.g. in AWS CodeBuild) then this can be left blank.
        aws_profile_name : str
            The name of a profile in the AWS credentials file that specifies the credentials to be used when connecting
            to AWS.  If the CI/CD process is running inside AWS (e.g. in AWS CodeBuild) then this can be left blank.

    Returns
    -------
    None
    """
    logging.debug('Checking AWS credentials...')
    client = get_aws_client('sts', aws_region_name, aws_profile_name)
    try:
        identity = client.get_caller_identity()
        logging.debug("AWS Credentials are valid.")
        for key, value in identity.items():
            if key in ['UserId', 'Account', 'Arn']:
                logging.debug(f"    {key}: {value}")
    except Exception:
        logging.error("Unable to connect to AWS - most likely AWS Credentials are invalid.")
        raise RuntimeError('Unable to connect to AWS.  Please check the AWS credentials/profile.')


def get_aws_client(aws_service_name: str, aws_region_name: str = None, aws_profile_name: str = None):
    """
    Get a boto3 client for interacting with an AWS service.

    Parameters
    ----------
    aws_service_name: str
        The name of the AWS service to get a client for, e.g. secretsmanager.
    aws_region_name : str
        The name of the AWS region to connect to, e.g. eu-west-2.
        If the CI/CD process is running inside AWS (e.g. in AWS CodeBuild) then this can be left blank.
    aws_profile_name : str
        The name of a profile in the AWS credentials file that specifies the credentials to be used when connecting
        to AWS.  If the CI/CD process is running inside AWS (e.g. in AWS CodeBuild) then this can be left blank.

    Returns
    -------
    client
        A boto3 client object that can be used to make API requests to the specified AWS service.
    """
    logging.debug('Creating boto3 session...')
    if aws_profile_name is None:
        session = boto3.Session()
    else:
        session = boto3.Session(region_name=aws_region_name, profile_name=aws_profile_name)
    logging.debug(f'Creating client for {aws_service_name} service...')
    client = session.client(aws_service_name)
    logging.debug('Client created.')
    return client

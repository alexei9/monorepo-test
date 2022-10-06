import snowflake_builder.classes.snowflake_connector as snowflake_connector
import logging


def test_login(snowflake_account_name: str, aws_secret_name: str,
               aws_region_name: str = None, aws_profile_name: str = None):
    """
    Test connecting to Snowflake using the credentials stored in a secret in AWS Secrets Manager.

    Parameters
    ----------
    snowflake_account_name : str
        The name of the Snowflake account to connect to.  This is usually the prefix in Snowflake URLs.
    aws_secret_name : str
        The name of the secret in AWS Secrets Manager containing the user secret of the Snowflake user to test.
    aws_region_name : str
        The name of the AWS region where the secret exists, e.g. eu-west-2.
    aws_profile_name : str
        The name of a profile in the AWS credentials file that specifies the credentials to be used when connecting
        to AWS.

    Returns
    -------
    None
    """
    logging.info(f'Testing login credentials from secret {aws_secret_name}...')

    # get snowflake connector

    connector = snowflake_connector.get_snowflake_connector(
        snowflake_account_name=snowflake_account_name,
        aws_secret_name=aws_secret_name,
        aws_region_name=aws_region_name,
        aws_profile_name=aws_profile_name
    )

    # run connection test

    logging.debug('Connecting to Snowflake...')
    con = connector.connect()
    logging.debug('Reading Snowflake version...')
    cursor = con.cursor()
    cursor.execute("SELECT CURRENT_VERSION()")
    value = cursor.fetchone()[0]
    logging.debug('Snowflake version: ' + value)

    con.close()

    # finished
    logging.info(f'Successfully tested login credentials from secret {aws_secret_name}.')

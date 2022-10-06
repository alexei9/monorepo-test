import logging
from datetime import datetime
import snowflake_builder.classes.snowflake_connector as snowflake_connector
import snowflake_builder.classes.snowflake_user_secret as snowflake_user_secret
import snowflake_builder.utilities.generate_keys as generate_keys
import snowflake_builder.utilities.string_utilities as string_utilities


def create_snowflake_cicd_user(connector: snowflake_connector.SnowflakeConnector,
                               environment: str, public_key: str):
    """
    Create a user for running CI/CD processes in Snowflake and associated the specified RSA public key with the user.

    Parameters
    ----------
    connector : SnowflakeConnector
        An object that represents Snowflake connection parameters and can be used to open a connection to Snowflake.
    environment : str
        The name of the environment being deployed to, e.g. sbox, dev, test, int, stg, prod.
    public_key : str
        The text representation of the RSA public key to be associated with the user in Snowflake.

    Returns
    -------
    None
    """
    logging.info('Creating Snowflake CICD user...')

    # connect to Snowflake

    logging.debug('Connecting to Snowflake...')
    con = connector.connect()

    # test connecting to snowflake

    logging.debug('Reading Snowflake version...')
    cursor = con.cursor()
    cursor.execute("SELECT CURRENT_VERSION()")
    value = cursor.fetchone()[0]
    logging.debug('Snowflake version: ' + value)

    # create user in snowflake

    logging.debug('Creating user in Snowflake...')

    if environment.upper() in ['SBOX', 'DEV']:
        account_admin_role_name = f'ADMIN - {environment.upper()} - DEVELOPER'
    else:
        account_admin_role_name = f'ADMIN - {environment.upper()} - SUPPORT'

    tag_values = {
        'ENV': environment.upper(),
        'PUBLIC_KEY': public_key,
        'ADMIN_ROLE': account_admin_role_name
    }

    sql = """
    BEGIN
        USE ROLE ACCOUNTADMIN;
        CREATE USER SVC_{ENV}_SNOWFLAKE_CICD
            LOGIN_NAME = 'SVC_{ENV}_SNOWFLAKE_CICD',
            DISPLAY_NAME = 'SVC_{ENV}_SNOWFLAKE_CICD',
            STATEMENT_QUEUED_TIMEOUT_IN_SECONDS = 3600,
            STATEMENT_TIMEOUT_IN_SECONDS = 3600,
            RSA_PUBLIC_KEY='{PUBLIC_KEY}';
        GRANT OWNERSHIP ON USER SVC_{ENV}_SNOWFLAKE_CICD TO ROLE {ENV}SECURITYADMIN;
        GRANT ROLE "{ADMIN_ROLE}" TO USER SVC_{ENV}_SNOWFLAKE_CICD;
        GRANT ROLE {ENV}ADMIN TO USER SVC_{ENV}_SNOWFLAKE_CICD;
        GRANT ROLE ACCOUNT_OBJECT_CREATOR TO USER SVC_{ENV}_SNOWFLAKE_CICD;
    END;
    """

    sql_cmd = string_utilities.replace_tags(sql, tag_values)
    con.cursor().execute(sql_cmd)

    con.close()

    logging.info('Created Snowflake CICD user.')


def create_ci_cd_user_and_secret(connector: snowflake_connector.SnowflakeConnector,
                                 environment: str, aws_region_name: str, aws_profile_name: str):
    """
    Create a Snowflake user for running CI/CD processes for all solutions in the specified environment and store the
    credentials for the user in a secret in AWS Secrets Manager.

    Parameters
    ----------
    connector : SnowflakeConnector
        An object that represents Snowflake connection parameters and can be used to open a connection to Snowflake.
    environment : str
        The name of the environment being deployed to, e.g. sbox, dev, test, int, stg, prod.
    aws_region_name : str
        The name of the AWS region where the secret will be created, e.g. eu-west-2.
    aws_profile_name : str
        The name of a profile in the AWS credentials file that specifies the credentials to be used when connecting
        to AWS.

    Returns
    -------
    None
    """
    allowed_auth_types = [
        snowflake_connector.SnowflakeAuthTypes.SINGLE_SIGN_ON,
        snowflake_connector.SnowflakeAuthTypes.USERNAME_PASSWORD
    ]
    if connector.auth_type not in allowed_auth_types:
        raise ValueError('Only SSO and username/password authentication methods can be used when creating ' +
                         'the CI/CD secret.')

    logging.info(f'Creating CICD secret for environment {environment}...')

    # check environment

    valid_environments = ['SBOX', 'DEV', 'TEST', 'INT', 'STG', 'PROD']
    if environment.upper() not in valid_environments:
        raise ValueError('Environment must be one of: ' + ', '.join(valid_environments))

    # create keys

    logging.debug('Creating keys...')
    private_key, public_key = generate_keys.generate_rsa_key_pair()
    private_key = string_utilities.strip_first_and_last_lines(private_key)
    private_key = string_utilities.convert_to_single_line(private_key)
    public_key = string_utilities.strip_first_and_last_lines(public_key)
    public_key = string_utilities.convert_to_single_line(public_key)

    # create snowflake user

    create_snowflake_cicd_user(connector, environment, public_key)

    # write secret to AWS Secrets Manager

    secret_name = 'cruk-bi-{ENV}-snowflake-cicd'.replace('{ENV}', environment.lower())
    user_name = 'SVC_{ENV}_SNOWFLAKE_CICD'.replace('{ENV}', environment.upper())
    user_secret = snowflake_user_secret.SnowflakeUserSecret(
        aws_secret_name=secret_name,
        user_name=user_name,
        private_key=private_key,
        public_key=public_key,
        active_key=1,
        created_utc=datetime.utcnow(),
        last_updated_utc=datetime.utcnow()
    )
    user_secret.set_user_secret_to_aws(
        aws_secret_desc='Snowflake CI/CD process credentials.',
        aws_region_name=aws_region_name,
        aws_profile_name=aws_profile_name,
    )

    # finished

    logging.info(f'Created CICD secret for environment {environment}.')

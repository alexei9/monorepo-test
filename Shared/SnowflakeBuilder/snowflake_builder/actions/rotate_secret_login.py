import logging
import snowflake_builder.classes.snowflake_connector as snowflake_connector
import snowflake_builder.classes.snowflake_user_secret as snowflake_user_secret
import snowflake_builder.utilities.generate_keys as generate_keys
import snowflake_builder.utilities.string_utilities as string_utilities


def update_snowflake_user(connector: snowflake_connector.SnowflakeConnector,
                          update_user_name: str, public_key: str | None, set_key: int):
    """
    Update the RSA public key associated with a user in Snowflake.

    Parameters
    ----------
    connector : SnowflakeConnector
        An object that represents Snowflake connection parameters and can be used to open a connection to Snowflake.
    update_user_name : str
        The username of the user in Snowflake to be updated.
    public_key : str
        The text representation of the new RSA public key to be associated with the user in Snowflake.
    set_key : int
        1 or 2 indicating which public key to update on the user in Snowflake.

    Returns
    -------
    None
    """
    # connect to Snowflake

    logging.debug('Connecting to Snowflake...')
    con = connector.connect()

    # test connecting to snowflake

    logging.debug('Reading Snowflake version...')
    cursor = con.cursor()
    cursor.execute("SELECT CURRENT_VERSION()")
    value = cursor.fetchone()[0]
    logging.debug('Snowflake version: ' + value)

    # update user in snowflake

    logging.debug('Updating user in Snowflake...')

    tag_values = {
        'USERNAME': update_user_name,
        'KEY_SUFFIX': '_2' if set_key == 2 else '',
        'PUBLIC_KEY': ("'" + public_key + "'") if public_key is not None else 'NULL'
    }

    sql_cmd = "ALTER USER {USERNAME} SET RSA_PUBLIC_KEY{KEY_SUFFIX}={PUBLIC_KEY};"
    sql_cmd = string_utilities.replace_tags(sql_cmd, tag_values)
    con.cursor().execute(sql_cmd)
    con.close()

    logging.info('Updated Snowflake user.')


def rotate_secret(connector: snowflake_connector.SnowflakeConnector,
                  aws_secret_name: str, aws_region_name: str, aws_profile_name: str):
    """
    Rotate the RSA keys associated with a user in Snowflake and update the corresponding user-secret in AWS Secrets
    Manager.

    Parameters
    ----------
    connector : SnowflakeConnector
        An object that represents Snowflake connection parameters and can be used to open a connection to Snowflake.
    aws_secret_name : str
        The name of the secret in AWS Secrets Manager containing the user secret of the Snowflake user to update.
    aws_region_name : str
        The name of the AWS region where the secret exists, e.g. eu-west-2.
    aws_profile_name : str
        The name of a profile in the AWS credentials file that specifies the credentials to be used when connecting
        to AWS.

    Returns
    -------
    None
    """
    logging.info(f'Rotating RSA keys in AWS secret {aws_secret_name}...')

    # retrieve existing secret

    logging.debug(f'Reading existing user secret {aws_secret_name}...')
    user_secret = snowflake_user_secret.get_user_secret_from_aws(
        aws_secret_name=aws_secret_name,
        aws_region_name=aws_region_name,
        aws_profile_name=aws_profile_name
    )

    # create new keys

    logging.debug('Creating keys...')
    private_key, public_key = generate_keys.generate_rsa_key_pair()
    private_key = string_utilities.strip_first_and_last_lines(private_key)
    private_key = string_utilities.convert_to_single_line(private_key)
    public_key = string_utilities.strip_first_and_last_lines(public_key)
    public_key = string_utilities.convert_to_single_line(public_key)

    # update snowflake user

    logging.debug('Setting new RSA key on user in Snowflake...')
    current_key_number = user_secret.key_number
    set_key = 1 if current_key_number == 2 else 2
    update_snowflake_user(
        connector=connector,
        update_user_name=user_secret.user_name,
        public_key=public_key,
        set_key=set_key
    )

    # update secret in AWS Secrets Manager

    logging.debug(f'Writing updated user secret {aws_secret_name}...')
    user_secret.private_key = private_key
    user_secret.public_key = public_key
    user_secret.key_number = set_key
    user_secret.set_user_secret_to_aws(aws_region_name=aws_region_name, aws_profile_name=aws_profile_name)

    # update snowflake user to remove the other key

    logging.debug('Clearing old RSA key from user in Snowflake...')
    update_snowflake_user(
        connector=connector,
        update_user_name=user_secret.user_name,
        public_key=None,
        set_key=current_key_number
    )

    # finished

    logging.info(f'Rotated RSA keys in AWS secret {aws_secret_name}...')

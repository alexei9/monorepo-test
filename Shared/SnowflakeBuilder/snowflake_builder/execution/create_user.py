import json
import logging
import sys
import snowflake_builder.classes.snowflake_user_secret as snowflake_user_secret
import snowflake_builder.execution.history as history
import snowflake_builder.utilities.app_logging as app_logging
import snowflake_builder.utilities.generate_keys as generate_keys
import snowflake_builder.utilities.snowflake_utilities as snowflake_utilities
import snowflake_builder.utilities.string_utilities as string_utilities
from datetime import datetime
from snowflake_builder.classes.snowflake_cicd_config import FileProcessModes, SnowflakeCICDConfig
from snowflake_builder.classes.snowflake_cicd_tracker import SnowflakeCICDTracker


def execute_create_user(config: SnowflakeCICDConfig, script_contents: str, script_checksum: str,
                        directory_name: str, script_name: str, process_mode: FileProcessModes,
                        cicd_secret_name: str, cicd_user_name: str, tracker: SnowflakeCICDTracker):
    """
    Execute a CI/CD script that creates a user in Snowflake and writes the user credentials as a user-secret into
    AWS Secrets Manager.

    Parameters
    ----------
    config : SnowflakeCICDConfig
        A configuration object containing information about how CI/CD scripts are to be executed.
    script_contents : str
        The contents of the CI/CD script to be executed.
    script_checksum : str
        An MD5 checksum of the script contents - used to check whether the script has been modified since the last
        execution of the script.
    directory_name : str
        The name of the directory containing the CI/CD script to be executed.
    script_name : str
        The name of the file containing the CI/CD script to be executed.
    process_mode : FileProcessModes
        The mode the script should be executed in, e.g. once-only, whenever the script is changed, always, etc.
    cicd_secret_name : str
        The name of the secret in AWS Secrets Manager where the credentials for the newly created user will be stored.
    cicd_user_name : str
        The name of the user to be created in Snowflake.
    tracker : SnowflakeCICDTracker
        A tracker object that records the execution results for each CI/CD script.

    Returns
    -------
    None
    """
    start_dt = datetime.utcnow()

    # create keys

    logging.debug('Creating keys...')
    private_key, public_key = generate_keys.generate_rsa_key_pair()
    private_key = string_utilities.strip_first_and_last_lines(private_key)
    private_key = string_utilities.convert_to_single_line(private_key)
    public_key = string_utilities.strip_first_and_last_lines(public_key)
    public_key = string_utilities.convert_to_single_line(public_key)

    # replace placeholder in the script

    script_contents = script_contents.replace('{USER_PUBLIC_KEY}', public_key)

    # create the user in Snowflake

    logging.debug(f'Executing create user script \'{script_name}\'...')
    if process_mode == FileProcessModes.PREPARATION:  # sql is not logged into DB for PREPARATION mode, so log here
        logging.debug('SQL:\n' + script_contents)
    try:
        create_result = snowflake_utilities.execute_sql_scalar(
            connector=config.connector,
            sql=script_contents,
            role_name=config.variable_dict['ENV'] + 'ADMIN',
            warehouse_name=config.variable_dict['WAREHOUSE_NAME']
        )
    except Exception:
        tracker.append_execution(directory_name, script_name, start_dt, datetime.utcnow(), False)
        logging.error('Execution of create user script failed.', exc_info=sys.exc_info())
        error_details = json.dumps(app_logging.format_exception(sys.exc_info()))
        if process_mode != FileProcessModes.PREPARATION:
            history.insert_change_history_row(
                config=config,
                directory_name=directory_name,
                script_name=script_name,
                script_contents=script_contents,
                script_checksum=script_checksum,
                success=False,
                start_time=start_dt,
                end_time=datetime.utcnow(),
                error_details=error_details
            )
        raise  # rethrow error to end process

    # write the secret to AWS?

    if create_result == 1:
        user_secret = snowflake_user_secret.SnowflakeUserSecret(
            aws_secret_name=cicd_secret_name,
            user_name=cicd_user_name,
            private_key=private_key,
            public_key=public_key,
            active_key=1,
            created_utc=datetime.utcnow(),
            last_updated_utc=datetime.utcnow()
        )
        user_secret.set_user_secret_to_aws(
            aws_secret_desc="Snowflake service account credentials.",
            aws_region_name=config.aws_region_name,
            aws_profile_name=config.aws_profile_name,
        )

    # log result

    tracker.append_execution(directory_name, script_name, start_dt, datetime.utcnow(), True)
    if process_mode != FileProcessModes.PREPARATION:
        history.insert_change_history_row(
            config=config,
            directory_name=directory_name,
            script_name=script_name,
            script_contents=script_contents,
            script_checksum=script_checksum,
            success=True,
            start_time=start_dt,
            end_time=datetime.utcnow(),
            error_details=None
        )

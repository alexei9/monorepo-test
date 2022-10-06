import hashlib
import logging
import os
import snowflake_builder.utilities.snowflake_utilities as snowflake_utilities
import snowflake_builder.execution.history as history
import snowflake_builder.execution.script_execution as script_execution
from datetime import datetime
from snowflake_builder.classes.snowflake_cicd_config import FileProcessModes, SnowflakeCICDConfig
from snowflake_builder.classes.snowflake_cicd_tracker import SnowflakeCICDTracker


def prepare_solution(config: SnowflakeCICDConfig, directory_name: str, tracker: SnowflakeCICDTracker):
    """
    Run the CI/CD preparation process for a specific solution - i.e. run the scripts in the Preparation directory.
    Typically, this process creates the solution roles, storage integration, database, schemas, etc.
    It also creates the DEV_OPS.CHANGE_HISTORY table used to control and audit CI/CD script execution.

    Parameters
    ----------
    config : SnowflakeCICDConfig
        A configuration object containing information about how CI/CD scripts are to be executed.
    directory_name : str
        The name of the directory containing the CI/CD script to be executed.
    tracker : SnowflakeCICDTracker
        A tracker object that records the execution results for each CI/CD script.

    Returns
    -------
    None
    """
    logging.info('Starting preparation process...')

    # check if the database currently exists

    logging.debug(f'Checking if database {config.implementation_database_name} exists...')

    sql = """
    SELECT COUNT(*) FROM SNOWFLAKE.INFORMATION_SCHEMA.DATABASES
    WHERE DATABASE_NAME = %(db_name)s;
    """
    parameters = {'db_name': config.implementation_database_name}

    existing_db_count = snowflake_utilities.execute_sql_scalar(
        connector=config.connector,
        sql=sql,
        parameters=parameters,
        role_name=config.variable_dict['ENV'] + 'ADMIN',
        warehouse_name=config.variable_dict['WAREHOUSE_NAME']
    )
    existing_db_count = int(existing_db_count)  # noqa

    if existing_db_count > 0:
        logging.debug(f'Database {config.implementation_database_name} exists.')
    else:
        logging.debug(f'Database {config.implementation_database_name} does not exist.')

    # if database exists, check if the DEV_OPS.CHANGE_HISTORY table exists

    existing_table_count = 0
    if existing_db_count > 0:
        logging.debug('Checking if table DEV_OPS.CHANGE_HISTORY exists...')

        sql = f"""
        SELECT COUNT(*) FROM {config.implementation_database_name}.INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = 'DEV_OPS' AND TABLE_NAME = 'CHANGE_HISTORY';
        """
        existing_table_count = snowflake_utilities.execute_sql_scalar(
            connector=config.connector,
            sql=sql,
            role_name=config.variable_dict['ENV'] + 'ADMIN',
            warehouse_name=config.variable_dict['WAREHOUSE_NAME']
        )
        existing_table_count = int(existing_table_count)  # noqa

        if existing_table_count > 0:
            logging.debug('Table DEV_OPS.CHANGE_HISTORY exists.')
        else:
            logging.debug('Table DEV_OPS.CHANGE_HISTORY does not exist.')

    # if database and table present, then no need to run the preparation scripts

    if existing_db_count > 0 and existing_table_count > 0:
        logging.info('No need to run preparation process for solution as database and table already exist.')
        return

    # run preparation process

    logging.debug('Running preparation process...')
    start_dt = datetime.utcnow()
    execute_directory(config, directory_name, FileProcessModes.PREPARATION, tracker)

    # special case of preparation directory

    logging.debug('Inserting change history row for preparation process...')
    history.insert_change_history_row(
        config=config,
        directory_name=directory_name,
        script_name='(preparation scripts)',
        script_contents='-',
        script_checksum='-',
        success=True,
        start_time=start_dt,
        end_time=datetime.utcnow(),
        error_details=None
    )

    logging.info('Finished.')


def should_process_file(config: SnowflakeCICDConfig,
                        directory_name: str, script_name: str, process_mode: FileProcessModes) -> bool:
    """
    Based on the specified process_mode, contents of the DEV_OPS.CHANGE_HISTORY database table and the MD5 hash
    of the current CI/CD script, determine whether the current CI/CD script should be executed.

    Parameters
    ----------
    config : SnowflakeCICDConfig
        A configuration object containing information about how CI/CD scripts are to be executed.
    directory_name : str
        The name of the directory containing the CI/CD script to be executed.
    script_name : str
        The name of the file containing the CI/CD script to be executed.
    process_mode : FileProcessModes
        The mode the script should be executed in, e.g. once-only, whenever the script is changed, always, etc.

    Returns
    -------
    bool
        True if the current CI/CD script should be executed, False otherwise.
    """
    logging.debug(f'Determining whether file \'{directory_name}\\{script_name}\' should be processed in ' +
                  f'process mode {process_mode.name}...')

    full_file_path = os.path.join(config.definitions_root_path, directory_name, script_name)
    if not os.path.isfile(full_file_path):
        raise ValueError('File not found: ' + full_file_path)

    file_path_with_no_extension, file_extension = os.path.splitext(full_file_path)
    if file_extension.lower() != ".sql":
        logging.debug(f'Ignoring file \'{script_name}\' because it is not a SQL script.')
        return False

    script_checksum = None
    if process_mode == FileProcessModes.WHEN_CHANGED:
        with open(full_file_path, mode='r', encoding='utf-8') as f:
            script_contents = f.read()
        script_checksum = hashlib.md5(script_contents.encode('utf-8')).hexdigest()

    success_exec_count = history.get_successful_execution_count(config, directory_name, script_name, script_checksum)

    return success_exec_count == 0


def execute_directory(config: SnowflakeCICDConfig, directory_name: str, process_mode: FileProcessModes,
                      tracker: SnowflakeCICDTracker):
    """
    Execute the CI/CD scripts in the specified directory in sequence.

    Parameters
    ----------
    config : SnowflakeCICDConfig
        A configuration object containing information about how CI/CD scripts are to be executed.
    directory_name : str
        The name of the directory containing the CI/CD script to be executed.
    process_mode : FileProcessModes
        The mode the script should be executed in, e.g. once-only, whenever the script is changed, always, etc.
    tracker : SnowflakeCICDTracker
        A tracker object that records the execution results for each CI/CD script.

    Returns
    -------
    None
    """
    logging.info(f'Processing directory \'{directory_name}\' in process mode {process_mode.name}...')

    # check the directory exists

    directory_path = os.path.join(config.definitions_root_path, directory_name)
    if not os.path.isdir(directory_path):
        logging.warning('Skipping processing directory ' + directory_name +
                        ' because no directory exists at path: ' + directory_path)
        return

    # process files in the directory

    script_names = os.listdir(directory_path)
    for script_name in script_names:

        if process_mode in [FileProcessModes.PREPARATION, FileProcessModes.ALWAYS]:
            process_file = True
        elif process_mode in [FileProcessModes.ONCE_ONLY, FileProcessModes.WHEN_CHANGED]:
            process_file = should_process_file(config, directory_name, script_name, process_mode)
        else:
            raise ValueError('Unknown file process mode: ' + process_mode.name)

        if process_file:
            logging.debug(f'Executing script \'{script_name}\'.')
        else:
            logging.debug(f'Skipping execution of script \'{script_name}\'.')
            continue

        script_execution.execute_file(config, directory_name, script_name, process_mode, tracker)

    logging.info(f'Finished processing directory \'{directory_name}\' in process mode {process_mode.name}.')


def execute_scripts(snowflake_account_name: str, definitions_root_path: str, environment: str,
                    aws_region_name: str = None, aws_profile_name: str = None, force_enabled: bool = False):
    """
    Execute the CI/CD scripts contained in the directories that are specified in the config.json configuration file.

    Parameters
    ----------
    snowflake_account_name : str
        The name of the Snowflake account to connect to.  This is usually the prefix in Snowflake URLs.
    definitions_root_path : str
        The path to the database containing a set of Snowflake CI/CD scripts and the config.json file.
    environment : str
        The name of the environment being deployed to, e.g. sbox, dev, test, int, stg, prod.
    aws_region_name : str
        The name of the AWS region being deployed to, e.g. eu-west-2.
        If the CI/CD process is running inside AWS (e.g. in AWS CodeBuild) then this can be left blank.
    aws_profile_name : str
        The name of a profile in the AWS credentials file that specifies the credentials to be used when connecting
        to AWS.  If the CI/CD process is running inside AWS (e.g. in AWS CodeBuild) then this can be left blank.
    force_enabled : bool
        A switch to force the CI/CD process to run, overriding the cicd-enabled settings in the config.json file.

    Returns
    -------
    None
    """
    logging.info('Processing scripts...')

    # check environment

    valid_environments = ['SBOX', 'DEV', 'TEST', 'INT', 'STG', 'PROD']
    if environment.upper() not in valid_environments:
        raise ValueError('Environment must be one of: ' + ', '.join(valid_environments))

    # create configuration object

    config = SnowflakeCICDConfig(
        environment=environment,
        snowflake_account_name=snowflake_account_name,
        definitions_root_path=definitions_root_path,
        aws_region_name=aws_region_name,
        aws_profile_name=aws_profile_name,
        force_enabled=force_enabled
    )

    # disabled?

    if not config.cicd_enabled:
        logging.warning('CICD is set to disabled in the config.ini file.')
        logging.info('Finished without processing scripts.')
        return

    # tracker to record script results for a simple summary

    tracker = SnowflakeCICDTracker()

    # process directories specified in config file

    try:
        for dir_exec in config.definitions_dict['directory-execution']:
            directory = dir_exec['directory']
            exec_type = dir_exec['execution-type']
            if exec_type == FileProcessModes.PREPARATION:
                prepare_solution(config, directory, tracker)
            else:
                execute_directory(config, directory, exec_type, tracker)
        tracker.output_summary()
    except Exception:
        tracker.output_summary()
        raise

    logging.info('Finished processing scripts.')

import json
import logging
import os
import snowflake_builder.utilities.snowflake_utilities as snowflake_utilities
from datetime import datetime
from snowflake_builder.classes.snowflake_cicd_config import SnowflakeCICDConfig


def insert_change_history_row(config: SnowflakeCICDConfig,
                              directory_name: str, script_name: str, script_contents: str, script_checksum: str,
                              success: bool, start_time: datetime, end_time: datetime, error_details: str | None):
    """
    Insert a row in the DEV_OPS.CHANGE_HISTORY table to record the results of executing a CI/CD script.

    Parameters
    ----------
    config : SnowflakeCICDConfig
        A configuration object containing information about how CI/CD scripts are to be executed.
    directory_name : str
        The name of the directory containing the CI/CD script to be executed.
    script_name : str
        The name of the file containing the CI/CD script to be executed.
    script_contents : str
        The contents of the CI/CD script to be executed.
    script_checksum : str
        An MD5 checksum of the script contents - used to check whether the script has been modified since the last
        execution of the script.
    success : bool
        True if the CI/CD script executed successfully.
    start_time : datetime
        The UTC time that the CI/CD script started executing.
    end_time : datetime
        The UTC time that the CI/CD script finished executing.
    error_details : str
        If the script failed, details of the error that occurred.

    Returns
    -------
    None
    """
    logging.debug('Inserting change history row...')
    sql = """
    INSERT INTO DEV_OPS.CHANGE_HISTORY (CHANGE_ID, SCRIPT_DIRECTORY, SCRIPT_TYPE, SCRIPT_NAME, SCRIPT_CHECKSUM,
        EXEC_VAR_VALUES, EXEC_SQL, EXEC_SUCCESS, EXEC_START_TIME_UTC, EXEC_END_TIME_UTC, EXEC_ERROR)
    VALUES(DEV_OPS.NEXT_CHANGE_ID.nextval, %(directory)s, %(type)s, %(script)s, %(checksum)s,
        %(var_vals)s, %(sql)s, %(success)s, %(started)s, %(ended)s, %(error)s)
    """
    parameters = {
        'directory': directory_name,
        'type': script_name,
        'script': script_name,
        'checksum': script_checksum,
        'var_vals': json.dumps(config.variable_dict),
        'sql': script_contents,
        'success': success,
        'started': start_time,
        'ended': end_time,
        'error': error_details
    }
    snowflake_utilities.execute_sql_command(
        connector=config.connector,
        sql=sql,
        parameters=parameters,
        role_name=config.variable_dict['ENV'] + 'ADMIN',
        database_name=config.implementation_database_name,
        warehouse_name=config.variable_dict['WAREHOUSE_NAME']
    )
    logging.debug('Inserted change history row.')


def get_successful_execution_count(config: SnowflakeCICDConfig,
                                   directory_name: str, script_name: str, script_checksum: str | None) -> int:
    """
    Based on the contents of the DEV_OPS.CHANGE_HISTORY database table, count the number of times that the
    specified script has been successfully executed.

    Parameters
    ----------
    config : SnowflakeCICDConfig
        A configuration object containing information about how CI/CD scripts are to be executed.
    directory_name : str
        The name of the directory containing the CI/CD script to be executed.
    script_name : str
        The name of the file containing the CI/CD script to be executed.
    script_checksum : str | None
        The MD5 hash of the script contents.

    Returns
    -------
    int
        The number of times that the script has been successfully executed previously.
    """
    logging.debug(f'Counting the number of times that script \'{directory_name}\\{script_name}\'' +
                  (f' with MD5 hash {script_checksum}' if script_checksum is not None else '') +
                  ' has been previously executed...')

    full_file_path = os.path.join(config.definitions_root_path, directory_name, script_name)
    if not os.path.isfile(full_file_path):
        raise ValueError('File not found: ' + full_file_path)

    file_path_with_no_extension, file_extension = os.path.splitext(full_file_path)
    if file_extension.lower() != ".sql":
        logging.debug(f'Ignoring file \'{script_name}\' because it is not a SQL script.')
        return False

    if script_checksum is None:
        sql = """
        SELECT COUNT(*) FROM DEV_OPS.CHANGE_HISTORY
        WHERE SCRIPT_DIRECTORY = %(directory_name)s AND SCRIPT_NAME = %(script_name)s AND EXEC_SUCCESS = 1;
        """
        parameters = {
            'directory_name': directory_name,
            'script_name': script_name
        }
    else:
        sql = """
        WITH MOST_RECENT_CHANGE AS
        (
            SELECT TOP 1 SCRIPT_CHECKSUM
            FROM DEV_OPS.CHANGE_HISTORY
            WHERE SCRIPT_DIRECTORY = %(directory_name)s AND SCRIPT_NAME = %(script_name)s AND EXEC_SUCCESS = 1
            ORDER BY CHANGE_ID DESC
        )
        SELECT COUNT(*)
        FROM MOST_RECENT_CHANGE
        WHERE SCRIPT_CHECKSUM = %(checksum)s;
        """
        parameters = {
            'directory_name': directory_name,
            'script_name': script_name,
            'checksum': script_checksum
        }

    success_exec_count = snowflake_utilities.execute_sql_scalar(
        connector=config.connector,
        sql=sql,
        parameters=parameters,
        role_name=config.variable_dict['ENV'] + 'ADMIN',
        warehouse_name=config.variable_dict['WAREHOUSE_NAME'],
        database_name=config.implementation_database_name
    )

    return int(success_exec_count)  # noqa

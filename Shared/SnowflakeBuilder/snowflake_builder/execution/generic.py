import json
import logging
import sys
import snowflake_builder.execution.history as history
import snowflake_builder.utilities.app_logging as app_logging
import snowflake_builder.utilities.snowflake_utilities as snowflake_utilities
from datetime import datetime
from snowflake_builder.classes.snowflake_cicd_config import FileProcessModes, SnowflakeCICDConfig
from snowflake_builder.classes.snowflake_cicd_tracker import SnowflakeCICDTracker


def execute_generic_script(config: SnowflakeCICDConfig, script_contents: str, script_checksum: str,
                           directory_name: str, script_name: str, process_mode: FileProcessModes,
                           tracker: SnowflakeCICDTracker):
    """
    Execute a CI/CD script that requires no special handling (e.g. requires nothing to updated in AWS).

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
    tracker : SnowflakeCICDTracker
        A tracker object that records the execution results for each CI/CD script.

    Returns
    -------
    None
    """
    start_dt = datetime.utcnow()

    # apply the change to Snowflake

    logging.debug(f'Executing generic script \'{script_name}\'...')
    if process_mode == FileProcessModes.PREPARATION:  # sql is not logged into DB for PREPARATION mode, so log here
        logging.debug('SQL:\n' + script_contents)
    try:
        snowflake_utilities.execute_sql_command(
            connector=config.connector,
            sql=script_contents,
            role_name=config.variable_dict['ENV'] + 'ADMIN',
            warehouse_name=config.variable_dict['WAREHOUSE_NAME']
        )
    except Exception:
        tracker.append_execution(directory_name, script_name, start_dt, datetime.utcnow(), False)
        logging.error('Execution of generic script failed.', exc_info=sys.exc_info())
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

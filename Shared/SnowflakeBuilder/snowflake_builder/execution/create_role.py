import logging
import snowflake_builder.execution.generic as generic
import snowflake_builder.utilities.snowflake_utilities as snowflake_utilities
from snowflake_builder.classes.snowflake_cicd_config import FileProcessModes, SnowflakeCICDConfig
from snowflake_builder.classes.snowflake_cicd_tracker import SnowflakeCICDTracker


def execute_create_role(config: SnowflakeCICDConfig, script_contents: str, script_checksum: str,
                        directory_name: str, script_name: str, process_mode: FileProcessModes,
                        cicd_role_name: str, tracker: SnowflakeCICDTracker):
    """
    Execute a CI/CD script that creates a role in Snowflake.

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
    cicd_role_name : str
        The name of the role to be created in Snowflake.
    tracker : SnowflakeCICDTracker
        A tracker object that records the execution results for each CI/CD script.

    Returns
    -------
    None
    """
    # check whether the role already exists - so can pass the role count to the script

    logging.debug(f'Checking whether role \'{cicd_role_name}\' already exists...')
    sql = f"SHOW ROLES LIKE '{cicd_role_name}';"""
    row_generator = snowflake_utilities.execute_sql_rows(
        connector=config.connector,
        sql=sql,
        role_name=config.variable_dict['ENV'] + 'ADMIN',
        warehouse_name=config.variable_dict['WAREHOUSE_NAME']
    )
    row_count = sum(1 for _ in row_generator)
    if row_count > 0:
        logging.debug(f'Role \'{cicd_role_name}\' already exists.')
        return
    else:
        logging.debug(f'Role \'{cicd_role_name}\' does not exist.')

    # replace placeholder in the script

    script_contents = script_contents.replace('{EXISTING_ROLE_COUNT}', str(row_count))

    # execute the script as a generic script

    generic.execute_generic_script(
        config=config,
        script_contents=script_contents,
        script_checksum=script_checksum,
        directory_name=directory_name,
        script_name=script_name,
        process_mode=process_mode,
        tracker=tracker
    )

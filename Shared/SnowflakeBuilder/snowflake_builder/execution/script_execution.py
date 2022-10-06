import hashlib
import logging
import os
import snowflake_builder.execution.create_integeration as create_integration
import snowflake_builder.execution.create_role as create_role
import snowflake_builder.execution.create_user as create_user
import snowflake_builder.execution.generic as generic
import snowflake_builder.utilities.string_utilities as string_utilities
from snowflake_builder.classes.snowflake_cicd_config import FileProcessModes, SnowflakeCICDConfig
from snowflake_builder.classes.snowflake_cicd_tracker import SnowflakeCICDTracker


def execute_file(config: SnowflakeCICDConfig,
                 directory_name: str, script_name: str, process_mode: FileProcessModes,
                 tracker: SnowflakeCICDTracker):
    """
    Execute a CI/CD script against Snowflake.

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
    tracker : SnowflakeCICDTracker
        A tracker object that records the execution results for each CI/CD script.

    Returns
    -------
    None
    """
    logging.info(f'Processing file \'{directory_name}\\{script_name}\' in process mode {process_mode.name}...')

    # get script contents

    full_file_path = os.path.join(config.definitions_root_path, directory_name, script_name)
    if not os.path.isfile(full_file_path):
        raise ValueError('File not found: ' + full_file_path)

    logging.debug('Computing checksum...')
    with open(full_file_path, mode='r', encoding='utf-8') as f:
        script_contents = f.read()
    script_checksum = hashlib.md5(script_contents.encode('utf-8')).hexdigest()
    logging.debug('Checksum: ' + script_checksum)

    # Parse the script type

    logging.debug('Determining script type...')
    cicd_script_type = 'GENERIC'
    script_lines = script_contents.splitlines()
    for script_line in script_lines:
        if script_line.upper().replace(' ', '').startswith('--CICD-SCRIPT-TYPE:'):
            line_parts = script_line.split(':', 1)
            cicd_script_type = line_parts[1].strip()
    logging.debug('Script type: ' + cicd_script_type)

    # check variables

    logging.debug('Checking CICD variables...')
    script_lines = script_contents.splitlines()
    for script_line in script_lines:
        if script_line.upper().replace(' ', '').startswith('--CICD-VAR:'):
            line_parts = script_line.split(':', 1)
            cicd_variable_name = line_parts[1].strip()
            if cicd_variable_name not in config.variable_dict:
                if cicd_script_type == 'CREATE_USER' and cicd_variable_name == 'USER_PUBLIC_KEY':
                    continue
                if cicd_script_type == 'CREATE_ROLE' and cicd_variable_name == 'EXISTING_ROLE_COUNT':
                    continue
                if cicd_script_type == 'CREATE_INTEGRATION' and cicd_variable_name == 'EXISTING_INTEGRATION_COUNT':
                    continue
                raise ValueError(f'Unknown CICD variable \'{cicd_variable_name}\' in script \'{script_name}\' in ' +
                                 f'directory {directory_name}.')

    # replace variables

    logging.debug('Replacing tags in script with variable values...')
    script_contents = string_utilities.replace_tags(script_contents, config.variable_dict)

    # parse the other CICD settings from the script (done here after the variable replacement above)

    logging.debug('Parsing other CICD settings from script...')
    cicd_secret_name = None
    cicd_user_name = None
    cicd_role_name = None
    cicd_integration_name = None
    script_lines = script_contents.splitlines()
    for script_line in script_lines:
        if script_line.upper().replace(' ', '').startswith('--CICD-SECRET-NAME:'):
            line_parts = script_line.split(':', 1)
            cicd_secret_name = line_parts[1].strip()
            logging.debug('CICD-SECRET-NAME: ' + cicd_secret_name)
        if script_line.upper().replace(' ', '').startswith('--CICD-USER-NAME:'):
            line_parts = script_line.split(':', 1)
            cicd_user_name = line_parts[1].strip()
            logging.debug('CICD-USER-NAME: ' + cicd_user_name)
        if script_line.upper().replace(' ', '').startswith('--CICD-ROLE-NAME:'):
            line_parts = script_line.split(':', 1)
            cicd_role_name = line_parts[1].strip()
            logging.debug('CICD-ROLE-NAME: ' + cicd_role_name)
        if script_line.upper().replace(' ', '').startswith('--CICD-INTEGRATION-NAME:'):
            line_parts = script_line.split(':', 1)
            cicd_integration_name = line_parts[1].strip()
            logging.debug('CICD-INTEGRATION-NAME: ' + cicd_integration_name)

    # check the CICD settings

    logging.debug('Checking CICD settings...')
    allowed_script_types = ['GENERIC', 'CREATE_USER', 'CREATE_ROLE', 'CREATE_INTEGRATION']
    if cicd_script_type not in allowed_script_types:
        raise ValueError(f'Invalid CICD-SCRIPT-TYPE script type specified in script \'{script_name}\' in ' +
                         f'directory {directory_name}.')
    if cicd_script_type == 'CREATE_USER' and len(cicd_secret_name) == 0:
        raise ValueError(f'CICD-SECRET-NAME must be specified in script \'{script_name}\' in ' +
                         f'directory {directory_name}.')
    if cicd_script_type == 'CREATE_USER' and len(cicd_user_name) == 0:
        raise ValueError(f'CICD-USER-NAME must be specified in script \'{script_name}\' in ' +
                         f'directory {directory_name}.')
    if cicd_script_type == 'CREATE_ROLE' and len(cicd_role_name) == 0:
        raise ValueError(f'CICD-ROLE-NAME must be specified in script \'{script_name}\' in ' +
                         f'directory {directory_name}.')
    if cicd_script_type == 'CREATE_INTEGRATION' and len(cicd_integration_name) == 0:
        raise ValueError(f'CICD-INTEGRATION-NAME must be specified in script \'{script_name}\' in ' +
                         f'directory {directory_name}.')

    # execute the script

    logging.debug(f'Executing script \'{script_name}\'...')
    if cicd_script_type == 'CREATE_USER':
        create_user.execute_create_user(
            config=config,
            script_contents=script_contents,
            script_checksum=script_checksum,
            directory_name=directory_name,
            script_name=script_name,
            process_mode=process_mode,
            cicd_secret_name=cicd_secret_name,
            cicd_user_name=cicd_user_name,
            tracker=tracker
        )
    elif cicd_script_type == 'CREATE_ROLE':
        create_role.execute_create_role(
            config=config,
            script_contents=script_contents,
            script_checksum=script_checksum,
            directory_name=directory_name,
            script_name=script_name,
            process_mode=process_mode,
            cicd_role_name=cicd_role_name,
            tracker=tracker
        )
    elif cicd_script_type == 'CREATE_INTEGRATION':
        create_integration.execute_create_integration(
            config=config,
            script_contents=script_contents,
            script_checksum=script_checksum,
            directory_name=directory_name,
            script_name=script_name,
            process_mode=process_mode,
            cicd_integration_name=cicd_integration_name,
            tracker=tracker
        )
    else:
        generic.execute_generic_script(
            config=config,
            script_contents=script_contents,
            script_checksum=script_checksum,
            directory_name=directory_name,
            script_name=script_name,
            process_mode=process_mode,
            tracker=tracker
        )

    logging.info(f'Finished processing file \'{directory_name}\\{script_name}\' in process mode {process_mode.name}.')

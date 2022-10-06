import enum
import json
import logging
import os
import snowflake_builder.classes.snowflake_connector as snowflake_connector


class FileProcessModes(enum.Enum):
    PREPARATION = 0,
    ONCE_ONLY = 1,
    WHEN_CHANGED = 2,
    ALWAYS = 3


class SnowflakeCICDConfig:
    """
    A class that represents the configuration data for one execution of a Snowflake CI/CD pipeline.
    """

    def __init__(self, environment: str, snowflake_account_name: str, definitions_root_path: str,
                 aws_region_name: str = None, aws_profile_name: str = None, force_enabled: bool = False):
        """
        Create a new instance of the configuration needed for one execution of a Snowflake CI/CD pipeline.

        Parameters
        ----------
        environment : str
            The name of the environment being deployed to, e.g. sbox, dev, test, int, stg, prod.
        snowflake_account_name : str
            The name of the Snowflake account being deployed to.  This is usually the prefix in Snowflake URLs.
        definitions_root_path : str
            The path to the database containing a set of Snowflake CI/CD scripts and the config.json file.
        aws_region_name : str
            The name of the AWS region being deployed to, e.g. eu-west-2.
            If the CI/CD process is running inside AWS (e.g. in AWS CodeBuild) then this can be left blank.
        aws_profile_name : str
            The name of a profile in the AWS credentials file that specifies the credentials to be used when connecting
            to AWS.  If the CI/CD process is running inside AWS (e.g. in AWS CodeBuild) then this can be left blank.
        force_enabled : bool
            A switch to force the CI/CD process to run, overriding the cicd-enabled settings in the config.json file.
        """

        logging.debug('Instantiating SnowflakeCICDConfig instance...')

        # basic config

        self.environment = environment
        self.definitions_root_path = definitions_root_path
        self.force_enabled = force_enabled

        # get config dictionary and variable dictionary

        self.definitions_dict = get_config_dict(definitions_root_path, environment)
        self.variable_dict = get_variable_dict(self.definitions_dict, environment)

        # enabled?

        global_enabled = self.definitions_dict['cicd-enabled']
        env_enabled = self.definitions_dict['environments'][environment.lower()]['cicd-enabled']
        self.cicd_enabled = (global_enabled and env_enabled) or self.force_enabled

        # get database names

        self.implementation_database_name = self.variable_dict['IMPLEMENTATION_DB_NAME']
        self.presentation_database_name = self.variable_dict['PRESENTATION_DB_NAME']

        # get snowflake credentials to use when running CI CD

        aws_secret_name = f'cruk-bi-{environment.lower()}-snowflake-cicd'
        self.connector = snowflake_connector.get_snowflake_connector(
            snowflake_account_name=snowflake_account_name,
            aws_secret_name=aws_secret_name,
            aws_region_name=aws_region_name,
            aws_profile_name=aws_profile_name
        )

        # aws login info (mainly for use outside AWS)

        self.aws_region_name = aws_region_name
        self.aws_profile_name = aws_profile_name

        logging.debug('Instantiated SnowflakeCICDConfig instance.')


def get_config_dict(definitions_root_path: str, environment: str) -> dict:
    """
    Read the contents of the config.json file and convert text values to the appropriate enum values where needed.

    Parameters
    ----------
    definitions_root_path : str
        The path to the config.json file to be read.
    environment : str
        The name of the environment being deployed to, e.g. sbox, dev, test, int, stg, prod.

    Returns
    -------
    dict
        A dictionary containing the CI/CD configuration read from the config.json file.
    """
    logging.debug('Check database definitions config.json file exists...')
    config_path = os.path.join(definitions_root_path, 'config.json')
    if not os.path.exists(config_path):
        raise ValueError('No database definitions config.json file can be found at: ' + config_path)

    logging.debug('Check database definitions config.json file contents...')
    with open(config_path) as f:
        definitions_dict = json.load(f)
    if type(definitions_dict) is not dict:
        raise ValueError('File does not contain a dictionary: ' + config_path)
    if 'type' not in definitions_dict:
        raise ValueError('File does not contain database definitions: ' + config_path)
    if definitions_dict['type'] != 'database-builder-config':
        raise ValueError('File does not contain database definitions: ' + config_path)
    if environment.lower() not in definitions_dict['environments']:
        raise ValueError(f'Environment \'{environment.lower()}\' not found in database definitions: ' + config_path)

    logging.debug('Checking/converting file process modes from string values to enum values...')
    lookup_dict = {
        'PREPARATION': FileProcessModes.PREPARATION,
        'ONCE_ONLY': FileProcessModes.ONCE_ONLY,
        'WHEN_CHANGED': FileProcessModes.WHEN_CHANGED,
        'ALWAYS': FileProcessModes.ALWAYS,
    }
    for dir_exec in definitions_dict['directory-execution']:
        directory = dir_exec['directory']
        exec_type = dir_exec['execution-type']
        if exec_type not in lookup_dict:
            raise ValueError('Config file contains unknown execution-type ' +
                             f'\'{exec_type}\' for directory \'{directory}\'.')
        dir_exec['execution-type'] = lookup_dict[exec_type]

    logging.debug('Read database definitions config dictionary.')
    return definitions_dict


def get_variable_dict(definitions_dict: dict, environment: str) -> dict:
    """
    Get a dictionary containing CI/CD variable values from the config.json file for a specified environment.

    Parameters
    ----------
    definitions_dict : dict
        A dictionary containing values read from the config.json file.
    environment : str
        The name of the environment being deployed to, e.g. sbox, dev, test, int, stg, prod.

    Returns
    -------
    dict
        A dictionary containing CI/CD variable values for the specified environment.
    """
    # parse variables

    logging.debug('Parsing variables from definitions dictionary...')
    variable_dict = {}
    for key, value in definitions_dict['variables'].items():
        variable_dict[key] = value
    for key, value in definitions_dict['environments'][environment.lower()]['variables'].items():
        variable_dict[key] = value
    logging.debug('Parsed variables from definitions dictionary.')

    # check that some mandatory variables are present

    logging.debug('Checking required config variables are present...')
    required_variables = ['SOLUTION_NAME', 'solution_name', 'solution-name', 'ENV', 'env', 'WAREHOUSE_NAME']
    missing_variables = []
    for required_variable in required_variables:
        if required_variable not in variable_dict:
            missing_variables.append(required_variable)
    if len(missing_variables) > 0:
        raise ValueError('The following variables are missing from the config.ini file: ' +
                         ', '.join(missing_variables))
    logging.debug('Checked required config variables are present.')

    return variable_dict

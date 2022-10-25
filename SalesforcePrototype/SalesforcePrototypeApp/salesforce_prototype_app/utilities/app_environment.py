import os
from enum import Enum

def is_running_in_container() -> bool:
    """
    Is the code running inside a docker container?

    This function relies on the following line being present in dockerfile:

    ENV RUNNINGINCONTAINER 1

    This approach is based on https://stackoverflow.com/questions/43878953

    Returns
    -------
    bool
        True if the code is running inside a docker container, False otherwise.
    """
    return os.getenv('RUNNINGINCONTAINER') == "1"


def is_running_in_aws() -> bool:
    """
    Is the code running inside an ECS container in AWS?

    This approach is based on
    https://docs.aws.amazon.com/AmazonECS/latest/userguide/task-metadata-endpoint-v4-fargate.html

    Returns
    -------
    bool
        True if the code is running inside an ECS container in AWS, False otherwise.
    """
    metadata_url = os.getenv('ECS_CONTAINER_METADATA_URI_V4')
    return metadata_url is not None and len(metadata_url) > 0


class EnvironmentVariableNames(Enum):
    """
    The set of supported environment variables.
    """


    ENABLED = 1,
    SERVICE_NAME = 2,
    ENVIRONMENT_NAME = 3,
    AWS_REGION_NAME = 10,  # for debug use outside of AWS only
    AWS_PROFILE_NAME = 11,  # for debug use outside of AWS only
    AWS_S3_BUCKET_NAME = 12
    AWS_SNS_TOPIC_ARN = 14,
    DATA_SOURCE_GAS_ROOT_URL = 21,
    DATA_SOURCE_GAS_FILENAMES = 22,
    DATA_SOURCE_ELECTRICITY_ROOT_URL = 23,
    DATA_SOURCE_ELECTRICITY_FILENAMES = 24,
    SNOWFLAKE_ACCOUNT_NAME = 31,
    SNOWFLAKE_USERNAME = 32,
    SNOWFLAKE_RSA_KEY_PASSPHRASE = 33,
    SNOWFLAKE_ROLE_NAME = 34,
    SNOWFLAKE_WH_NAME = 35,
    SNOWFLAKE_DB_NAME = 36
    DELETE_DATA_FILES = 90

def get_env_var_value(env_var: EnvironmentVariableNames) -> str:
    """
    Get the value of an environment variable.

    The environment variables defined in the container/system need to be prefixed with CRUK_ to avoid accidental name
    collisions with existing system environment variables.

    Parameters
    ----------
    env_var : EnvironmentVariableNames
        The environment variable to retrieve the value of.

    Returns
    -------
    str
        The value of the environment variable.
    """
    return os.getenv('CRUK_' + env_var.name, '')

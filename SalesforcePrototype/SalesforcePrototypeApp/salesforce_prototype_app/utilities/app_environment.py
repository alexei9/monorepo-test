import boto3
import logging
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
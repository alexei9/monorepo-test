# import boto3
#
#
# def get_aws_client(aws_service_name: str, aws_region_name: str = None, aws_profile_name: str = None):
#     """
#     Get a boto3 client for interacting with an AWS service.
#
#     Parameters
#     ----------
#     aws_service_name: str
#         The name of the AWS service to get a client for, e.g. secretsmanager.
#     aws_region_name : str
#         The name of the AWS region to connect to, e.g. eu-west-2.
#         If the CI/CD process is running inside AWS (e.g. in AWS CodeBuild) then this can be left blank.
#     aws_profile_name : str
#         The name of a profile in the AWS credentials file that specifies the credentials to be used when connecting
#         to AWS.  If the CI/CD process is running inside AWS (e.g. in AWS CodeBuild) then this can be left blank.
#
#     Returns
#     -------
#     client
#         A boto3 client object that can be used to make API requests to the specified AWS service.
#     """
#     if aws_profile_name is None:
#         session = boto3.Session()
#     else:
#         session = boto3.Session(region_name=aws_region_name, profile_name=aws_profile_name)
#     client = session.client(aws_service_name)
#
#     return client

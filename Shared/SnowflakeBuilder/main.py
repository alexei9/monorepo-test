import argparse
import logging
import os
import sys
import snowflake_builder.actions.apply_changes as apply_changes
import snowflake_builder.actions.prepare_environment as prepare_env
import snowflake_builder.actions.rotate_secret_login as rotate_secret_login
import snowflake_builder.actions.test_secret_login as test_secret_login
import snowflake_builder.classes.snowflake_connector as snowflake_connector
import snowflake_builder.utilities.app_logging as app_logging
import snowflake_builder.utilities.aws_utilities as aws_utilities


def main():

    # start logging

    app_logging.start_logging(level='DEBUG')
    logging.info('Snowflake CI/CD')
    logging.info('Python version: ' + sys.version)

    # basic command parsing

    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument('--prepare-environment', action='store_true',
                        help="Prepare an environment by creating a user in Snowflake for CI/CD and storing the user" +
                        " credentials in AWS Secrets Manager.  Not valid for environment=pers.")
    parser.add_argument('--test-secret', action='store_true',
                        help="Test the Snowflake credentials stored in the specified AWS Secrets Manager secret.")
    parser.add_argument('--apply-changes', action='store_true',
                        help="Apply Snowflake changes to the specified Snowflake environment.")
    parser.add_argument('--rotate-secret', action='store_true',
                        help="Rotate the Snowflake credentials stored in the specified AWS Secrets Manager secret.")

    args = parser.parse_known_args()[0]

    # command specified?

    if not (args.prepare_environment or args.test_secret or args.apply_changes or args.rotate_secret):
        raise ValueError('Either --prepare-environment, --test-secret, --apply-changes, or --rotate-secret ' +
                         'must be specified.')

    # detailed argument parsing

    parser.add_argument('--snowflake-account', default="cruk.eu-west-2.privatelink",
                        help="The account name used to connect to Snowflake via the Snowflake Python connector.")

    if args.prepare_environment:
        parser.add_argument('--environment', required=True,
                            choices=['sbox', 'dev', 'test', 'int', 'stg', 'prod'],
                            help="The account name used to connect to Snowflake via the Snowflake Python connector.")
        parser.add_argument('--snowflake-auth', required=True,
                            help="The Snowflake authentication method to use.  Only SINGLE_SIGN_ON and " +
                                 "USERNAME_PASSWORD can be used when preparing an environment.")
        parser.add_argument('--snowflake-user', required=True,
                            help="The Snowflake user to be used when preparing the environment.  The user should " +
                                 "have been granted the ACCOUNTADMIN role.")
        parser.add_argument('--snowflake-password',
                            help="The password used to authenticate the specified Snowflake user.")
        parser.add_argument('--snowflake-role', default="ACCOUNTADMIN",
                            help="The Snowflake role used when preparing the environment - typically ACCOUNTADMIN.")
        parser.add_argument('--snowflake-warehouse', required=True,
                            help="The name of the Snowflake warehouse to use when executing the SQL scripts.")
        parser.add_argument('--aws-region', default="eu-west-2",
                            help="The AWS region where the AWS account exists that will contain the CI/CD secret.")
        parser.add_argument('--aws-profile', required=True,
                            help="The name of the set of credentials in the local AWS credentials file, e.g. crukbidev")

    if args.test_secret:
        parser.add_argument('--aws-secret', required=True,
                            help="The name of the secret containing Snowflake login credentials that is to be tested.")
        parser.add_argument('--aws-region', default="eu-west-2",
                            help="The AWS region where the AWS account exists that will contain the CI/CD secret.")
        parser.add_argument('--aws-profile',
                            help="The name of the set of credentials in the local AWS credentials file, e.g. " +
                                 "crukbidev.  If not specified, the current IAM credentials will be used.")

    if args.apply_changes:
        parser.add_argument('--definitions-path-abs', default=os.getcwd(),
                            help="The absolute path to the database definitions directory containing the " +
                                 "config.ini file.")
        parser.add_argument('--definitions-path-rel',
                            help="The relative path to the database definitions directory containing the " +
                                 "config.ini file.")
        parser.add_argument('--environment', required=True,
                            choices=['sbox', 'dev', 'test', 'int', 'stg', 'prod'],
                            help="The account name used to connect to Snowflake via the Snowflake Python connector.")
        parser.add_argument('--aws-region', default="eu-west-2",
                            help="The AWS region where the AWS account exists that will contain the CI/CD secret.")
        parser.add_argument('--aws-profile',
                            help="The name of the set of credentials in the local AWS credentials file, e.g. " +
                                 "crukbidev.  If not specified, the current IAM credentials will be used.")
        parser.add_argument('--force-enabled', action='store_true',
                            help="Assume that all of the cicd-enabled settings in the config.ini file are set to true.")

    if args.rotate_secret:
        parser.add_argument('--snowflake-auth', required=True,
                            help="The Snowflake authentication method to use.  SINGLE_SIGN_ON, USERNAME_PASSWORD and " +
                                 "AWS_USER_SECRET (=CICD user) can be used when rotating a secret.")
        parser.add_argument('--snowflake-user', required=True,
                            help="The Snowflake user to be used when rotating the user keys.  The user should " +
                                 "have been granted the ACCOUNTADMIN role or an environment admin role, e.g. DEVADMIN.")
        parser.add_argument('--snowflake-password',
                            help="The password used to authenticate the specified Snowflake user.")
        parser.add_argument('--connect-aws-secret',
                            help="The name of the secret containing Snowflake login credentials to use to connect.")
        parser.add_argument('--snowflake-role', default="ACCOUNTADMIN",
                            help="The Snowflake role used when rotating the user keys, e.g. ACCOUNTADMIN, DEVADMIN...")
        parser.add_argument('--rotate-aws-secret', required=True,
                            help="The name of the secret containing Snowflake login credentials that is to be rotated.")
        parser.add_argument('--aws-region', default="eu-west-2",
                            help="The AWS region where the AWS account exists that will contain the CI/CD secret.")
        parser.add_argument('--aws-profile',
                            help="The name of the set of credentials in the local AWS credentials file, e.g. crukbidev")

    args = parser.parse_args()

    # print arguments

    arg_values = {}
    secret_args = ['snowflake_password']
    for key, value in args.__dict__.items():
        if key in secret_args:
            arg_values[key] = 'secret of length ' + str(len(str(value)))
        else:
            arg_values[key] = str(value)
    logging.debug('Arguments: ')
    for key, value in arg_values.items():
        logging.debug('    ' + key + '=' + value)

    # test AWS connectivity

    aws_utilities.check_aws_credentials(args.aws_region, args.aws_profile)

    # run relevant command

    if args.prepare_environment:
        logging.info('Command: Prepare Environment.')
        connector = snowflake_connector.SnowflakeConnector(
            account_name=args.snowflake_account,
            auth_type=args.snowflake_auth,
            user_name=args.snowflake_user,
            password=args.snowflake_password,
            role_name=args.snowflake_role,
            warehouse_name=args.snowflake_warehouse
        )
        prepare_env.create_ci_cd_user_and_secret(
            connector=connector,
            environment=args.environment,
            aws_region_name=args.aws_region,
            aws_profile_name=args.aws_profile
        )

    elif args.test_secret:
        logging.info('Command: Test Secret.')
        test_secret_login.test_login(
            snowflake_account_name=args.snowflake_account,
            aws_secret_name=args.aws_secret,
            aws_region_name=args.aws_region,
            aws_profile_name=args.aws_profile
        )

    elif args.apply_changes:
        logging.info('Command: Apply Changes.')
        definitions_path = args.definitions_path_abs
        if args.definitions_path_rel is not None:
            definitions_path = os.path.normpath(definitions_path + args.definitions_path_rel)
            logging.debug('Definitions path = ' + definitions_path)
        apply_changes.execute_scripts(
            snowflake_account_name=args.snowflake_account,
            definitions_root_path=definitions_path,
            environment=args.environment,
            aws_region_name=args.aws_region,
            aws_profile_name=args.aws_profile,
            force_enabled=args.force_enabled
        )

    elif args.rotate_secret:
        logging.info('Command: Rotate Secret.')
        if args.snowflake_auth == 'AWS_USER_SECRET':
            connector = snowflake_connector.get_snowflake_connector(
                snowflake_account_name=args.snowflake_account,
                aws_secret_name=args.connect_aws_secret,
                role_name=args.snowflake_role,
                aws_region_name=args.aws_region,
                aws_profile_name=args.aws_profile
            )
        else:
            connector = snowflake_connector.SnowflakeConnector(
                account_name=args.snowflake_account,
                auth_type=args.snowflake_auth,
                user_name=args.snowflake_user,
                password=args.snowflake_password,
                role_name=args.snowflake_role
            )
        rotate_secret_login.rotate_secret(
            connector=connector,
            aws_secret_name=args.rotate_aws_secret,
            aws_region_name=args.aws_region,
            aws_profile_name=args.aws_profile,
        )

    logging.info('Finished')


if __name__ == '__main__':
    main()

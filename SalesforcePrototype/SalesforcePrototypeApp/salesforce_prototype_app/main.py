from salesforce_prototype_app.utilities.get_connections import get_boto3,  get_user_secret_arn_from_aws, get_user_secret_from_aws
from salesforce_prototype_app.utilities.app_environment import is_running_in_container
from salesforce_prototype_app.utilities.salesforce_poc import salesforce_poc, generate_source_data, write_target_rows_yield_json_s3
# from salesforce_prototype_app.utilities.acccess_secrets import access_secrets
# from salesforce_prototype_app.utilities.testing_code import get_user_secret_arn_from_aws, get_user_secret_from_aws
from salesforce_prototype_app.utilities.copyinto_snowflake import insert_contact, insert_contact2


if __name__ == '__main__':
    print('Starting Salesforce ELT process...')

    print(is_running_in_container())

    print(get_user_secret_arn_from_aws("ageorge-dev-salesforce-prototype"))

    print(get_user_secret_from_aws("ageorge-dev-salesforce-prototype"))

    # salesforce_poc tests a connection to salesforce by querying 1 row
    salesforce_poc()

    # connect to salesforce
    row_generator = generate_source_data()

    # write to s3
    write_target_rows_yield_json_s3(row_generator)

    # insert Contact s3 file from AWS into Snowflake

    insert_contact()

    #insert_contact2("SALESFORCE_CONTACT")

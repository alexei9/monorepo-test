from salesforce_prototype_app.utilities.get_connections import get_boto3,  get_user_secret_arn_from_aws, get_user_secret_from_aws
from salesforce_prototype_app.utilities.app_environment import is_running_in_container
from salesforce_prototype_app.utilities.salesforce_poc import salesforce_poc, generate_source_data, write_target_rows_yield_json_s3
from salesforce_prototype_app.utilities.acccess_secrets import access_secrets
# from salesforce_prototype_app.utilities.testing_code import get_user_secret_arn_from_aws, get_user_secret_from_aws
from salesforce_prototype_app.utilities.get_columns import get_column_names

def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_hi('Alex George - Updation - toucan attempt')
    print(is_running_in_container())

    print(get_user_secret_arn_from_aws("ageorge-dev-salesforce-prototype"))

    print(get_user_secret_from_aws("ageorge-dev-salesforce-prototype"))

    # salesforce_poc tests a connection to salesforce by querying 1 row
    salesforce_poc()

    # connect to salesforce
    row_generator = generate_source_data()

    # write to s3
    write_target_rows_yield_json_s3(row_generator)

    # move to snowflake
    get_column_names()

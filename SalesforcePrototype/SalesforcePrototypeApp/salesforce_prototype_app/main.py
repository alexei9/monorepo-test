from salesforce_prototype_app.utilities.get_connections import  get_user_secret_arn_from_aws, get_user_secret_from_aws
from salesforce_prototype_app.utilities.app_environment import is_running_in_container
from salesforce_prototype_app.utilities.salesforce_poc import salesforce_poc, pull_salesforce_entity, write_target_rows_yield_json_s3
from salesforce_prototype_app.utilities.copyinto_snowflake import insert_contact
from salesforce_prototype_app.utilities.snowflake_config import get_valid_salesforce_entities


if __name__ == '__main__':
    print('Starting Salesforce ELT process...')

    print(is_running_in_container())

    print(get_user_secret_arn_from_aws("ageorge-dev-salesforce-prototype"))

    print(get_user_secret_from_aws("ageorge-dev-salesforce-prototype"))

    # salesforce_poc tests a connection to salesforce by querying 1 row
    salesforce_poc()


    for salesforce_entity_name in get_valid_salesforce_entities():
        # connect to salesforce
        row_generator = pull_salesforce_entity(salesforce_entity_name)

        # write to s3
        write_target_rows_yield_json_s3(row_generator, salesforce_entity_name)

    # insert Contact s3 file from AWS into Snowflake
    # question for later - which is more efficient - should this be one loop or two (two at present)?
        # Option 1. Pull Entity, Write Entity to S3, Write S3 file to Snowflake
        # Option 2. Pull Entity, Write Entity to S3, Pull next Entity, Write Next Entity to S3 (then loop to Snowflake)
    for salesforce_entity_name in get_valid_salesforce_entities():
        insert_contact(salesforce_entity_name)

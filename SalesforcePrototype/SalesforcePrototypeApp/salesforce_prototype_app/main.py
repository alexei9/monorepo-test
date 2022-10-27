from salesforce_prototype_app.utilities.get_connections import  get_user_secret_arn_from_aws, get_user_secret_from_aws
from salesforce_prototype_app.utilities.app_environment import is_running_in_container
from salesforce_prototype_app.utilities.salesforce_poc import salesforce_poc, pull_salesforce_entity, write_target_rows_yield_json_s3
from salesforce_prototype_app.utilities.copyinto_snowflake import copyinto_snowflake, truncate_snowflaketable
from salesforce_prototype_app.utilities.snowflake_config import get_valid_salesforce_entities
from salesforce_prototype_app.utilities.snowflake_merge import mergeinto_snowflake
from salesforce_prototype_app.helper_functions.testing2 import do_something
from enum import Enum
import os

if __name__ == '__main__':
    print('Starting Salesforce ELT process...')
    print(f"It is {is_running_in_container()} that the code is running in a container")
    # print(get_user_secret_arn_from_aws("ageorge-dev-salesforce-prototype"))
    # print(get_user_secret_from_aws("ageorge-dev-salesforce-prototype"))

    valid_salesforce_entities = get_valid_salesforce_entities()
    for sf_entity_name in valid_salesforce_entities:
        # connect to salesforce

        salesforce_entity_name = sf_entity_name[0]
        print(f'Currently processing {salesforce_entity_name}')

        # truncate loading tables
        truncate_snowflaketable(salesforce_entity_name)

        row_generator = pull_salesforce_entity(salesforce_entity_name)

        # write to s3 and get the filename which is then specified in Snowflake COPY INTO
        filename = write_target_rows_yield_json_s3(row_generator, salesforce_entity_name)

        copyinto_snowflake(salesforce_entity_name, filename)

    # question for later - which is more efficient - should this be one loop or two (one at present)?
    # Option 1. Pull Entity, Write Entity to S3, Write S3 file to Snowflake
    # Option 2. Pull Entity, Write Entity to S3, Pull next Entity, Write Next Entity to S3 (then loop to Snowflake)

    # new code in here to move data from loading into proper schema
        mergeinto_snowflake(salesforce_entity_name)

    print("push-on-deploy testing complete - hi")


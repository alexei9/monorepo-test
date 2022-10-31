import posixpath

from salesforce_prototype_app.utilities.get_connections import  get_user_secret_arn_from_aws, get_user_secret_from_aws
from salesforce_prototype_app.utilities.app_environment import is_running_in_container
from salesforce_prototype_app.utilities.salesforce_poc import salesforce_poc, pull_salesforce_entity, write_target_rows_yield_json_s3
from salesforce_prototype_app.utilities.copyinto_snowflake import copyinto_snowflake, truncate_snowflaketable
from salesforce_prototype_app.utilities.snowflake_config import get_valid_salesforce_entities
from salesforce_prototype_app.utilities.snowflake_merge import mergeinto_snowflake
from salesforce_prototype_app.helper_functions.testing2 import do_something
from enum import Enum
import os
from multiprocessing import Process
import multiprocessing
from salesforce_prototype_app.utilities.main_multip_wrapper import main_multip_wrapper

if __name__ == '__main__':
    print('Starting Salesforce ELT process...')
    print(f"It is {is_running_in_container()} that the code is running in a container")
    # print(get_user_secret_arn_from_aws("ageorge-dev-salesforce-prototype"))
    # print(get_user_secret_from_aws("ageorge-dev-salesforce-prototype"))

    valid_salesforce_entities = get_valid_salesforce_entities()

    new_list = []
    for sf_entity_name in valid_salesforce_entities:
        new_list.append(sf_entity_name[0])

    no_of_processes = 4


    pool = multiprocessing.Pool(processes=no_of_processes)
    pool.map(main_multip_wrapper, new_list)



    # https://docs.python.org/3/library/multiprocessing.html

    # https://superfastpython.com/multiprocessing-for-loop/
    # https://superfastpython.com/multiprocessing-pool-python/


    # THIS BIT BELOW WORKS!
    # processes = [Process(target=main_multip_wrapper, args=(sf_entity_name,)) for sf_entity_name in valid_salesforce_entities]
    # for process in processes:
    #         process.start()


    print("Processing complete")


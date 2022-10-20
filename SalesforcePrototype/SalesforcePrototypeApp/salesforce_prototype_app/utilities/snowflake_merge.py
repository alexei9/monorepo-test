from salesforce_prototype_app.utilities.rsa_tools import get_user_secret_from_aws, get_snowflake_rsa_keys_connection
from salesforce_prototype_app.utilities.get_fieldnames import dict_of_lists


def mergeinto_snowflake(salesforce_entity_name):
    secret_dict = get_user_secret_from_aws()
    # connect to snowflake as service user and read Snowflake version
    con = get_snowflake_rsa_keys_connection(secret_dict)
    cursor = con.cursor()

    print(f'Merging {salesforce_entity_name} into Snowflake')

    column_names = dict_of_lists(salesforce_entity_name)
    snowflake_when_matched = ''
    snowflake_when_notmatched = ''
    snowflake_values = ''
    for x, col_name in enumerate(column_names):

        snowflake_when_matched += f'd.{col_name} = s.{col_name}, '
        snowflake_when_notmatched += f'{col_name}, '
        snowflake_values += f's.{col_name}, '

    snowflake_when_matched = snowflake_when_matched[:-2]
    snowflake_when_notmatched = snowflake_when_notmatched[:-2]
    snowflake_values = snowflake_values[:-2]

#TODO code reliant on primary key being called "ID" - this should be passed as a variable/lookup/list etc

    sql = f"MERGE INTO DEV_AG_SALESFORCE.SALESFORCE_MODEL.SALESFORCE_{salesforce_entity_name} d" \
          f" USING DEV_AG_SALESFORCE.SALESFORCE_LOAD.SALESFORCE_{salesforce_entity_name} s ON d.ID = s.ID " \
          f"WHEN MATCHED THEN UPDATE SET {snowflake_when_matched} " \
          f"WHEN NOT MATCHED THEN INSERT ({snowflake_when_notmatched} )" \
          f"VALUES ({snowflake_values});"

    cursor.execute(sql)

    print(f'{salesforce_entity_name} has been copied into Snowflake')

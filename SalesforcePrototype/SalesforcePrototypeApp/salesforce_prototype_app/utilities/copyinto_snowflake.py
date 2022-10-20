from salesforce_prototype_app.utilities.rsa_tools import get_user_secret_from_aws, get_snowflake_rsa_keys_connection
from salesforce_prototype_app.utilities.get_fieldnames import dict_of_lists



def copyinto_snowflake(salesforce_entity_name, filename):
    secret_dict = get_user_secret_from_aws()
    # connect to snowflake as service user and read Snowflake version
    con = get_snowflake_rsa_keys_connection(secret_dict)
    cursor = con.cursor()

    print(f'Copying {salesforce_entity_name} into Snowflake')
    # cursor.execute("SELECT CURRENT_VERSION()")
    # value = cursor.fetchone()[0]
    # print('Snowflake version: ' + value)


    column_names = dict_of_lists(salesforce_entity_name)
    snowflake_query_select = ''
    snowflake_query_final_select = ''
    for x, col_name in enumerate(column_names):
        #sf_datatype = get_snowflake_datatype(destination_table_name, x)

        # below - replace "VARIANT" with something dynamic for datatype.
        # perhaps this could come from the Source? check with CB
        snowflake_query_select += f'parse_json($1):{col_name}::VARIANT as {col_name}, '
        snowflake_query_final_select  += f's.{col_name}, '

    snowflake_query_select = snowflake_query_select[:-2]

    sql = f"COPY INTO DEV_AG_SALESFORCE.SALESFORCE_LOAD.SALESFORCE_{salesforce_entity_name}" \
                      f" FROM (" \
                      f"SELECT " \
                      f"{snowflake_query_select} " \
                      f"from @DEV_AG_SALESFORCE.SALESFORCE_LOAD.S3_STAGE)" \
                      f" FILE_FORMAT = (FORMAT_NAME = 'DEV_AG_SALESFORCE.SALESFORCE_LOAD.BASIC_CSV')" \
                      f" PATTERN = '.*{filename}.*';"


    cursor.execute(sql)

    print(f'{salesforce_entity_name} has been copied into Snowflake')


def truncate_snowflaketable(salesforce_entity_name):
    secret_dict = get_user_secret_from_aws()
    # connect to snowflake as service user and read Snowflake version
    con = get_snowflake_rsa_keys_connection(secret_dict)
    cursor = con.cursor()

    print(f'Preparing to truncate DEV_AG_SALESFORCE.SALESFORCE_LOAD.SALESFORCE_{salesforce_entity_name}')
    sql = f"TRUNCATE DEV_AG_SALESFORCE.SALESFORCE_LOAD.SALESFORCE_{salesforce_entity_name};"
    cursor.execute(sql)
    print(f'DEV_AG_SALESFORCE.SALESFORCE_LOAD.SALESFORCE_{salesforce_entity_name} has been truncated')

def test_snowflake_service_user_authentication():
    # get existing user secret
    secret_dict = get_user_secret_from_aws()
    # connect to snowflake as service user and read Snowflake version
    con = get_snowflake_rsa_keys_connection(secret_dict)
    cursor = con.cursor()
    cursor.execute("SELECT CURRENT_VERSION()")
    value = cursor.fetchone()[0]
    print('Snowflake version: ' + value)
    print('Service user successfully established connection to Snowflake.')


def lookup_snowflake_datatype(datatype: int):
    # change!! this is almost certainly not the way to do it. discuss with CB.
    snowflake_datatype = {0: 'NUMBER', 1: 'REAL', 2: 'TEXT', 3: 'DATE', 4: 'TIMESTAMP', 5: 'VARIANT',
                          6: 'TIMESTAMP_LTZ', 7: 'TIMESTAMP_TZ', 8: 'TIMESTAMP_NTZ', 9: 'OBJECT', 10: 'ARRAY',
                          11: 'BINARY', 12: 'TIME', 13: 'BOOLEAN'}
    return snowflake_datatype.get(datatype)


def get_snowflake_datatype(destination_table_name, position_in_iteration):

    secret_dict = get_user_secret_from_aws()
    # connect to snowflake as service user and read Snowflake version
    con = get_snowflake_rsa_keys_connection(secret_dict)
    csr = con.cursor()
    metadata = csr.describe(f"SELECT * FROM DEV_AG_SALESFORCE.SALESFORCE_LOAD.{destination_table_name}")
    snowflake_column_metadata = metadata[(position_in_iteration)]
    snowflake_column_datatype_code = snowflake_column_metadata[1]
    return lookup_snowflake_datatype(snowflake_column_datatype_code)


from salesforce_prototype_app.utilities.rsa_tools import get_user_secret_from_aws, get_snowflake_rsa_keys_connection


def insert_contact2(destination_table_name):

    secret_dict = get_user_secret_from_aws()
    # connect to snowflake as service user and read Snowflake version
    con = get_snowflake_rsa_keys_connection(secret_dict)
    cursor = con.cursor()

    column_names = get_column_names(destination_table_name)
    snowflake_query_select = ''
    snowflake_query_final_select = ''
    for x, col_name in enumerate(column_names):
        sf_datatype = get_snowflake_datatype(destination_table_name, x)

        snowflake_query_select += f'parse_json($1):{col_name}::{sf_datatype} as {col_name}, '
        snowflake_query_final_select  += f's.{col_name}, '

    snowflake_query_select = snowflake_query_select[:-2]

    snowflake_query = f"COPY INTO DEV_AG_SALESFORCE.SALESFORCE_LOAD.{destination_table_name}" \
                      f" FROM (" \
                      f"SELECT " \
                      f"{snowflake_query_select} " \
                      f"from @DEV_AG_SALESFORCE.SALESFORCE_LOAD.S3_STAGE)" \
                      f" FILE_FORMAT = (FORMAT_NAME = 'DEV_AG_SALESFORCE.SALESFORCE_LOAD.BASIC_CSV');"

    cursor.execute(snowflake_query)

#    print(snowflake_query)
#   print("hello")

# def get_column_names(destination_table_name):
def insert_contact():
    secret_dict = get_user_secret_from_aws()
    # connect to snowflake as service user and read Snowflake version
    con = get_snowflake_rsa_keys_connection(secret_dict)
    cursor = con.cursor()

    cursor.execute("SELECT CURRENT_VERSION()")
    value = cursor.fetchone()[0]
    print('Snowflake version: ' + value)

    sql = f"COPY INTO DEV_AG_SALESFORCE.SALESFORCE_LOAD.SALESFORCE_CONTACT " \
          f"FROM (SELECT parse_json($1):Id::VARIANT as ID, " \
          f"parse_json($1):AccountId::VARIANT as ACCOUNTID, " \
          f"parse_json($1):Salutation::VARIANT as SALUTATION," \
          f"parse_json($1):FirstName::VARIANT as FIRSTNAME," \
          f"parse_json($1):LastName::VARIANT as LASTNAME from @DEV_AG_SALESFORCE.SALESFORCE_LOAD.S3_STAGE)" \
          f" FILE_FORMAT = (FORMAT_NAME = 'DEV_AG_SALESFORCE.SALESFORCE_LOAD.BASIC_CSV');"


    cursor.execute(sql)


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


def copyinto_snowflake(destination_table_name, stage_name):

    secret_dict = get_user_secret_from_aws()
    # connect to snowflake as service user and read Snowflake version
    con = get_snowflake_rsa_keys_connection(secret_dict)
    csr = con.cursor()

    column_names = get_column_names(destination_table_name)
    snowflake_query_select = ''
    snowflake_query_final_select = ''
    #x = 0
    #for col_name in column_names:
    for x, col_name in enumerate(column_names):
        sf_datatype = get_snowflake_datatype(destination_table_name, x)

        snowflake_query_select += f'parse_json($1):{col_name}::{sf_datatype} as {col_name}, '
        snowflake_query_final_select  += f's.{col_name}, '
        #x +=1

    snowflake_query_select = snowflake_query_select[:-2]
    snowflake_query = f"COPY INTO {destination_table_name}" \
                      f" FROM (" \
                      f"SELECT " \
                      f"{snowflake_query_select} " \
                      f"from @{stage_name})"\


    csr.execute(snowflake_query)
    con.close()

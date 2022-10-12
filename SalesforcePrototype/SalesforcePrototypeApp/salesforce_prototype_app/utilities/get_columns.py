from salesforce_prototype_app.utilities.rsa_tools import get_user_secret_from_aws, get_snowflake_rsa_keys_connection

# def get_column_names(destination_table_name):
def get_column_names():
    secret_dict = get_user_secret_from_aws()
    # connect to snowflake as service user and read Snowflake version
    con = get_snowflake_rsa_keys_connection(secret_dict)
    cursor = con.cursor()

    cursor.execute("SELECT CURRENT_VERSION()")
    value = cursor.fetchone()[0]
    print('Snowflake version: ' + value)

    #sql = f"SELECT * FROM DEV_AG_SALESFORCE.SALESFORCE_LOAD.Contact WHERE Id = '0032500001eyiEkAAI'"
    # cursor.execute("USE WAREHOUSE NON_PROD_ALL")

    sql1 = f"SELECT * FROM DEV_AG_SALESFORCE.SALESFORCE_LOAD.SALESFORCE_CONTACT WHERE Id = '0032500001eyiEkAAI'"
    sql3 = f"COPY INTO DEV_AG_SALESFORCE.SALESFORCE_LOAD.SALESFORCE_CONTACT " \
           f"FROM (SELECT parse_json($1):Id::VARIANT as Id, " \
           f"parse_json($1):AccountId::VARIANT as AccountId, " \
           f"parse_json($1):Salutation::VARIANT as Salutation," \
           f"parse_json($1):FirstName::VARIANT as FirstName," \
           f"parse_json($1):LastName::VARIANT as LastName from @DEV_AG_SALESFORCE.SALESFORCE_LOAD.S3_STAGE)" \
           f" FILE_FORMAT = (FORMAT_NAME = 'DEV_AG_SALESFORCE.SALESFORCE_LOAD.BASIC_CSV');"

    cursor.execute(sql3)
    list_of_roles = []

  #  list_of_roles = cursor.fetchall()


  #  print(list_of_roles[0])

    #print(value2)



#    cursor.execute("SELECT * FROM SALESFORCE_LOAD.SALESFORCE_CONTACT")

    # sql1 = f'USE DATABASE DEV_AG_SALESFORCE'
    # sql2 = f'SELECT 1 FROM SALESFORCE_LOAD.SALESFORCE_CONTACT'
    #
    # cursor.execute(sql1)
    # cursor.execute(sql2)
    # agq = cursor.execute(sql2)
    # print(agq)



    # # create query string
    # get_column_names_sql = f'SELECT TOP (1) * FROM {destination_table_name}'
    # # execute sql
    # execute_get_column_names = dmvp_cursor.execute(get_column_names_sql)
    # column_names = [column[0] for column in execute_get_column_names.description]
    #
    #

    #con.close()
    # return column_names
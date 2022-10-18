from salesforce_prototype_app.utilities.rsa_tools import get_user_secret_from_aws, get_snowflake_rsa_keys_connection



def get_valid_salesforce_entities():
    secret_dict = get_user_secret_from_aws()
    # connect to snowflake as service user and read Snowflake version
    con = get_snowflake_rsa_keys_connection(secret_dict)
    cursor = con.cursor()
    sql_query = f"SELECT ENTITY_NAME FROM DEV_AG_SALESFORCE.SALESFORCE_LOAD.CONFIG WHERE PROCESS_FLAG ='Y'"
    cursor.execute(sql_query)
    valid_entities = cursor.fetchall()


    con.close()
   # print(column_names)
    return valid_entities[0]



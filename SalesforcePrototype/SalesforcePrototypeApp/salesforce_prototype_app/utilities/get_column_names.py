from salesforce_prototype_app.utilities.rsa_tools import get_user_secret_from_aws, get_snowflake_rsa_keys_connection



def get_column_names(destination_table_name):
    secret_dict = get_user_secret_from_aws()
    # connect to snowflake as service user and read Snowflake version
    con = get_snowflake_rsa_keys_connection(secret_dict)
    cursor = con.cursor()
    get_column_names_sql = f'SELECT TOP 1 * FROM DEV_AG_SALESFORCE.SALESFORCE_LOAD.{destination_table_name}'
    execute_get_column_names = cursor.execute(get_column_names_sql)
    column_names = [column[0] for column in execute_get_column_names.description]
    con.close()
    print(column_names)
    return column_names
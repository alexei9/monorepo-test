import logging
import snowflake_builder.classes.snowflake_connector as snowflake_connector


def execute_sql_command(connector: snowflake_connector.SnowflakeConnector, sql: str, parameters: dict = None,
                        role_name: str = None, warehouse_name: str = None, database_name: str = None):
    """
    Execute a SQL command that returns no value against Snowflake.

    Parameters
    ----------
    connector : snowflake_connector.SnowflakeConnector
        A connection to Snowflake.
    sql : str
        The SQL command to execute.
    parameters : dict
        A dictionary containing a list of parameter values where the dictionary keys are parameter names in the SQL.
    role_name : str
        The name of the Snowflake role to be used when executing the SQL command.
    warehouse_name : str
        The name of the Snowflake warehouse to be used to execute the SQL command.
    database_name : str
        The name of the Snowflake database to be used when executing the SQL command.

    Returns
    -------
    None
    """
    con = connector.connect(role_name, warehouse_name, database_name)
    logging.debug('Executing SQL command...')
    con.cursor().execute(sql, parameters)
    con.close()
    logging.debug('Executed SQL command.')


def execute_sql_scalar(connector: snowflake_connector.SnowflakeConnector, sql: str, parameters: dict = None,
                       role_name: str = None, warehouse_name: str = None, database_name: str = None):
    """
    Execute a SQL query that returns a scalar value against Snowflake.

    Parameters
    ----------
    connector : snowflake_connector.SnowflakeConnector
        A connection to Snowflake.
    sql : str
        The SQL query to execute.
    parameters : dict
        A dictionary containing a list of parameter values where the dictionary keys are parameter names in the SQL.
    role_name : str
        The name of the Snowflake role to be used when executing the SQL query.
    warehouse_name : str
        The name of the Snowflake warehouse to be used to execute the SQL query.
    database_name : str
        The name of the Snowflake database to be used when executing the SQL query.

    Returns
    -------
    object
        The value returned from Snowflake query.
    """
    con = connector.connect(role_name, warehouse_name, database_name)
    logging.debug('Executing SQL query...')
    cursor = con.cursor()
    cursor.execute(sql, parameters)
    value = cursor.fetchone()[0]
    con.close()
    logging.debug('Executed SQL query, result: ' + str(value))
    return value


def execute_sql_rows(connector: snowflake_connector.SnowflakeConnector, sql: str, parameters: dict = None,
                     role_name: str = None, warehouse_name: str = None, database_name: str = None):
    """
    Execute a SQL query that returns row(s) against Snowflake.

    Parameters
    ----------
    connector : snowflake_connector.SnowflakeConnector
        A connection to Snowflake.
    sql : str
        The SQL query to execute.
    parameters : dict
        A dictionary containing a list of parameter values where the dictionary keys are parameter names in the SQL.
    role_name : str
        The name of the Snowflake role to be used when executing the SQL query.
    warehouse_name : str
        The name of the Snowflake warehouse to be used to execute the SQL query.
    database_name : str
        The name of the Snowflake database to be used when executing the SQL query.

    Returns
    -------
    Iterator[dict[str, object]]
        A generator object that can be iterated a dictionary for each row in the query results, where the keys in the
        dictionary are the column names and the values in the dictionary are the column values in the current row.
    """
    con = connector.connect(role_name, warehouse_name, database_name)
    logging.debug('Executing SQL query...')
    cursor = con.cursor()
    cursor.execute(sql, parameters)
    columns = [column[0] for column in cursor.description]
    logging.debug('Query run, yielding results...')
    row_count = 0
    for row in cursor:
        row_count = row_count + 1
        yield dict(zip(columns, row))  # dict(zip(columns, row)) produces a dict of the column values in the current row
    logging.debug('Results completed.')
    con.close()
    logging.debug('Executed SQL query, rows: ' + str(row_count))

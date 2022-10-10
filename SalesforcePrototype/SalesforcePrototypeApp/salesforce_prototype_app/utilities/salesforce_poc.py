from salesforce_prototype_app.utilities.get_connections import get_salesforce

def salesforce_poc():

    sf = get_salesforce()
    ## print(sf.describe())
    valid_contact_fields_sql = f"SELECT Id, FirstName, LastName FROM Contact WHERE Id = '0032500001eyiEkAAI'"
    results = sf.query_all(valid_contact_fields_sql)
    rows = results['records']
    for row in rows:
        del row['attributes']

    for row in rows:
        print(row)


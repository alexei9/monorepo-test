from salesforce_prototype_app.utilities.get_connections import get_salesforce
from simple_salesforce import SFType
from tabulate import tabulate
import salesforce_prototype_app.utilities.app_environment as app_env



def salesforce_query():

    sf = get_salesforce()
    valid_contact_fields_sql = f"SELECT ID, FIRSTNAME, LASTNAME FROM Contact WHERE Id = '0032500001eyiEkAAI'"
    results = sf.query_all(valid_contact_fields_sql)
    rows = results['records']
    for row in rows:
        del row['attributes']
    for row in rows:
        print(row)

    objects = sf.describe()

    print(f'{len(objects["sobjects"])} objects found.')
    for obj in objects["sobjects"]:
        print(obj["label"])


def get_salesforce_fields_from_entity():
    sf = get_salesforce()
    object_name = input('Specify object name: ')
    sf_type = SFType(object_name, session_id=sf.session_id, sf_instance=sf.sf_instance)
    description = sf_type.describe()
    fields = description['fields']
    table_data = list(map(lambda x: [x['name'], x['label'], x['type']], fields))
    print(tabulate(table_data, headers=['Name', 'Label', 'SF Data Type']))



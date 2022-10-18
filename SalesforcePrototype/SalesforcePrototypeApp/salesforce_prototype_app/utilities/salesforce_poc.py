from salesforce_prototype_app.utilities.get_connections import get_salesforce, get_boto3
import salesforce_prototype_app.utilities.app_environment as app_env
from salesforce_prototype_app.utilities.get_fieldnames import dict_of_lists
from datetime import datetime
import gzip
import json
import os

def salesforce_poc():

    sf = get_salesforce()
    valid_contact_fields_sql = f"SELECT ID, FIRSTNAME, LASTNAME FROM Contact WHERE Id = '0032500001eyiEkAAI'"
    results = sf.query_all(valid_contact_fields_sql)
    rows = results['records']
    for row in rows:
        del row['attributes']
    for row in rows:
        print(row)


def pull_salesforce_entity(salesforce_entity_name):

    sf = get_salesforce()
    objects = sf.describe()

    valid_contact_fields = ["Id", "AccountId", "Salutation", "FirstName", "LastName"]
    valid_contact_fields = dict_of_lists(salesforce_entity_name)

    e= ', '.join(valid_contact_fields)
    # valid_contact_fields_sql = f"SELECT {e} FROM Contact"
    valid_contact_fields_sql = f"SELECT {e} FROM {salesforce_entity_name}"

    results = sf.query_all(valid_contact_fields_sql)


    rows = results['records']
    for row in rows:
        del row['attributes']
    for row in rows:
        yield row


def write_target_rows_yield_json_s3(row_generator, salesforce_entity_name):
    dt = datetime.now()
    formatted_date = datetime.strftime(dt, '%Y%m%d%H%M%S')
    #filename = f'Contact_{formatted_date}.json.gz'
    filename = f'{salesforce_entity_name}_{formatted_date}.json.gz'


    with gzip.open(filename, mode='wt', encoding='UTF8', newline='') as f:
        for idx, row_values in enumerate(row_generator, 1):
            json.dump(json.dumps(row_values, default=str), f)
            f.write("\n")

    s3 = get_boto3()
    bucket = 'ageorge-dev-salesforce-prototype'
    prefix = f'{salesforce_entity_name}'
    key = f'{prefix}/{filename}'
    s3.upload_file(Filename=filename, Bucket=bucket, Key=key)

    # remove the file if created locally (if created via AWS it gets removed when the container is destroyed at the end
    # of the ELT so not actions required?
    if app_env.is_running_in_aws():
        pass
    else:
        os.remove(filename)

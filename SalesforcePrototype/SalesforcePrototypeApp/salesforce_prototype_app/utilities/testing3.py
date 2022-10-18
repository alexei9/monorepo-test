from salesforce_prototype_app.utilities.get_fieldnames import listtests


result = listtests()
x = result["valid_contact_fields"]

for x in x:
    print(x)
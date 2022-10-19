from salesforce_prototype_app.utilities.snowflake_config import get_valid_salesforce_entities

def dict_of_lists(salesforce_entity):


    entity_quoted = f"'{get_valid_salesforce_entities()}'"
    print(entity_quoted)

# this is a dictionary of lists
# the "key" (first value) is to match (the entity in Salesforce) (the table in Snowflake)
# this will still be "config-driven" by a Snowflake table

    dict_of_lists = {
        "Contact": ["Id", "AccountId", "Salutation", "FirstName", "LastName"],
        "Person": ["PersonId", "HairColor", "Address", "CatName", "StarSign"],
        "City": ["CityId", "CityName", "Population"]
    }

    return dict_of_lists[salesforce_entity]



#
#
# for x in get_valid_salesforce_entities():
#     print(x[0])

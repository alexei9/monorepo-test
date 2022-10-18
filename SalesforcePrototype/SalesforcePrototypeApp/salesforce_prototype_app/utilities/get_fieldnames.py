


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

    #print(dict_of_lists[salesforce_entity])
    return dict_of_lists[salesforce_entity]


# dict_of_lists("Contact")
# everything = listtests()
# for x in everything.keys():
#     print(x)





from salesforce_prototype_app.utilities.snowflake_config import get_valid_salesforce_entities


for x in get_valid_salesforce_entities():
    print(x[0])



def listtests():


# this is a dictionary of lists
# the "key" (first value) is to match (the entity in Salesforce) (the table in Snowflake)
# this will still be "config-driven" by a Snowflake table

    dict_of_lists = {
        "contact": ["Id", "AccountId", "Salutation", "FirstName", "LastName"],
        "person": ["PersonId", "HairColor", "Address", "CatName", "StarSign"],
        "city": ["CityId", "CityName", "Population"]
    }


    return dict_of_lists

everything = listtests()
for x in everything.keys():
    print(x)

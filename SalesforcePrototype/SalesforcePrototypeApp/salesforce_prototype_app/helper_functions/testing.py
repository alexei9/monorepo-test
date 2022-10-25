

from salesforce_prototype_app.utilities.get_connections import get_awsclient
get_awsclient("secretsmanager")
get_awsclient("s3")

#
# from salesforce_prototype_app.utilities.get_connections import get_salesforce
#
# sf = get_salesforce()
# description = sf.Account.describe()
# print(description)



# https://stackoverflow.com/questions/65079754/salesforce-soql-how-to-retrieve-all-column-names-from-account

# 1     login to Salesforce SIT
# 2     cog in top right
# 3     Developer Console
# 4     File --> Open
# 5     Objects
# 6     Select Object, e.g. "Account"
# 7     Click "Open"
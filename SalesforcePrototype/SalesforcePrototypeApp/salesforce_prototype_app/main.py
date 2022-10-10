from salesforce_prototype_app.utilities.get_connections import get_boto3
from salesforce_prototype_app.utilities.app_environment import is_running_in_container
import boto3


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_hi('Alex George - Updation - toucan attempt')
    print(is_running_in_container())
    print(get_boto3())
    client = get_boto3()
    response = client.list_objects_v2(Bucket='ageorge-dev-salesforce-prototype')
    for content in response.get('Contents', []):
        print(content['Key'])

# See PyCharm help at https://www.jetbrains.com/help/pycharm/

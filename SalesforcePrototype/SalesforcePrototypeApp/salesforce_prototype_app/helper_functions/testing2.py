from enum import Enum
import os


class EnvironmentVariableNames(Enum):
    CRUK_AWS_PROFILE_NAME = 1,
    CRUK_AWS_REGION_NAME = 2



def get_env_var_value(env_var: EnvironmentVariableNames) -> str:
    return os.getenv(env_var.name, '')

def do_something():
    x = get_env_var_value(EnvironmentVariableNames.CRUK_AWS_PROFILE_NAME)
    print(x)


for name, value in os.environ.items():
    print(f"{name} = {value}")


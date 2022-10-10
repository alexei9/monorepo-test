import botocore
import botocore.session
from aws_secretsmanager_caching import SecretCache, SecretCacheConfig

def access_secrets():
    client = botocore.session.get_session().create_client('secretsmanager')
    cache_config = SecretCacheConfig()
    cache = SecretCache( config = cache_config, client = client)

    secret = cache.get_secret_string('snowflake-rsa-key-passphrase')
    return secret


# https://docs.aws.amazon.com/secretsmanager/latest/userguide/retrieving-secrets_cache-python.html
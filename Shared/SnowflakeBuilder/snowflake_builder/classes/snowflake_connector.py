import logging
import snowflake.connector
import snowflake_builder.classes.snowflake_user_secret as snowflake_user_secret
from cryptography.hazmat.primitives import serialization
from enum import Enum


class SnowflakeAuthTypes(Enum):
    SINGLE_SIGN_ON = 1
    USERNAME_PASSWORD = 2,
    RSA_KEYS = 3,
    AWS_USER_SECRET = 4


class SnowflakeConnector:
    """
    A class that represents a set of Snowflake connection parameters and can be used to open a connection to Snowflake.
    Multiple authentication methods are supported:  Single sign on via web browser, username-password, RSA keys and
    credentials stored in AWS Secrets Manager.
    """
    def __init__(self, account_name: str, auth_type: SnowflakeAuthTypes | str,
                 user_name: str = None, password: str = None,
                 public_key: str = None, private_key: str = None,
                 user_secret: snowflake_user_secret.SnowflakeUserSecret = None,
                 role_name: str = None, warehouse_name: str = None, database_name: str = None):
        """
        Create an object that can be used to open a connection to Snowflake.

        Parameters
        ----------
        account_name : str
            The name of the Snowflake account to connect to.  This is usually the prefix in Snowflake URLs.
        auth_type : SnowflakeAuthTypes
            The type of authentication to use when connecting to Snowflake.
        user_name : str
            If using SSO or username-password authentication, then the name of the Snowflake user.
        password : str
            If using username-password authentication, then the password of the Snowflake user.
        public_key : str
            If using RSA key-pair authentication, then the text-encoded public key.
        private_key : str
            If using RSA key-pair authentication, then the text-encoded private key.
        user_secret : snowflake_user_secret.SnowflakeUserSecret
            If using a secret stored in AWS secrets manager to authenticate, then the user secret from AWS SM.
        role_name : str
            The name of the Snowflake role to be used when executing the SQL query.
        warehouse_name : str
            The name of the Snowflake warehouse to be used to execute the SQL query.
        database_name : str
            The name of the Snowflake database to be used when executing the SQL query.
        """
        self.account_name = account_name
        if type(auth_type) is str:
            auth_values = [e.name for e in SnowflakeAuthTypes]
            if auth_type not in auth_values:
                raise ValueError(auth_type + ' is not a valid Snowflake Auth Type.')
            else:
                auth_type = SnowflakeAuthTypes[auth_type]
        self.auth_type = auth_type
        self.public_key = public_key
        self.private_key_text = private_key
        self.user_name = user_name
        self.password = password
        self.user_secret = user_secret
        self.role_name = role_name
        self.warehouse_name = warehouse_name
        self.database_name = database_name

        if auth_type == SnowflakeAuthTypes.USERNAME_PASSWORD:
            if user_name is None or len(user_name.strip()) == 0:
                raise ValueError('user_name must be specified.')
            if password is None or len(password.strip()) == 0:
                raise ValueError('password must be specified.')
        elif auth_type == SnowflakeAuthTypes.RSA_KEYS:
            if user_name is None or len(user_name.strip()) == 0:
                raise ValueError('user_name must be specified.')
            if private_key is None or len(private_key.strip()) == 0:
                raise ValueError('Private key must be specified.')
        elif auth_type == SnowflakeAuthTypes.AWS_USER_SECRET:
            if user_secret is None:
                raise ValueError('User secret must be specified.')
            self.user_name = user_secret.user_name
            self.public_key = user_secret.public_key
            self.private_key_text = user_secret.private_key

        if self.private_key_text is not None:
            self.private_key_bytes = get_private_key_bytes(self.private_key_text)

    def connect(self, role_name: str = None, warehouse_name: str = None, database_name: str = None):
        """
        Open a connection to Snowflake, optionally specifying some connection parameters to override the defaults
        specified when this SnowflakeConnector instance was created.

        Parameters
        ----------
        role_name : str
            The name of the Snowflake role to be used when executing the SQL query.
        warehouse_name : str
            The name of the Snowflake warehouse to be used to execute the SQL query.
        database_name : str
            The name of the Snowflake database to be used when executing the SQL query.

        Returns
        -------
        SnowflakeConnection
            A connection to Snowflake.
        """
        use_role = role_name if role_name is not None else self.role_name
        use_warehouse = warehouse_name if warehouse_name is not None else self.warehouse_name
        use_database = database_name if database_name is not None else self.database_name

        if self.auth_type == SnowflakeAuthTypes.SINGLE_SIGN_ON:
            logging.debug('Connecting to Snowflake via SSO...')
            con = snowflake.connector.connect(
                account=self.account_name,
                user=self.user_name,
                authenticator="externalbrowser",
                role=use_role,
                warehouse=use_warehouse,
                database=use_database
            )
        elif self.auth_type == SnowflakeAuthTypes.USERNAME_PASSWORD:
            logging.debug('Connecting to Snowflake via username and password...')
            con = snowflake.connector.connect(
                account=self.account_name,
                user=self.user_name,
                password=self.password,
                role=use_role,
                warehouse=use_warehouse,
                database=use_database
            )
        elif self.auth_type == SnowflakeAuthTypes.RSA_KEYS:
            logging.debug('Connecting to Snowflake via RSA keys...')
            con = snowflake.connector.connect(
                account=self.account_name,
                user=self.user_name,
                private_key=self.private_key_bytes,
                role=use_role,
                warehouse=use_warehouse,
                database=use_database
            )
        elif self.auth_type == SnowflakeAuthTypes.AWS_USER_SECRET:
            logging.debug('Connecting to Snowflake via user secret...')
            con = snowflake.connector.connect(
                account=self.account_name,
                user=self.user_name,
                private_key=self.private_key_bytes,
                role=use_role,
                warehouse=use_warehouse,
                database=use_database
            )
        else:
            raise ValueError('Unknown authentication type: ' + str(self.auth_type))
        return con


def get_snowflake_connector(snowflake_account_name: str, aws_secret_name: str,
                            role_name: str = None, warehouse_name: str = None, database_name: str = None,
                            aws_region_name: str = None, aws_profile_name: str = None) -> SnowflakeConnector:
    """
    Create an instance of the SnowflakeConnector class from a user-secret stored in AWS Secrets Manager.

    Parameters
    ----------
    snowflake_account_name : str
        The name of the Snowflake account to connect to.  This is usually the prefix in Snowflake URLs.
    aws_secret_name : str
        The name of the secret in AWS secrets manager.
    role_name : str
        The name of the Snowflake role to be used when executing the SQL query.
    warehouse_name : str
        The name of the Snowflake warehouse to be used to execute the SQL query.
    database_name : str
        The name of the Snowflake database to be used when executing the SQL query.
    aws_region_name : str
        The name of the AWS region where the secret is located, e.g. eu-west-2.
        If the CI/CD process is running inside AWS (e.g. in AWS CodeBuild) then this can be left blank.
    aws_profile_name : str
        The name of a profile in the AWS credentials file that specifies the credentials to be used when connecting
        to AWS.  If the CI/CD process is running inside AWS (e.g. in AWS CodeBuild) then this can be left blank.

    Returns
    -------
    SnowflakeConnector
        A SnowflakeConnector object containing the credentials read from AWS secrets manager.
    """
    logging.debug('Reading secrets manager secret...')
    user_secret = snowflake_user_secret.get_user_secret_from_aws(aws_secret_name, aws_region_name, aws_profile_name)
    connector = SnowflakeConnector(
        account_name=snowflake_account_name,
        auth_type=SnowflakeAuthTypes.AWS_USER_SECRET,
        user_secret=user_secret,
        role_name=role_name,
        warehouse_name=warehouse_name,
        database_name=database_name
    )
    return connector


def get_private_key_bytes(private_key: str) -> bytes:
    """
    Convert the text representation of a private key to bytes so that it can be used when opening a connection
    to Snowflake.

    Parameters
    ----------
    private_key : str
        The text representation of the private key.

    Returns
    -------
    bytes
        The binary representation of the private key.
    """
    logging.debug('Parsing private key...')
    private_key = '-----BEGIN PRIVATE KEY-----\n' + private_key + '\n-----END PRIVATE KEY-----'
    private_key_bytes = private_key.encode('utf-8')
    p_key = serialization.load_pem_private_key(
        private_key_bytes,
        password=None,
        backend=None)
    pkb = p_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption())
    return pkb

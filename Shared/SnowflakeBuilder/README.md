# SnowflakeBuilder

## Overview

SnowflakeBuilder is a Database Change Management (DCM) tool for managing objects inside Snowflake.  DCM is a generic 
term.  In reality, the tool will manage more than just databases (and their contents) - objects like users, roles, 
storage integrations, etc. can also be managed by the tool. 

SnowflakeBuilder is essentially a command line tool written in Python.  It is expected that developers will only need
to use it as a command line tool.  No ongoing changes to the Python code should be needed (there might be a few changes
whilst we test/stablise the tool).

SnowflakeBuilder allows Snowflake objects to be defined in SQL scripts (under source control).  Those scripts can
then be executed either locally (e.g. on laptops, for development/debugging/ad-hoc use) or as part of CI/CD pipelines,
e.g. in AWS CodePipeline.

## Actions

SnowflakeBuilder supports the following actions:

- **Prepare Environment** - sets up a CI/CD user in Snowflake for the specific environment.  This has already been run
  in each environment and does not need to be run again.
- **Test Secret** - retrieves the credentials of a Snowflake user that are stored in AWS Secrets Manager then
  attempts to connect to Snowflake using these credentials, to ensure they work.
- **Apply Changes** - executes SQL scripts against an environment in Snowflake.
- **Rotate User Keys** - retrieves the credentials of a Snowflake user that are stored in AWS Secrets Manager, creates 
  new RSA keys for the user, sets the keys in Snowflake then updates the secret in AWS Secrets Manager with the new 
  keys.

## More Information

A lot more information about SnowflakeBuilder can be found in the CRUK wiki:
https://wiki.cancerresearchuk.org/confluence/display/BI/Snowflake+and+AWS

You should read the wiki before attempting to use the tool.

## Example Command Lines

This section shows some short command line examples.  Full explanations of the actions and command lines is provided
in the wiki.

The command lines below are split onto multiple lines for readability.  They should be reformatted onto a single line
before executing them.

### Preparing an Environment

**Do not run this command:  It has already been run in each environment so does not need to be run again.**

```
python -m main --prepare-environment --environment dev 
    --snowflake-auth USERNAME_PASSWORD
    --snowflake-user CBAILISS_ACCOUNTADMIN --snowflake-password YOURPASSWORD 
    --snowflake-role ACCOUNTADMIN --snowflake-warehouse NON_PROD_ALL
    --aws-profile crukbidev
```

This action must be executed with one of the following roles/auth methods in Snowflake:

- ACCOUNTADMIN using username and password authentication.
- ACCOUNTADMIN using SSO (though there are currently no CRUK account admins set up via SSO).

Roles such as DEVADMIN, PRODADMIN, etc. are not sufficient, since the CICD user must be granted the 
ACCOUNT_OBJECT_CREATOR role which is owned by the account level SECURITYADMIN.

### Testing Credentials

Testing the CI/CD user in a particular environment:

```
python -m main --test-secret --aws-secret cruk-bi-dev-snowflake-cicd --aws-profile crukbidev
```

Testing the service account for a particular solution in a particular environment:

```
python -m main --test-secret --aws-secret cruk-bi-dev-energy-usage-2-svc-creds --aws-profile crukbidev
```

No Snowflake credentials need to be provided with this command since it uses the credentials read from AWS.

### Applying changes to an Environment

```
python -m main --apply-changes --definitions-path-abs "C:\Python\BIEnergyUsage\BIEnergyUsageDB" --environment dev
    --aws-profile crukbidev
```

This command executes using the CI/CD credentials stored in AWS Secrets Manager for the specified environment (i.e.
the CI/CD credentials that were previously set up using the Prepare Environment action).

### Rotate user keys

This action can be executed using any of the following roles/auth methods:

- ACCOUNTADMIN using username and password authentication.
- {ENV}ADMIN, e.g. DEVADMIN using SSO
- As the Snowflake CICD user in a particular environment.

The examples below show three variations of the same action - rotating the credentials stored in the AWS Secrets 
Manager secret named cruk-bi-dev-snowflake-cicd.  Each variation below uses a different authentication method.

Using username and password to authenticate to Snowflake:

```
python -m main --rotate-secret 
    --snowflake-auth USERNAME_PASSWORD
    --snowflake-user CBAILISS_ACCOUNTADMIN --snowflake-password PWD 
    --snowflake-role ACCOUNTADMIN --rotate-aws-secret cruk-bi-dev-snowflake-cicd
    --aws-profile crukbidev
```

Using SSO to authenticate to Snowflake:

```
python -m main --rotate-secret 
    --snowflake-auth SINGLE_SIGN_ON --snowflake-user "chris.bailiss@cancer.org.uk"
    --snowflake-role DEVADMIN --rotate-aws-secret cruk-bi-dev-snowflake-cicd
    --aws-profile crukbidev
```

Using the credentials stored in a secret in AWS Secrets Manager to authenticate:

```
python -m main --rotate-secret 
    --snowflake-auth AWS_USER_SECRET --snowflake-user "SVC_DEV_SNOWFLAKE_CICD"
    --snowflake-role DEVADMIN 
    --connect-aws-secret cruk-bi-dev-snowflake-cicd 
    --rotate-aws-secret cruk-bi-dev-snowflake-cicd --aws-profile crukbidev
```

## Requirements

### Python

Python 3.10

### Packages

For running the code:

- boto3
- Snowflake connector (see below)

The Snowflake connector can be installed using the following command:

```
pip install -r https://raw.githubusercontent.com/snowflakedb/snowflake-connector-python/v2.7.9/tested_requirements/requirements_310.reqs
pip install snowflake-connector-python==2.7.9
```

For running tests/code checks:

- flake8
- pytest

## Unit Tests

The project has a small number of unit tests defined.  At the current time these are incomplete - and focus on testing
the code in the utilities package only.  The tests can be executed from the PyCharm Terminal pane using simply `pytest`. 

## Setting default web browser

When using SSO with PyCharm, you may encounter issues with Chrome.  Since PyCharm is running under an admin account 
(i.e. not your normal CRUK account) Chrome can be prone to crashing immediately on opening.  If this happens, the 
simplest workaround is to install FireFox under your admin account, then set Firefox as the default browser for your
admin account.  You may be able to do this in the Windows default app settings, but if this proves problematic the
utility/commands linked below can help.  Running the four commands listed below in a command prompt running under
your admin account will set Firefox as the default browser for your admin account.

https://www.winhelponline.com/blog/set-default-browser-file-associations-command-line-windows-10/
http://kolbi.cz/blog/2017/10/25/setuserfta-userchoice-hash-defeated-set-file-type-associations-per-user/

```
SetUserFTA  http FirefoxHTML
SetUserFTA  https FirefoxHTML
SetUserFTA  .htm FirefoxHTML
SetUserFTA  .html FirefoxHTML
```

## TODO

SnowflakeBuilder will be extended shortly to provide a mechanism that will allow rollback if a CI/CD run fails.  We've
had some discussions with Snowflake on this topic so expect more on this soon.

In the meantime, rollback will be completely manual as described in the following section.

## Manual Rollback

When working with SnowflakeBuilder initially, it is helpful to have a rollback script for Snowflake.  This allows 
you to run SnowflakeBuilder multiple times and easily remove the Snowflake objects that it creates.  An example
rollback script is shown below.  The commands in the script are in the reverse order to the order that the scripts
are executed by SnowflakeBuilder (i.e. they work through undoing each change that SnowflakeBuilder made).

```
DROP SCHEMA IF EXISTS DEV_CRUK.BEIS;
DROP DATABASE IF EXISTS DEV_ENERGY_USAGE_2;
DROP INTEGRATION IF EXISTS DEV_ENERGY_USAGE_2;
DROP ROLE IF EXISTS DEV_ENERGY_USAGE_2_READER;
DROP ROLE IF EXISTS DEV_ENERGY_USAGE_2_ADMIN;
DROP USER IF EXISTS SVC_DEV_ENERGY_USAGE_2;
```
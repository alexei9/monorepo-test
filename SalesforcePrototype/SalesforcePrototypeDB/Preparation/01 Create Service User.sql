-- CICD-SCRIPT-TYPE: CREATE_USER
-- CICD-USER-NAME: {SERVICE_USER_NAME}
-- CICD-SECRET-NAME: cruk-bi-{env}-{solution-name}-svc-creds
-- CICD-VAR: SOLUTION_NAME
-- CICD-VAR: solution-name
-- CICD-VAR: ENV
-- CICD-VAR: env
-- CICD-VAR: SERVICE_USER_NAME
-- CICD-VAR: ADMIN_ROLE_NAME
-- CICD-VAR: USER_PUBLIC_KEY
-- CICD-VAR: WAREHOUSE_NAME

-- Unfortunately, there is no programmatic way (without being SECURITYADMIN) to check whether a user exists.
-- So we must adopt the sub-optimal approach of always trying to create the user and assuming any error means
-- that the user already exists.
-- Whilst not ideal, we can live with this since it only affects the one-off preparation process when a new
-- solution is created.

BEGIN
    USE ROLE ACCOUNT_OBJECT_CREATOR;
    USE WAREHOUSE {WAREHOUSE_NAME};

    CREATE USER {SERVICE_USER_NAME} 
        LOGIN_NAME = '{SERVICE_USER_NAME}', 
        DISPLAY_NAME = '{SERVICE_USER_NAME} ',
        STATEMENT_QUEUED_TIMEOUT_IN_SECONDS = 300,
        STATEMENT_TIMEOUT_IN_SECONDS = 300,
        RSA_PUBLIC_KEY='{USER_PUBLIC_KEY}';
    ALTER USER {SERVICE_USER_NAME}  SET DEFAULT_ROLE = '{ADMIN_ROLE_NAME}', DEFAULT_WAREHOUSE = '{WAREHOUSE_NAME}';
    GRANT OWNERSHIP ON USER {SERVICE_USER_NAME} TO ROLE {ENV}SECURITYADMIN;
    RETURN 1; --> register credentials in AWS Secrets Manager
EXCEPTION
    WHEN STATEMENT_ERROR THEN 
        RETURN 0;  --> assume user already exists, do not set credentials in AWS Secrets Manager 
    WHEN OTHER THEN
        RETURN 0;  --> assume user already exists, do not set credentials in AWS Secrets Manager 
END;
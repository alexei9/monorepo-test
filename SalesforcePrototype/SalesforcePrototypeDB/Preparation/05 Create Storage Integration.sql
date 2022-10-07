-- CICD-SCRIPT-TYPE: CREATE_INTEGRATION
-- CICD-INTEGRATION-NAME: {STORAGE_INTEGRATION_NAME}
-- CICD-VAR: solution-name
-- CICD-VAR: ENV
-- CICD-VAR: env
-- CICD-VAR: ADMIN_ROLE_NAME
-- CICD-VAR: WAREHOUSE_NAME
-- CICD-VAR: STORAGE_INTEGRATION_NAME
-- CICD-VAR: AWS_STORAGE_ROLE_ARN
-- CICD-VAR: EXISTING_INTEGRATION_COUNT

DECLARE 
    object_count INT DEFAULT {EXISTING_INTEGRATION_COUNT};
BEGIN
    USE ROLE ACCOUNT_OBJECT_CREATOR;
    USE WAREHOUSE {WAREHOUSE_NAME};

    IF (object_count = 0) THEN
        CREATE STORAGE INTEGRATION {STORAGE_INTEGRATION_NAME}
          TYPE = EXTERNAL_STAGE
          STORAGE_PROVIDER = S3
          ENABLED = TRUE
          STORAGE_AWS_ROLE_ARN = '{AWS_STORAGE_ROLE_ARN}'
          --STORAGE_ALLOWED_LOCATIONS = ('s3://cruk-bi-{env}-{solution-name}/');
          STORAGE_ALLOWED_LOCATIONS = ('s3://ageorge-dev-salesforce-prototype/');

        GRANT OWNERSHIP ON INTEGRATION {STORAGE_INTEGRATION_NAME} TO ROLE {ENV}SYSADMIN;
    END IF;

    USE ROLE {ENV}ADMIN;

    GRANT USAGE ON INTEGRATION {STORAGE_INTEGRATION_NAME} TO ROLE {ADMIN_ROLE_NAME};
END;
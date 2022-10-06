-- CICD-VAR: SOLUTION_NAME
-- CICD-VAR: solution-name
-- CICD-VAR: ENV
-- CICD-VAR: env
-- CICD-VAR: ADMIN_ROLE_NAME
-- CICD-VAR: IMPLEMENTATION_DB_NAME
-- CICD-VAR: WAREHOUSE_NAME
-- CICD-VAR: STORAGE_INTEGRATION_NAME

BEGIN
    USE ROLE {ENV}ADMIN;
    USE WAREHOUSE {WAREHOUSE_NAME};
    USE DATABASE {IMPLEMENTATION_DB_NAME};

    CREATE STAGE SALESFORCE_LOAD.S3_STAGE
        STORAGE_INTEGRATION = {STORAGE_INTEGRATION_NAME} URL = 's3://cruk-bi-{env}-{solution-name}/';

    GRANT OWNERSHIP ON STAGE SALESFORCE_LOAD.S3_STAGE TO ROLE {ADMIN_ROLE_NAME};

    GRANT USAGE ON STAGE SALESFORCE_LOAD.S3_STAGE TO ROLE {ADMIN_ROLE_NAME};
END;
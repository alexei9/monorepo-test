-- CICD-VAR: ENV
-- CICD-VAR: ADMIN_ROLE_NAME
-- CICD-VAR: PRESENTATION_DB_NAME
-- CICD-VAR: WAREHOUSE_NAME

BEGIN
    USE ROLE {ENV}ADMIN;
    USE WAREHOUSE {WAREHOUSE_NAME};
    USE DATABASE {PRESENTATION_DB_NAME};

    GRANT USAGE ON DATABASE {PRESENTATION_DB_NAME} TO ROLE {ADMIN_ROLE_NAME};

    CREATE SCHEMA SALESFORCE WITH MANAGED ACCESS;

    GRANT OWNERSHIP ON SCHEMA SALESFORCE TO ROLE {ADMIN_ROLE_NAME};

    GRANT ALL ON SCHEMA SALESFORCE TO ROLE {ADMIN_ROLE_NAME};
END;
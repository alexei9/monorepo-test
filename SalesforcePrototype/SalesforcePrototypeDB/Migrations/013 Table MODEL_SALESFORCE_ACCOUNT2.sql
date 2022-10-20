-- CICD-VAR: ADMIN_ROLE_NAME
-- CICD-VAR: IMPLEMENTATION_DB_NAME
-- CICD-VAR: WAREHOUSE_NAME

BEGIN
    USE ROLE {ADMIN_ROLE_NAME};
    USE WAREHOUSE {WAREHOUSE_NAME};
    USE DATABASE {IMPLEMENTATION_DB_NAME};

    CREATE OR REPLACE TABLE SALESFORCE_MODEL.SALESFORCE_ACCOUNT
    (
        ID       VARCHAR(100),
        NAME                VARCHAR(100),
        INDUSTRY            VARCHAR(50),
        NUMBEROFEMPLOYEES   NUMBER
    );

    GRANT OWNERSHIP ON TABLE SALESFORCE_MODEL.SALESFORCE_ACCOUNT TO ROLE {ADMIN_ROLE_NAME};
END;

-- CICD-SCRIPT-TYPE: CREATE_ROLE
-- CICD-ROLE-NAME: {READER_ROLE_NAME}
-- CICD-VAR: ENV
-- CICD-VAR: READER_ROLE_NAME
-- CICD-VAR: WAREHOUSE_NAME
-- CICD-VAR: EXISTING_ROLE_COUNT

DECLARE 
    object_count INT DEFAULT {EXISTING_ROLE_COUNT};
BEGIN
    USE ROLE ACCOUNT_OBJECT_CREATOR;
    USE WAREHOUSE {WAREHOUSE_NAME};

    IF (object_count = 0) THEN
        CREATE ROLE {READER_ROLE_NAME};
        GRANT OWNERSHIP ON ROLE {READER_ROLE_NAME} TO ROLE {ENV}SECURITYADMIN;
    END IF;

    USE ROLE {ENV}ADMIN;
    GRANT ROLE {READER_ROLE_NAME} TO ROLE {ENV}SYSADMIN;
    GRANT ROLE {READER_ROLE_NAME} TO ROLE "BI TEAM MEMBER";
END;
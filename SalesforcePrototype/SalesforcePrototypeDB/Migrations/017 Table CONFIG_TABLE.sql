-- CICD-VAR: ADMIN_ROLE_NAME
-- CICD-VAR: IMPLEMENTATION_DB_NAME
-- CICD-VAR: WAREHOUSE_NAME

BEGIN
    USE ROLE {ADMIN_ROLE_NAME};
    USE WAREHOUSE {WAREHOUSE_NAME};
    USE DATABASE {IMPLEMENTATION_DB_NAME};

    CREATE OR REPLACE TABLE CONFIG.CONFIG_TABLE
    (
        SALESFORCEOBJECTNAME        VARCHAR(100),
        ENABLED                     BOOLEAN,
        SEQUENCENUMBER              INT,
        SELECTCOLUMNS               VARIANT,
        SENSITIVECOLUMNNAMES        VARCHAR(10000),
        PRIMARYKEYCOLUMNNAME        VARCHAR(100),
        PARTITIONCOLUMNNAME         VARCHAR(100),
        PARTITIONRANGES             VARCHAR(1000),
        INCREMENTALCOLUMNNAME       VARCHAR(100),
        INCREMENTALPROCESSTYPE      VARCHAR(100),
        LASTINCREMENTALVALUEINT     INT,
        LASTINCREMENTALVALUEDT      TIMESTAMP_TZ,
        WIPINCREMENTALVALUEINT      INT,
        WIPINCREMENTALVALUEDT       TIMESTAMP_TZ,
        SNOWFLAKELOADINGTABLENAME   VARCHAR(100),
        SNOWFLAKETARGETTABLENAME    VARCHAR(100),
        SALESFORCEAPI               VARCHAR(100),
        IGNOREMISSINGSOURCECOLUMNS  BOOLEAN,
        EXTRACTTIMEOUTSECONDS       INT,
        LOADTIMEOUTSECONDS          INT,
        MERGETIMEOUTSECONDS         INT
    );

    GRANT OWNERSHIP ON TABLE CONFIG.CONFIG_TABLE TO ROLE {ADMIN_ROLE_NAME};
END;

-- CICD-VAR: ADMIN_ROLE_NAME
-- CICD-VAR: IMPLEMENTATION_DB_NAME
-- CICD-VAR: PRESENTATION_DB_NAME
-- CICD-VAR: WAREHOUSE_NAME

BEGIN
    USE ROLE {ADMIN_ROLE_NAME};
    USE WAREHOUSE {WAREHOUSE_NAME};
    USE DATABASE {PRESENTATION_DB_NAME};

    CREATE OR REPLACE VIEW SALESFORCE.ENERGY_USAGE3
    AS
    SELECT EnergyType, YEAR, PostCode, MeterCount, TotalConsumption
    FROM {IMPLEMENTATION_DB_NAME}.SALESFORCE_LOAD.ENERGY_USAGE3;

    GRANT OWNERSHIP ON VIEW SALESFORCE.ENERGY_USAGE3 TO ROLE {ADMIN_ROLE_NAME};
END;
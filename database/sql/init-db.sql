-- ==============================================================================
-- SURAKSHA AI - INITIAL DATABASE SCHEMAS AND EXTENSIONS
-- ==============================================================================

-- 1. Enable PostGIS Extension
-- CREATE EXTENSION IF NOT EXISTS postgis;
-- CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- 2. Define Primary Schemas
-- CREATE SCHEMA IF NOT EXISTS raw_intelligence;
-- CREATE SCHEMA IF NOT EXISTS core_records;
-- CREATE SCHEMA IF NOT EXISTS analytical_layers;

-- 3. Database structures will be created via SQLAlchemy declarative mapping
--    and migration scripts compiled under migrations/ using Alembic.

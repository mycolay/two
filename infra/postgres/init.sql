-- Si nano Factory — initial Postgres setup
-- Mounted into postgres container at /docker-entrypoint-initdb.d/01_init.sql
-- Runs once on first container creation.

-- Schemas:
--   factory_meta : NanoparticleSpec, runs, recipes (Module 1, 4)
--   molecule_cache : InChIKey-keyed DFT/xTB cache (FR-34, §5.4)
--   prefect : auto-created by Prefect server (don't touch)
--   mlflow : auto-created by MLflow server (don't touch)

CREATE SCHEMA IF NOT EXISTS factory_meta;
CREATE SCHEMA IF NOT EXISTS molecule_cache;

GRANT ALL ON SCHEMA factory_meta TO factory;
GRANT ALL ON SCHEMA molecule_cache TO factory;

-- Useful extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- for InChIKey similarity search later

-- Note: real tables are managed by SQLAlchemy/Alembic migrations.
-- This file only sets up schemas and extensions.

\echo 'Si nano Factory: schemas factory_meta + molecule_cache created'

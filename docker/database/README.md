# PostgreSQL with PostGIS Database Container

This directory contains resources for configuring the PostgreSQL instance. 

## Base Image
We use `postgis/postgis:15-3.3` which extends official PostgreSQL 15 image by adding support for PostGIS spatial features.

## Spatial Query Configuration
- Geometries use spatial coordinates matching Karnataka boundaries (SRID 4326 - WGS 84, or SRID 32643 - UTM Zone 43N for meter-based distance calculations).
- PostGIS extensions are enabled automatically:
  - `postgis`
  - `postgis_topology`

## Initialization Scripts
Initialization scripts in `../../database/sql/` are automatically mapped to `/docker-entrypoint-initdb.d/` in the container.
- `init-db.sql`: Creates extensions, creates primary schemas, and provisions users/permissions.

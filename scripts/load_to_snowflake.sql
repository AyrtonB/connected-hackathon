-- Load exported Parquet files into Snowflake tables
-- Prerequisites:
--   1. Run: uv run python scripts/export_to_snowflake.py  (exports Postgres -> Parquet)
--   2. Run: scripts/create_tables.sql                     (creates target tables)
--
-- This script stages the Parquet files and loads them via COPY INTO.

USE DATABASE MET_SCRATCH;
USE SCHEMA THAMES;

-- Create a dedicated internal stage for the load
CREATE STAGE IF NOT EXISTS LOAD_STAGE
    FILE_FORMAT = (TYPE = PARQUET);

----------------------------------------------------------------------
-- PUT files (run these from SnowSQL / Snowflake CLI, not Snowsight)
-- Adjust the path to wherever `scripts/exports/` lives on your machine.
----------------------------------------------------------------------
-- PUT 'file:///path/to/connected-hackathon/scripts/exports/stations.parquet'             @LOAD_STAGE/stations AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
-- PUT 'file:///path/to/connected-hackathon/scripts/exports/station_types.parquet'        @LOAD_STAGE/station_types AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
-- PUT 'file:///path/to/connected-hackathon/scripts/exports/station_statuses.parquet'     @LOAD_STAGE/station_statuses AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
-- PUT 'file:///path/to/connected-hackathon/scripts/exports/measures.parquet'             @LOAD_STAGE/measures AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
-- PUT 'file:///path/to/connected-hackathon/scripts/exports/readings.parquet'             @LOAD_STAGE/readings AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
-- PUT 'file:///path/to/connected-hackathon/scripts/exports/river_links.parquet'          @LOAD_STAGE/river_links AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
-- PUT 'file:///path/to/connected-hackathon/scripts/exports/catchment_boundaries.parquet' @LOAD_STAGE/catchment_boundaries AUTO_COMPRESS=FALSE OVERWRITE=TRUE;

----------------------------------------------------------------------
-- COPY INTO: load each table from staged Parquet
----------------------------------------------------------------------

-- Stations (derive GEOGRAPHY point from lat/long)
COPY INTO STATIONS (ID, LABEL, RIVER_NAME, LAT, LONG, NRFA_STATION_ID, LOCATION)
FROM (
    SELECT
        $1:id::VARCHAR,
        $1:label::VARCHAR,
        $1:river_name::VARCHAR,
        $1:lat::FLOAT,
        $1:long::FLOAT,
        $1:nrfa_station_id::VARCHAR,
        TRY_TO_GEOGRAPHY('POINT(' || $1:long::VARCHAR || ' ' || $1:lat::VARCHAR || ')')
    FROM @LOAD_STAGE/stations
)
FILE_FORMAT = (TYPE = PARQUET)
MATCH_BY_COLUMN_NAME = NONE;

-- Station types
COPY INTO STATION_TYPES
FROM @LOAD_STAGE/station_types
FILE_FORMAT = (TYPE = PARQUET)
MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE;

-- Station statuses
COPY INTO STATION_STATUSES
FROM @LOAD_STAGE/station_statuses
FILE_FORMAT = (TYPE = PARQUET)
MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE;

-- Measures
COPY INTO MEASURES
FROM @LOAD_STAGE/measures
FILE_FORMAT = (TYPE = PARQUET)
MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE;

-- Readings
COPY INTO READINGS (MEASURE_ID, DATE_TIME, VALUE, QUALITY, STATION_ID, PARAMETER, PERIOD, PERIOD_NAME, VALUE_TYPE, UNIT_NAME)
FROM @LOAD_STAGE/readings
FILE_FORMAT = (TYPE = PARQUET)
MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE;

-- River links (parse WKT geometry string into GEOGRAPHY)
COPY INTO RIVER_LINKS (ID, WATERCOURSE_NAME, WATERCOURSE_NAME_ALTERNATIVE, FORM, FLOW_DIRECTION, FICTITIOUS, LENGTH, START_NODE, END_NODE, GEOMETRY)
FROM (
    SELECT
        $1:id::VARCHAR,
        $1:watercourse_name::VARCHAR,
        $1:watercourse_name_alternative::VARCHAR,
        $1:form::VARCHAR,
        $1:flow_direction::VARCHAR,
        $1:fictitious::VARCHAR,
        $1:length::FLOAT,
        $1:start_node::VARCHAR,
        $1:end_node::VARCHAR,
        TRY_TO_GEOGRAPHY($1:geometry_wkt::VARCHAR)
    FROM @LOAD_STAGE/river_links
)
FILE_FORMAT = (TYPE = PARQUET)
MATCH_BY_COLUMN_NAME = NONE;

-- Catchment boundaries (parse GeoJSON string into GEOGRAPHY)
COPY INTO CATCHMENT_BOUNDARIES (NRFA_STATION_ID, AREA_KM2, GEOMETRY)
FROM (
    SELECT
        $1:nrfa_station_id::VARCHAR,
        $1:area_km2::FLOAT,
        TRY_TO_GEOGRAPHY($1:geometry_geojson::VARCHAR)
    FROM @LOAD_STAGE/catchment_boundaries
)
FILE_FORMAT = (TYPE = PARQUET)
MATCH_BY_COLUMN_NAME = NONE;

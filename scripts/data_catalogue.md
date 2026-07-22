# Fried Fish — Data Catalogue

> **Database:** `MET_SCRATCH`
> **Project:** Thames Ecosystem & Climate Risk (Connected Places Catapult / Met Office / Snowflake Hackathon, July 2026)

All project data lives in a single database with four domain schemas plus read-only Met Office data shares.

---

## Schema Overview

| Schema | Domain | Tables | Description |
|--------|--------|--------|-------------|
| `THAMES` | River & hydrology | 10 tables, 2 views | River network, EA monitoring stations, readings, catchments |
| `CLIMATE` | Meteorology | 7 tables | Met Office temperature & precipitation timeseries, catchment-aggregated climate, water temp forecasts |
| `FISH` | Ecology | 7 tables | Fish surveys, thermal tolerance, population simulations |
| `DOCS` | Documents & RAG | 2 tables | Parsed source documents and text chunks |

---

## MET_SCRATCH.THAMES — River Geography & Hydrology

### STATIONS (63 rows)
EA Hydrology API monitoring stations: temperature/water-quality sensors plus river flow gauges along the Thames corridor. 27 stations carry an NRFA ID; 12 of those join to a CAMELS-GB catchment boundary.

| Column | Type | Description |
|--------|------|-------------|
| ID | TEXT (PK) | EA station URI |
| LABEL | TEXT | Human-readable name |
| RIVER_NAME | TEXT | e.g. "River Thames" |
| LAT | FLOAT | Latitude |
| LONG | FLOAT | Longitude |
| NRFA_STATION_ID | TEXT | Join key to CATCHMENT_BOUNDARIES |
| LOCATION | GEOGRAPHY | Point geometry (derived from lat/long) |

### STATION_TYPES (145 rows)
One row per (station, type URI). A station can carry multiple types (e.g. RiverStation + WithTemperature).

| Column | Type | Description |
|--------|------|-------------|
| STATION_ID | TEXT (PK, FK → STATIONS) | |
| TYPE_URI | TEXT (PK) | e.g. `http://...#WithTemperature` |

### STATION_STATUSES (35 rows)
One row per (station, status URI). Some stations report multiple statuses simultaneously.

| Column | Type | Description |
|--------|------|-------------|
| STATION_ID | TEXT (PK, FK → STATIONS) | |
| STATUS_URI | TEXT (PK) | e.g. `statusActive`, `statusSuspended` |

### MEASURES (265 rows)
Timeseries dimension — one row per sensor/parameter a station provides.

| Column | Type | Description |
|--------|------|-------------|
| ID | TEXT (PK) | Measure URI |
| LABEL | TEXT | Human-readable label |
| PARAMETER | TEXT | e.g. TEMPERATURE, FLOW, LEVEL |
| PARAMETER_NAME | TEXT | Full parameter name |
| PERIOD | NUMBER | Sampling period in seconds (900=15min, 86400=daily) |
| PERIOD_NAME | TEXT | e.g. "15 min", "daily" |
| VALUE_TYPE | TEXT | mean, min, max, instantaneous |
| UNIT_NAME | TEXT | e.g. "deg C", "m3/s", "mAOD" |
| STATION_ID | TEXT (FK → STATIONS) | |

### READINGS (3,314,678 rows)
Denormalised time-series observations. Clustered by `(STATION_ID, DATE_TIME)`.

| Column | Type | Description |
|--------|------|-------------|
| MEASURE_ID | TEXT (PK) | Which timeseries |
| DATE_TIME | TIMESTAMP (PK) | Observation time |
| VALUE | FLOAT | Measured value |
| QUALITY | TEXT | Quality flag |
| STATION_ID | TEXT (FK → STATIONS) | |
| PARAMETER | TEXT | Denormalised from MEASURES |
| PERIOD | NUMBER | Denormalised from MEASURES |
| PERIOD_NAME | TEXT | Denormalised from MEASURES |
| VALUE_TYPE | TEXT | Denormalised from MEASURES |
| UNIT_NAME | TEXT | Denormalised from MEASURES |

### RIVER_LINKS (193,040 rows)
Full OS Open Rivers (GB) watercourse network with PostGIS-style GEOGRAPHY linestrings.

| Column | Type | Description |
|--------|------|-------------|
| ID | TEXT (PK) | OS link ID |
| WATERCOURSE_NAME | TEXT | Primary name |
| WATERCOURSE_NAME_ALTERNATIVE | TEXT | Secondary name |
| FORM | TEXT | Watercourse form |
| FLOW_DIRECTION | TEXT | |
| FICTITIOUS | TEXT | |
| LENGTH | FLOAT | Metres |
| START_NODE | TEXT | Network topology |
| END_NODE | TEXT | Network topology |
| GEOMETRY | GEOGRAPHY | LINESTRING (WGS84) |

### CATCHMENT_BOUNDARIES (671 rows)
CAMELS-GB upstream drainage-area polygons. Join to STATIONS via NRFA_STATION_ID.

| Column | Type | Description |
|--------|------|-------------|
| NRFA_STATION_ID | TEXT (PK) | NRFA gauge ID |
| AREA_KM2 | FLOAT | Catchment area |
| GEOMETRY | GEOGRAPHY | Polygon/MultiPolygon (WGS84) |

### PSEUDO_SITES_GEO (3,681 rows)
Met Office pseudo-observation sites with GEOGRAPHY points.

| Column | Type | Description |
|--------|------|-------------|
| SITE_ID | NUMBER | Met Office site ID |
| SITE_NAME | TEXT | e.g. "OXFORD" |
| LATITUDE | FLOAT | |
| LONGITUDE | FLOAT | |
| LOCATION | GEOGRAPHY | Point geometry |

### THAMES_GEOM (1 row)
Single pre-computed Thames river GEOGRAPHY object (union of all Thames links).

| Column | Type | Description |
|--------|------|-------------|
| THAMES | GEOGRAPHY | Full river geometry |

### THAMES_SITE_DISTANCE (3,681 rows)
Pre-computed distance from each Met Office site to the Thames.

| Column | Type | Description |
|--------|------|-------------|
| SITE_ID | NUMBER | Met Office site ID |
| SITE_NAME | TEXT | |
| LATITUDE | FLOAT | |
| LONGITUDE | FLOAT | |
| DIST_M | FLOAT | Distance to Thames in metres |

### CATCHMENT_SITE_MAP (73 rows)
Mapping between EA stations with NRFA catchments and nearby Met Office sites.

| Column | Type | Description |
|--------|------|-------------|
| STATION_ID | TEXT | EA station ID |
| STATION_LABEL | TEXT | |
| RIVER_NAME | TEXT | |
| NRFA_STATION_ID | TEXT | |
| AREA_KM2 | FLOAT | |
| SITE_ID | NUMBER | Nearest Met Office site |
| SITE_NAME | TEXT | |

### Views

- **RIVER_THAMES** — Thames links filtered by name (376 rows)
- **RIVER_THAMES_CONNECTED** — Thames + gap-bridging unnamed links via recursive CTE (~527 rows)

---

## MET_SCRATCH.CLIMATE — Met Office Temperature & Precipitation

### THAMES_TEMPERATURE_TIMESERIES (15,596,736 rows)
Hourly air temperature from 116 Met Office pseudo-obs sites within 5km of the Thames, 2011–2026.

| Column | Type | Description |
|--------|------|-------------|
| SITE_ID | NUMBER | Met Office site ID |
| SITE_NAME | TEXT | |
| LATITUDE | FLOAT | |
| LONGITUDE | FLOAT | |
| DIST_TO_RIVER_M | FLOAT | Distance to Thames |
| VALIDITY_TIME | TIMESTAMP | Observation hour |
| SCREEN_TEMPERATURE_C | NUMBER | Air temperature at 1.5m |
| SCREEN_TEMP_MAX_1H_C | NUMBER | Max in the hour |
| SCREEN_TEMP_MIN_1H_C | NUMBER | Min in the hour |
| FEELS_LIKE_TEMPERATURE_C | NUMBER | Feels-like temperature |
| SURFACE_TEMPERATURE_C | NUMBER | Surface/ground temperature |

### THAMES_PRECIPITATION_TIMESERIES (15,596,736 rows)
Hourly precipitation from the same 116 sites, matching the temperature table 1:1 on `(SITE_ID, VALIDITY_TIME)`.

| Column | Type | Description |
|--------|------|-------------|
| SITE_ID | NUMBER | Met Office site ID |
| SITE_NAME | TEXT | |
| LATITUDE | FLOAT | |
| LONGITUDE | FLOAT | |
| DIST_TO_RIVER_M | FLOAT | |
| VALIDITY_TIME | TIMESTAMP | Observation hour |
| RAINFALL_MM_1H | NUMBER | Hourly rainfall |
| SNOWFALL_MM_1H | NUMBER | Hourly snowfall |
| SNOW_DEPTH_CM | NUMBER | Snow depth |
| RELATIVE_HUMIDITY_PCT | NUMBER | Relative humidity |

### THAMES_WATER_TEMPERATURE_DAILY (1,825 rows)
Derived daily mean water temperature for the Thames (from EA readings).

| Column | Type | Description |
|--------|------|-------------|
| date | TIMESTAMP | Day |
| water_temp_c | FLOAT | Mean water temperature |

### THAMES_WATER_TEMPERATURE_FORECAST (7 rows)
Short-range water temperature forecast (next 7 days).

| Column | Type | Description |
|--------|------|-------------|
| date | TIMESTAMP | Forecast day |
| forecast_water_temp_c | FLOAT | Predicted water temperature |

### THAMES_FORECAST_TRAINING_DATA (28 rows)
Training data for the water temperature forecast model.

| Column | Type | Description |
|--------|------|-------------|
| date | TIMESTAMP | Day |
| water_temp_c_actual_or_synthetic | FLOAT | Target variable |
| air_temp_c | FLOAT | Feature: air temperature |
| precip_mm | FLOAT | Feature: precipitation |

### CATCHMENT_PRECIPITATION_TIMESERIES (~1.48M rows)
Hourly precipitation spatially averaged over all Met Office pseudo-obs sites falling within each of 11 Thames-area upstream catchment boundary polygons. Covers 2011-03-16 to 2026-07-21.

The 11 catchments (by NRFA_STATION_ID): Kingston (39001, 9931 km²), Windsor (39072, 7125 km²), Cassington/Evenlode (39034, 427 km²), Newbridge/Windrush (39006, 362 km²), Abingdon/Ock (39081, 234 km²), Pangbourne/Pang (39027, 176 km²), Bourne End Hedsor/Wye (39023, 134 km²), Cerney Wick/Churn (39008, 1627 km²), Water Eaton/Ray (39087, 82 km²), Lechlade/Leach (39042, 78 km²), Kingston Hogsmill (39012, 73 km²).

| Column | Type | Description |
|--------|------|-------------|
| NRFA_STATION_ID | TEXT | Catchment identifier (joins to STATIONS and CATCHMENT_BOUNDARIES) |
| AREA_KM2 | FLOAT | Catchment area |
| VALIDITY_TIME | TIMESTAMP | Observation hour |
| SITES_REPORTING | NUMBER | Pseudo-obs sites that reported that hour |
| MEAN_RAINFALL_MM_1H | FLOAT | Spatial average rainfall across sites in catchment |
| TOTAL_RAINFALL_MM_1H | FLOAT | Sum across all sites (proxy for catchment total) |
| MAX_RAINFALL_MM_1H | FLOAT | Hotspot: max rainfall at any single site |
| MEAN_SNOWFALL_MM_1H | FLOAT | Spatial average snowfall |

### CATCHMENT_TEMPERATURE_TIMESERIES (~1.48M rows)
Hourly temperature spatially averaged over the same 11 catchment polygons, same temporal coverage as CATCHMENT_PRECIPITATION_TIMESERIES. Joins 1:1 on `(NRFA_STATION_ID, VALIDITY_TIME)`.

| Column | Type | Description |
|--------|------|-------------|
| NRFA_STATION_ID | TEXT | Catchment identifier |
| AREA_KM2 | FLOAT | Catchment area |
| VALIDITY_TIME | TIMESTAMP | Observation hour |
| SITES_REPORTING | NUMBER | Pseudo-obs sites that reported |
| MEAN_AIR_TEMP_C | FLOAT | Spatial average air temperature (1.5m) |
| MAX_AIR_TEMP_C | FLOAT | Max across sites |
| MIN_AIR_TEMP_C | FLOAT | Min across sites |
| MEAN_SURFACE_TEMP_C | FLOAT | Spatial average surface/ground temperature |
| MEAN_FEELS_LIKE_TEMP_C | FLOAT | Spatial average feels-like temperature |

---

## MET_SCRATCH.FISH — Fish Ecology & Population Modelling

### THAMES_10 (10 rows)
Top 10 Thames fish species with thermal tolerance bands from literature.

| Column | Type | Description |
|--------|------|-------------|
| SPECIES_RANK | NUMBER | Rank by Thames prevalence |
| COMMON_NAME | TEXT | e.g. "Roach", "Bleak" |
| SCIENTIFIC_NAME | TEXT | |
| SPECIES_GROUP | TEXT | |
| THAMES_REACH | TEXT | Where in the Thames |
| OPTIMUM_TEMP_MIN_C | NUMBER | Lower optimum bound |
| OPTIMUM_TEMP_MAX_C | NUMBER | Upper optimum bound |
| STRESS_TEMP_MAX_C | NUMBER | Thermal stress onset |
| LETHAL_TEMP_MAX_C | NUMBER | Lethal temperature |
| LETHAL_METRIC | TEXT | CTmax, LT50, etc. |
| VALUE_BASIS | TEXT | Lab/field |
| THERMAL_SOURCE | TEXT | Citation |
| THERMAL_SOURCE_URL | TEXT | Source URL |
| NOTES | TEXT | |

### FW_FISH_COUNTS (368,779 rows)
EA freshwater fish survey counts (electrofishing results, multi-year).

| Column | Type | Description |
|--------|------|-------------|
| SITE_ID | NUMBER | Survey site |
| SITE_NAME | TEXT | |
| EVENT_DATE | TEXT | Survey date |
| EVENT_DATE_YEAR | NUMBER | Year |
| SPECIES_NAME | TEXT | Common name |
| LATIN_NAME | TEXT | Scientific name |
| ALL_RUNS | NUMBER | Total count across runs |
| SURVEY_AREA | NUMBER | Surveyed area (m²) |
| GEO_WATERBODY | TEXT | Waterbody name |
| REGION | TEXT | EA region |
| *(+ 38 more columns)* | | Survey metadata, run counts, density estimates |

### FW_FISH_SITES (16,819 rows)
Fish survey site locations with grid references.

| Column | Type | Description |
|--------|------|-------------|
| SITE_ID | NUMBER | |
| NEW_AREA_NAME | TEXT | EA area |
| SITE_RANKED_NGR | TEXT | National Grid Reference |
| SITE_RANKED_EASTING | NUMBER | |
| SITE_RANKED_NORTHING | NUMBER | |
| N_SURVEYS | NUMBER | Total surveys at site |
| FIRST_SURVEY | TEXT | |
| LAST_SURVEY | TEXT | |

### TAXON_INFO (28,556 rows)
Species taxonomy reference (all freshwater taxa, not just fish).

| Column | Type | Description |
|--------|------|-------------|
| TAXON_NAME | TEXT | |
| PREFERRED_TAXON_NAME | TEXT | Accepted name |
| TAXON_RANK | TEXT | Species/genus/family |
| TAXON_GROUP_NAME | TEXT | e.g. "fish" |
| NON_NATIVE_SP | BOOLEAN | |
| PROTECTED_TAXA | BOOLEAN | |
| *(+ 10 more columns)* | | TVKs, sort codes, parent taxa |

### THERMAL_TOLERANCE (3,257 rows)
Literature thermal tolerance values for freshwater species (broader than just Thames).

| Column | Type | Description |
|--------|------|-------------|
| SPECIES_NAME | TEXT | |
| TOLERANCE_TYPE | TEXT | |
| TOLERANCE_DESCRIPTION | TEXT | |
| TOLERANCE_MEASURE | TEXT | CTmax, LT50, etc. |
| TOLERANCE_VALUE | FLOAT | Temperature (°C) |
| ACCLIMATION_TEMP_C | FLOAT | Lab acclimation temp |
| MAX_OR_MIN | TEXT | Upper or lower tolerance |
| CT_OR_LT | TEXT | Critical or lethal |
| *(+ 9 more columns)* | | Taxonomy, references |

### THAMES_FISH_POPULATION_SIMULATION (54,750 rows)
Daily population simulation under climate scenarios (baseline, +3°C, +5°C).

| Column | Type | Description |
|--------|------|-------------|
| day | NUMBER | Simulation day |
| population | NUMBER | Population count |
| temp | FLOAT | Temperature that day |
| avg_thermal_tol | FLOAT | Mean thermal tolerance of survivors |
| thermal_deaths | NUMBER | Deaths from heat |
| births | NUMBER | Births that day |
| species | TEXT | Which species |
| scenario | TEXT | baseline, +3C, +5C |

### THAMES_FISH_POPULATION_SUMMARY (30 rows)
Summary outcomes per species per scenario.

| Column | Type | Description |
|--------|------|-------------|
| species | TEXT | |
| scenario | TEXT | baseline, +3C, +5C |
| stress_c | NUMBER | Stress temperature threshold |
| lethal_c | FLOAT | Lethal temperature threshold |
| final_pop | NUMBER | End-of-simulation population |
| thermal_deaths | NUMBER | Total thermal deaths |
| thermal_tol | FLOAT | Final mean thermal tolerance |

---

## MET_SCRATCH.DOCS — Documents & RAG

### PARSED_DOCS (2 rows)
Source documents parsed for text extraction.

| Column | Type | Description |
|--------|------|-------------|
| FILE_PATH | TEXT | Stage path |
| FILE_SIZE | NUMBER | Bytes |
| LAST_MODIFIED | TIMESTAMP_TZ | |
| DOC_TEXT | TEXT | Full extracted text |

### DOC_CHUNKS (399 rows)
Chunked document text for retrieval-augmented generation.

| Column | Type | Description |
|--------|------|-------------|
| FILE_PATH | TEXT | Source document |
| CHUNK_INDEX | NUMBER | Chunk sequence |
| CHUNK_TEXT | TEXT | Text content |
| DOC_TITLE | TEXT | Document title |

---

## Key Join Patterns

```sql
-- Station → its readings
THAMES.STATIONS.ID = THAMES.READINGS.STATION_ID

-- Station → its measures (timeseries metadata)
THAMES.STATIONS.ID = THAMES.MEASURES.STATION_ID

-- Station → catchment boundary polygon
THAMES.STATIONS.NRFA_STATION_ID = THAMES.CATCHMENT_BOUNDARIES.NRFA_STATION_ID

-- Station → catchment-aggregated precipitation history
THAMES.STATIONS.NRFA_STATION_ID = CLIMATE.CATCHMENT_PRECIPITATION_TIMESERIES.NRFA_STATION_ID

-- Station → catchment-aggregated temperature history
THAMES.STATIONS.NRFA_STATION_ID = CLIMATE.CATCHMENT_TEMPERATURE_TIMESERIES.NRFA_STATION_ID

-- Catchment precip + temp (1:1 hourly match)
CLIMATE.CATCHMENT_PRECIPITATION_TIMESERIES.NRFA_STATION_ID = CLIMATE.CATCHMENT_TEMPERATURE_TIMESERIES.NRFA_STATION_ID
  AND .VALIDITY_TIME = .VALIDITY_TIME

-- Site-level temperature + precipitation (1:1 hourly match)
CLIMATE.THAMES_TEMPERATURE_TIMESERIES.SITE_ID = CLIMATE.THAMES_PRECIPITATION_TIMESERIES.SITE_ID
  AND .VALIDITY_TIME = .VALIDITY_TIME

-- Met site → nearest EA station (spatial)
SELECT s.*, ps.*
FROM THAMES.STATIONS s
CROSS JOIN THAMES.PSEUDO_SITES_GEO ps
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY s.ID ORDER BY ST_DISTANCE(s.LOCATION, ps.LOCATION)
) = 1;

-- Fish species → thermal tolerance literature
FISH.THAMES_10.SCIENTIFIC_NAME = FISH.THERMAL_TOLERANCE.SPECIES_NAME

-- Fish survey counts → site locations
FISH.FW_FISH_COUNTS.SITE_ID = FISH.FW_FISH_SITES.SITE_ID
```

---

## External Read-Only Data Shares (Met Office)

These imported databases provide the raw source data:

| Database | Contents |
|----------|----------|
| `MET_CLIMATE` | Climate Data Portal (static) |
| `MET_OBSERVATIONS` | Land/marine observations |
| `MET_GRIDDED_FCST` | Gridded UK forecasts |
| `MET_SITE_FCST` | Site-specific UK forecasts |
| `MET_PSEUDO_OBS` | Pseudo-observations (source for CLIMATE timeseries) |
| `MET_WARNINGS` | NSWWS warnings archive |
| `UK_LAND_SURFACE_OBSERVATIONS` | Land surface obs |

---

## Access

```sql
USE ROLE ACCOUNTADMIN;
USE DATABASE MET_SCRATCH;
USE WAREHOUSE DEFAULT_WH;
```

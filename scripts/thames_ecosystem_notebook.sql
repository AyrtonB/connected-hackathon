-- Thames Ecosystem & Climate Risk: Connecting the Data
-- =====================================================
-- This notebook ties together our key datasets to tell a coherent story:
--   1. The River Thames geography (OS Open Rivers)
--   2. EA Hydrology monitoring stations and water quality readings
--   3. Met Office pseudo-observation climate timeseries (air temp & precip)
--   4. Fish thermal tolerance thresholds and population impact
--
-- The narrative: Climate warming → river water temperature rise → ecosystem stress
-- for Thames fish species. We join spatial, temporal, and biological data to quantify
-- this risk.

-- ============================================================================
-- PART 1: THE RIVER — Geography & Monitoring Network
-- ============================================================================

-- 1a. The Thames river network (527 links from OS Open Rivers)
SELECT
    COUNT(*)                          AS total_links,
    ROUND(SUM(LENGTH) / 1000, 1)     AS total_length_km,
    COUNT(DISTINCT WATERCOURSE_NAME)  AS distinct_named_rivers
FROM MET_SCRATCH.THAMES.RIVER_THAMES;

-- 1b. EA monitoring stations on/near the Thames
SELECT
    s.ID,
    s.LABEL,
    s.RIVER_NAME,
    s.LAT,
    s.LONG,
    COUNT(m.ID) AS num_measures
FROM MET_SCRATCH.THAMES.STATIONS s
LEFT JOIN MET_SCRATCH.THAMES.MEASURES m ON m.STATION_ID = s.ID
WHERE s.RIVER_NAME ILIKE '%thames%'
GROUP BY 1, 2, 3, 4, 5
ORDER BY s.LABEL;

-- 1c. What parameters do our Thames stations measure?
SELECT
    m.PARAMETER,
    m.PERIOD_NAME,
    m.VALUE_TYPE,
    m.UNIT_NAME,
    COUNT(*) AS num_measures,
    COUNT(DISTINCT m.STATION_ID) AS num_stations
FROM MET_SCRATCH.THAMES.MEASURES m
JOIN MET_SCRATCH.THAMES.STATIONS s ON s.ID = m.STATION_ID
WHERE s.RIVER_NAME ILIKE '%thames%'
GROUP BY 1, 2, 3, 4
ORDER BY num_stations DESC, m.PARAMETER;

-- ============================================================================
-- PART 2: WATER TEMPERATURE — What the River Actually Measures
-- ============================================================================

-- 2a. Water temperature readings from EA stations (last year, daily mean)
SELECT
    s.LABEL AS station,
    DATE_TRUNC('day', r.DATE_TIME) AS day,
    ROUND(AVG(r.VALUE), 2) AS avg_water_temp_c
FROM MET_SCRATCH.THAMES.READINGS r
JOIN MET_SCRATCH.THAMES.STATIONS s ON s.ID = r.STATION_ID
WHERE r.PARAMETER = 'TEMPERATURE'
  AND r.PERIOD_NAME = '15min'
  AND s.RIVER_NAME ILIKE '%thames%'
GROUP BY 1, 2
ORDER BY station, day
LIMIT 200;

-- 2b. Recent daily water temperature (derived from EA readings)
SELECT
    DATE_TRUNC('day', r.DATE_TIME) AS day,
    ROUND(AVG(r.VALUE), 2) AS mean_water_temp_c,
    ROUND(MAX(r.VALUE), 2) AS max_water_temp_c,
    COUNT(DISTINCT r.STATION_ID) AS reporting_stations
FROM MET_SCRATCH.THAMES.READINGS r
JOIN MET_SCRATCH.THAMES.STATIONS s ON s.ID = r.STATION_ID
WHERE r.PARAMETER = 'TEMPERATURE'
  AND s.RIVER_NAME ILIKE '%thames%'
GROUP BY 1
ORDER BY day DESC
LIMIT 30;

-- ============================================================================
-- PART 3: AIR TEMPERATURE & PRECIPITATION — Met Office Pseudo-Obs
-- ============================================================================

-- 3a. Coverage: 116 Met Office sites along the Thames corridor, hourly 2011-2026
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT SITE_ID) AS sites,
    MIN(VALIDITY_TIME) AS first_obs,
    MAX(VALIDITY_TIME) AS last_obs,
    ROUND(AVG(SCREEN_TEMPERATURE_C), 1) AS mean_air_temp_c,
    ROUND(MAX(SCREEN_TEMPERATURE_C), 1) AS max_air_temp_c
FROM SNOWFLAKE_INTELLIGENCE.PUBLIC.THAMES_TEMPERATURE_TIMESERIES;

-- 3b. Annual warming trend: is Thames corridor air temperature rising?
SELECT
    YEAR(VALIDITY_TIME) AS yr,
    ROUND(AVG(SCREEN_TEMPERATURE_C), 2) AS mean_annual_air_temp_c,
    ROUND(MAX(SCREEN_TEMPERATURE_C), 1) AS max_air_temp_c,
    COUNT(*) AS obs_count
FROM SNOWFLAKE_INTELLIGENCE.PUBLIC.THAMES_TEMPERATURE_TIMESERIES
GROUP BY 1
ORDER BY 1;

-- 3c. Summer extremes: days where air temp exceeded fish stress thresholds
--     (26°C = upper optimum for most species, 30°C = stress, 33°C+ = lethal)
SELECT
    YEAR(VALIDITY_TIME) AS yr,
    COUNT_IF(SCREEN_TEMPERATURE_C >= 26) AS hours_above_26c,
    COUNT_IF(SCREEN_TEMPERATURE_C >= 30) AS hours_above_30c,
    COUNT_IF(SCREEN_TEMPERATURE_C >= 33) AS hours_above_33c
FROM SNOWFLAKE_INTELLIGENCE.PUBLIC.THAMES_TEMPERATURE_TIMESERIES
WHERE MONTH(VALIDITY_TIME) BETWEEN 5 AND 9  -- summer months
GROUP BY 1
ORDER BY 1;

-- ============================================================================
-- PART 4: FISH THERMAL RISK — Connecting Climate to Ecology
-- ============================================================================

-- 4a. Top 10 Thames fish species and their thermal tolerance bands
SELECT
    SPECIES_RANK,
    COMMON_NAME,
    THAMES_REACH,
    OPTIMUM_TEMP_MIN_C,
    OPTIMUM_TEMP_MAX_C,
    STRESS_TEMP_MAX_C,
    LETHAL_TEMP_MAX_C
FROM FISHDB.FISH_DEATH_RATES.THAMES_10
ORDER BY LETHAL_TEMP_MAX_C;

-- 4b. Cross-join: total site-hours of heat stress per species (air temp as proxy)
SELECT
    f.COMMON_NAME,
    f.STRESS_TEMP_MAX_C,
    f.LETHAL_TEMP_MAX_C,
    COUNT_IF(t.SCREEN_TEMPERATURE_C >= f.STRESS_TEMP_MAX_C
             AND t.SCREEN_TEMPERATURE_C < f.LETHAL_TEMP_MAX_C) AS stress_site_hours,
    COUNT_IF(t.SCREEN_TEMPERATURE_C >= f.LETHAL_TEMP_MAX_C)     AS lethal_site_hours,
    ROUND(MAX(t.SCREEN_TEMPERATURE_C), 1)                       AS max_observed_air_c
FROM FISHDB.FISH_DEATH_RATES.THAMES_10 f
CROSS JOIN SNOWFLAKE_INTELLIGENCE.PUBLIC.THAMES_TEMPERATURE_TIMESERIES t
GROUP BY 1, 2, 3
ORDER BY lethal_site_hours DESC;

-- 4c. Population simulation outcomes under climate scenarios
SELECT
    SPECIES,
    SCENARIO,
    INITIAL_POP,
    FINAL_POP,
    TOTAL_THERMAL_DEATHS,
    ROUND(FINAL_THERMAL_TOLERANCE, 4) AS FINAL_THERMAL_TOLERANCE,
    ROUND((FINAL_POP - INITIAL_POP)::FLOAT / INITIAL_POP * 100, 1) AS pct_change
FROM SNOWFLAKE_INTELLIGENCE.PUBLIC.THAMES_FISH_POPULATION_SUMMARY
ORDER BY SPECIES, SCENARIO;

-- ============================================================================
-- PART 5: SPATIAL JOIN — Linking Met Sites to EA Stations
-- ============================================================================

-- 5a. For each EA station, find the nearest Met Office pseudo-obs site
--     and compare air vs water temperature where both are available
SELECT
    s.LABEL AS ea_station,
    ps.SITE_NAME AS met_site,
    ROUND(ST_DISTANCE(s.LOCATION, ps.LOCATION), 0) AS distance_m
FROM MET_SCRATCH.THAMES.STATIONS s
CROSS JOIN MET_SCRATCH.THAMES.PSEUDO_SITES_GEO ps
WHERE s.RIVER_NAME ILIKE '%thames%'
QUALIFY ROW_NUMBER() OVER (PARTITION BY s.ID ORDER BY ST_DISTANCE(s.LOCATION, ps.LOCATION)) = 1
ORDER BY ea_station;

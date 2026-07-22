import json
import streamlit as st
import pandas as pd


def _conn():
    return st.connection("snowflake")


@st.cache_data(ttl=600)
def get_stations() -> pd.DataFrame:
    return _conn().query(
        "SELECT ID, LABEL, RIVER_NAME, LAT, LONG, NRFA_STATION_ID FROM MET_SCRATCH.THAMES.STATIONS"
    )


@st.cache_data(ttl=600)
def get_river_geojson() -> dict:
    df = _conn().query(
        "SELECT ID, WATERCOURSE_NAME, ST_ASGEOJSON(GEOMETRY) as geojson "
        "FROM MET_SCRATCH.THAMES.RIVER_THAMES"
    )
    geojson_col = "GEOJSON" if "GEOJSON" in df.columns else "geojson"
    features = []
    for _, row in df.iterrows():
        features.append({
            "type": "Feature",
            "geometry": json.loads(row[geojson_col]),
            "properties": {"ID": row["ID"], "WATERCOURSE_NAME": row["WATERCOURSE_NAME"]},
        })
    return {"type": "FeatureCollection", "features": features}


@st.cache_data(ttl=600)
def get_tidal_station_catchment(station_id: str) -> dict | None:
    df = _conn().query(
        f"""SELECT cb.NRFA_STATION_ID, cb.AREA_KM2, ST_ASGEOJSON(cb.GEOMETRY) as geojson
            FROM MET_SCRATCH.THAMES.TIDAL_STATION_CATCHMENTS tsc
            JOIN MET_SCRATCH.THAMES.CATCHMENT_BOUNDARIES cb ON cb.NRFA_STATION_ID = tsc.NRFA_STATION_ID
            WHERE tsc.STATION_ID = '{station_id}'"""
    )
    if df.empty:
        return None
    geojson_col = "GEOJSON" if "GEOJSON" in df.columns else "geojson"
    features = []
    total_area = 0
    for _, row in df.iterrows():
        features.append(json.loads(row[geojson_col]))
        total_area += row["AREA_KM2"]
    # Union via GeoJSON FeatureCollection (individual polygons for rendering)
    return {
        "type": "FeatureCollection",
        "features": [{"type": "Feature", "geometry": g, "properties": {}} for g in features],
        "total_area_km2": total_area,
    }


@st.cache_data(ttl=600)
def get_catchment_geojson(nrfa_station_id: str) -> dict | None:
    df = _conn().query(
        f"SELECT NRFA_STATION_ID, AREA_KM2, ST_ASGEOJSON(GEOMETRY) as geojson "
        f"FROM MET_SCRATCH.THAMES.CATCHMENT_BOUNDARIES "
        f"WHERE NRFA_STATION_ID = '{nrfa_station_id}'"
    )
    if df.empty:
        return None
    row = df.iloc[0]
    geojson_col = "GEOJSON" if "GEOJSON" in df.columns else "geojson"
    return {
        "type": "Feature",
        "geometry": json.loads(row[geojson_col]),
        "properties": {"NRFA_STATION_ID": row["NRFA_STATION_ID"], "AREA_KM2": row["AREA_KM2"]},
    }


@st.cache_data(ttl=600)
def get_catchment_climate(nrfa_station_id: str, days: int = 90) -> pd.DataFrame:
    return _conn().query(
        f"""SELECT t.VALIDITY_TIME, t.MEAN_AIR_TEMP_C, t.MAX_AIR_TEMP_C, t.MIN_AIR_TEMP_C,
                   p.MEAN_RAINFALL_MM_1H, p.TOTAL_RAINFALL_MM_1H
            FROM MET_SCRATCH.CLIMATE.CATCHMENT_TEMPERATURE_TIMESERIES t
            JOIN MET_SCRATCH.CLIMATE.CATCHMENT_PRECIPITATION_TIMESERIES p
              ON t.NRFA_STATION_ID = p.NRFA_STATION_ID AND t.VALIDITY_TIME = p.VALIDITY_TIME
            WHERE t.NRFA_STATION_ID = '{nrfa_station_id}'
              AND t.VALIDITY_TIME >= DATEADD(day, -{days}, CURRENT_TIMESTAMP())
            ORDER BY t.VALIDITY_TIME"""
    )


@st.cache_data(ttl=600)
def get_tidal_station_primary_catchment(station_id: str) -> str | None:
    df = _conn().query(
        f"""SELECT NRFA_STATION_ID FROM MET_SCRATCH.THAMES.TIDAL_STATION_CATCHMENTS
            WHERE STATION_ID = '{station_id}'
            ORDER BY NRFA_STATION_ID
            LIMIT 1"""
    )
    if df.empty:
        return None
    return str(df.iloc[0]["NRFA_STATION_ID"])


@st.cache_data(ttl=600)
def get_nearest_met_site(station_id: str) -> pd.DataFrame:
    return _conn().query(
        f"""SELECT ps.SITE_ID, ps.SITE_NAME,
                   ROUND(ST_DISTANCE(s.LOCATION, ps.LOCATION), 0) as DIST_M
            FROM MET_SCRATCH.THAMES.STATIONS s
            CROSS JOIN MET_SCRATCH.THAMES.PSEUDO_SITES_GEO ps
            WHERE s.ID = '{station_id}'
            QUALIFY ROW_NUMBER() OVER (PARTITION BY s.ID ORDER BY ST_DISTANCE(s.LOCATION, ps.LOCATION)) = 1"""
    )


@st.cache_data(ttl=600)
def get_site_climate(site_id: int, days: int = 90) -> pd.DataFrame:
    return _conn().query(
        f"""SELECT t.VALIDITY_TIME, t.SCREEN_TEMPERATURE_C, p.RAINFALL_MM_1H
            FROM MET_SCRATCH.CLIMATE.THAMES_TEMPERATURE_TIMESERIES t
            JOIN MET_SCRATCH.CLIMATE.THAMES_PRECIPITATION_TIMESERIES p
              ON t.SITE_ID = p.SITE_ID AND t.VALIDITY_TIME = p.VALIDITY_TIME
            WHERE t.SITE_ID = {site_id}
              AND t.VALIDITY_TIME >= DATEADD(day, -{days}, CURRENT_TIMESTAMP())
            ORDER BY t.VALIDITY_TIME"""
    )


@st.cache_data(ttl=600)
def get_station_readings(station_id: str, parameter: str = "TEMPERATURE") -> pd.DataFrame:
    return _conn().query(
        f"SELECT DATE_TIME, VALUE, QUALITY FROM MET_SCRATCH.THAMES.READINGS "
        f"WHERE STATION_ID = '{station_id}' AND PARAMETER = '{parameter}' "
        f"ORDER BY DATE_TIME"
    )


@st.cache_data(ttl=600)
def get_air_temp_timeseries(
    site_id: int | None = None, start: str | None = None, end: str | None = None
) -> pd.DataFrame:
    if site_id is not None:
        query = (
            "SELECT SITE_ID, SITE_NAME, VALIDITY_TIME, SCREEN_TEMPERATURE_C "
            "FROM MET_SCRATCH.CLIMATE.THAMES_TEMPERATURE_TIMESERIES"
        )
        conditions = [f"SITE_ID = {site_id}"]
        if start:
            conditions.append(f"VALIDITY_TIME >= '{start}'")
        if end:
            conditions.append(f"VALIDITY_TIME <= '{end}'")
        query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY VALIDITY_TIME"
    else:
        query = (
            "SELECT VALIDITY_TIME, "
            "AVG(SCREEN_TEMPERATURE_C) as SCREEN_TEMPERATURE_C, "
            "MIN(SCREEN_TEMPERATURE_C) as SCREEN_TEMP_MIN_C, "
            "MAX(SCREEN_TEMPERATURE_C) as SCREEN_TEMP_MAX_C "
            "FROM MET_SCRATCH.CLIMATE.THAMES_TEMPERATURE_TIMESERIES"
        )
        conditions = []
        if start:
            conditions.append(f"VALIDITY_TIME >= '{start}'")
        if end:
            conditions.append(f"VALIDITY_TIME <= '{end}'")
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        else:
            query += " WHERE VALIDITY_TIME >= DATEADD(year, -1, CURRENT_DATE())"
        query += " GROUP BY VALIDITY_TIME ORDER BY VALIDITY_TIME"
    return _conn().query(query)


@st.cache_data(ttl=600)
def get_water_temp_daily() -> pd.DataFrame:
    return _conn().query(
        """SELECT DATE_TRUNC('day', r.DATE_TIME) AS "date",
                  AVG(r.VALUE) as "water_temp_c",
                  MIN(r.VALUE) as "water_temp_min_c",
                  MAX(r.VALUE) as "water_temp_max_c"
           FROM MET_SCRATCH.THAMES.READINGS r
           WHERE r.PARAMETER = 'TEMPERATURE'
           GROUP BY 1
           ORDER BY 1"""
    )


@st.cache_data(ttl=600)
def get_water_temp_forecast() -> pd.DataFrame:
    return _conn().query(
        'SELECT "date", "forecast_water_temp_c" FROM MET_SCRATCH.CLIMATE.THAMES_WATER_TEMPERATURE_FORECAST ORDER BY "date"'
    )


@st.cache_data(ttl=600)
def get_fish_species() -> pd.DataFrame:
    return _conn().query(
        "SELECT * FROM MET_SCRATCH.FISH.THAMES_10 ORDER BY LETHAL_TEMP_MAX_C"
    )


@st.cache_data(ttl=600)
def get_population_simulation(
    species: str | None = None, scenario: str | None = None
) -> pd.DataFrame:
    query = "SELECT * FROM MET_SCRATCH.FISH.THAMES_FISH_POPULATION_SIMULATION"
    conditions = []
    if species:
        conditions.append(f"species = '{species}'")
    if scenario:
        conditions.append(f"scenario = '{scenario}'")
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    return _conn().query(query)


@st.cache_data(ttl=600)
def get_population_summary() -> pd.DataFrame:
    return _conn().query(
        "SELECT * FROM MET_SCRATCH.FISH.THAMES_FISH_POPULATION_SUMMARY"
    )

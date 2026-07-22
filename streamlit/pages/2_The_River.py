import streamlit as st
import pandas as pd
import pydeck as pdk
from data import (
    get_stations, get_river_geojson, get_catchment_geojson,
    get_station_readings, get_nearest_met_site, get_site_climate,
    get_catchment_climate, get_tidal_station_catchment,
    get_tidal_station_primary_catchment,
)

st.title("The River Thames — Monitoring Network")

stations = get_stations()
river_geojson = get_river_geojson()


@st.cache_data(ttl=600)
def get_station_parameters():
    conn = st.connection("snowflake")
    return conn.query(
        "SELECT DISTINCT STATION_ID, PARAMETER FROM MET_SCRATCH.THAMES.READINGS"
    )


params_df = get_station_parameters()

# Default to Cadogan Pier
if "selected_station_label" not in st.session_state:
    st.session_state.selected_station_label = "THAMES_CADOGAN PIER_E_200707"

station_label = st.sidebar.selectbox(
    "Select a station",
    stations["LABEL"].tolist(),
    index=stations["LABEL"].tolist().index(st.session_state.selected_station_label)
    if st.session_state.selected_station_label in stations["LABEL"].tolist()
    else 0,
    key="station_select",
)
st.session_state.selected_station_label = station_label
selected_station = stations[stations["LABEL"] == station_label].iloc[0]
station_id = str(selected_station["ID"])
nrfa_id = selected_station.get("NRFA_STATION_ID")

# Build pydeck layers
layers = []

# River GeoJSON layer
layers.append(pdk.Layer(
    "GeoJsonLayer",
    data=river_geojson,
    get_line_color=[0, 100, 200],
    get_line_width=30,
    pickable=False,
))

# Catchment polygon
catchment_data = None
if pd.notna(nrfa_id) and str(nrfa_id).strip():
    catchment_data = get_catchment_geojson(str(nrfa_id))
if not catchment_data:
    catchment_data = get_tidal_station_catchment(station_id)

if catchment_data:
    layers.append(pdk.Layer(
        "GeoJsonLayer",
        data=catchment_data,
        get_fill_color=[0, 180, 0, 30],
        get_line_color=[0, 150, 0],
        get_line_width=50,
        pickable=False,
    ))

# Station scatter layer
station_data = []
for _, stn in stations.iterrows():
    is_selected = stn["LABEL"] == station_label
    station_data.append({
        "position": [float(stn["LONG"]), float(stn["LAT"])],
        "label": stn["LABEL"],
        "color": [220, 50, 50, 220] if is_selected else [50, 100, 200, 160],
        "radius": 350 if is_selected else 180,
    })

layers.append(pdk.Layer(
    "ScatterplotLayer",
    data=station_data,
    get_position="position",
    get_fill_color="color",
    get_radius="radius",
    pickable=True,
))

# Render map
view_state = pdk.ViewState(
    latitude=float(selected_station["LAT"]),
    longitude=float(selected_station["LONG"]),
    zoom=9,
    pitch=0,
)

st.pydeck_chart(pdk.Deck(
    layers=layers,
    initial_view_state=view_state,
    map_style="mapbox://styles/mapbox/light-v10",
))

# Station detail panel
st.divider()
st.subheader(f"Station: {selected_station['LABEL']}")

col1, col2, col3, col4 = st.columns(4)
col1.metric("River", selected_station.get("RIVER_NAME") or "N/A")
col2.metric("Latitude", f"{selected_station['LAT']:.4f}")
col3.metric("Longitude", f"{selected_station['LONG']:.4f}")
col4.metric("NRFA ID", str(nrfa_id) if pd.notna(nrfa_id) else "N/A")

# Get available parameters for this station
available_params = params_df[params_df["STATION_ID"] == station_id]["PARAMETER"].tolist()

if not available_params:
    st.info("This station has no readings in the database.")
else:
    default_idx = available_params.index("TEMPERATURE") if "TEMPERATURE" in available_params else 0
    parameter = st.selectbox("Parameter", available_params, index=default_idx)
    readings = get_station_readings(station_id, parameter)

    if readings.empty:
        st.warning("No readings available for this station/parameter combination")
    else:
        st.subheader(f"Station Readings — {parameter}")
        try:
            readings["DATE_TIME"] = pd.to_datetime(readings["DATE_TIME"])
            if readings["DATE_TIME"].dt.year.max() > 2030 or readings["DATE_TIME"].dt.year.min() < 1990:
                raise ValueError("Dates out of valid range")
            st.line_chart(readings.set_index("DATE_TIME")["VALUE"])
        except (ValueError, TypeError):
            st.caption(f"Showing {len(readings):,} readings (sequential order)")
            st.line_chart(readings["VALUE"].reset_index(drop=True))

# Catchment climate data
st.divider()

catchment_nrfa = None
catchment_label_text = None
if pd.notna(nrfa_id) and str(nrfa_id).strip():
    catchment_nrfa = str(nrfa_id)
    catchment_label_text = f"Catchment {nrfa_id} — aggregated from Met Office sites within the catchment boundary"
else:
    tidal_nrfa = get_tidal_station_primary_catchment(station_id)
    if tidal_nrfa:
        catchment_nrfa = tidal_nrfa
        catchment_label_text = f"Upstream catchment {tidal_nrfa} (Kingston/Thames) — aggregated from Met Office sites within the drainage area"

use_catchment = False
if catchment_nrfa:
    catchment_climate = get_catchment_climate(catchment_nrfa, days=90)
    if not catchment_climate.empty:
        use_catchment = True
        st.subheader("Catchment Climate (multi-site aggregate)")
        st.caption(catchment_label_text)

        catchment_climate["VALIDITY_TIME"] = pd.to_datetime(catchment_climate["VALIDITY_TIME"])
        daily = catchment_climate.set_index("VALIDITY_TIME").resample("D").agg({
            "MEAN_AIR_TEMP_C": "mean",
            "MIN_AIR_TEMP_C": "min",
            "MAX_AIR_TEMP_C": "max",
            "TOTAL_RAINFALL_MM_1H": "sum",
        }).dropna().reset_index().sort_values("VALIDITY_TIME")

        col_temp, col_rain = st.columns(2)
        with col_temp:
            st.markdown("**Air Temperature (daily, last 90 days)**")
            chart_data = daily[["VALIDITY_TIME", "MEAN_AIR_TEMP_C", "MIN_AIR_TEMP_C", "MAX_AIR_TEMP_C"]].copy()
            chart_data.columns = ["Date", "Mean", "Min", "Max"]
            st.line_chart(chart_data.set_index("Date"))
        with col_rain:
            st.markdown("**Precipitation (daily total, last 90 days)**")
            rain_data = daily[["VALIDITY_TIME", "TOTAL_RAINFALL_MM_1H"]].copy()
            rain_data.columns = ["Date", "Rainfall (mm)"]
            st.bar_chart(rain_data.set_index("Date"))

if not use_catchment:
    st.subheader("Local Climate — Nearest Met Office Site")
    met_site_df = get_nearest_met_site(station_id)
    if not met_site_df.empty:
        site_name = met_site_df.iloc[0]["SITE_NAME"]
        dist_m = met_site_df.iloc[0]["DIST_M"]
        selected_met_site_id = int(met_site_df.iloc[0]["SITE_ID"])
        st.caption(f"Met Office site: {site_name} ({dist_m:.0f}m from station)")

        climate_df = get_site_climate(selected_met_site_id, days=90)
        if not climate_df.empty:
            climate_df["VALIDITY_TIME"] = pd.to_datetime(climate_df["VALIDITY_TIME"])
            daily = climate_df.set_index("VALIDITY_TIME").resample("D").agg(
                {"SCREEN_TEMPERATURE_C": "mean", "RAINFALL_MM_1H": "sum"}
            ).reset_index()
            daily.columns = ["Date", "Air Temp (°C)", "Rainfall (mm)"]

            col_temp, col_rain = st.columns(2)
            with col_temp:
                st.markdown("**Air Temperature (daily mean, last 90 days)**")
                st.line_chart(daily.set_index("Date")["Air Temp (°C)"])
            with col_rain:
                st.markdown("**Precipitation (daily total, last 90 days)**")
                st.bar_chart(daily.set_index("Date")["Rainfall (mm)"])
        else:
            st.info("No recent climate data available.")
    else:
        st.info("No nearby Met Office site found.")

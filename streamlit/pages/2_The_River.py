import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
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


@st.cache_data(ttl=600)
def get_met_sites():
    conn = st.connection("snowflake")
    return conn.query(
        "SELECT SITE_ID, SITE_NAME, LATITUDE, LONGITUDE FROM MET_SCRATCH.THAMES.PSEUDO_SITES_GEO"
    )


params_df = get_station_parameters()
met_sites = get_met_sites()

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

# Build folium map
m = folium.Map(location=[51.5, -0.8], zoom_start=9, tiles="CartoDB positron")

# Add river GeoJSON
folium.GeoJson(
    river_geojson,
    style_function=lambda _: {"color": "blue", "weight": 2, "opacity": 0.7},
    name="River Thames",
).add_to(m)

# Add catchment if available (direct NRFA match or tidal station mapping)
catchment_shown = False
if pd.notna(nrfa_id) and str(nrfa_id).strip():
    catchment = get_catchment_geojson(str(nrfa_id))
    if catchment:
        folium.GeoJson(
            catchment,
            style_function=lambda _: {
                "color": "green",
                "weight": 2,
                "fillColor": "green",
                "fillOpacity": 0.15,
            },
            name="Catchment",
        ).add_to(m)
        catchment_shown = True

if not catchment_shown:
    tidal_catchment = get_tidal_station_catchment(station_id)
    if tidal_catchment:
        folium.GeoJson(
            tidal_catchment,
            style_function=lambda _: {
                "color": "green",
                "weight": 2,
                "fillColor": "green",
                "fillOpacity": 0.12,
            },
            name="Upstream Catchment",
        ).add_to(m)
        catchment_shown = True

# Find nearest Met site for the selected station
met_site_df = get_nearest_met_site(station_id)
selected_met_site_id = int(met_site_df.iloc[0]["SITE_ID"]) if not met_site_df.empty else None

# Add Met Office sites (small green/orange markers)
for _, site in met_sites.iterrows():
    is_nearest = site["SITE_ID"] == selected_met_site_id
    folium.CircleMarker(
        location=[site["LATITUDE"], site["LONGITUDE"]],
        radius=7 if is_nearest else 4,
        color="orange" if is_nearest else "green",
        fill=True,
        fill_color="orange" if is_nearest else "green",
        fill_opacity=0.9 if is_nearest else 0.3,
        tooltip=f"Met: {site['SITE_NAME']}" + (" (nearest)" if is_nearest else ""),
    ).add_to(m)

# Add EA station markers with tooltip
for _, stn in stations.iterrows():
    is_selected = stn["LABEL"] == station_label
    folium.CircleMarker(
        location=[stn["LAT"], stn["LONG"]],
        radius=8 if is_selected else 6,
        color="red" if is_selected else "blue",
        fill=True,
        fill_color="red" if is_selected else "blue",
        fill_opacity=0.8 if is_selected else 0.5,
        tooltip=stn["LABEL"],
    ).add_to(m)

map_data = st_folium(m, width=None, height=500, returned_objects=["last_object_clicked"])

# Handle map click — find nearest station
if map_data and map_data.get("last_object_clicked"):
    click = map_data["last_object_clicked"]
    click_lat = click.get("lat")
    click_lng = click.get("lng")
    if click_lat and click_lng:
        distances = ((stations["LAT"] - click_lat) ** 2 + (stations["LONG"] - click_lng) ** 2)
        nearest_idx = distances.idxmin()
        clicked_label = stations.loc[nearest_idx, "LABEL"]
        if clicked_label != st.session_state.selected_station_label:
            st.session_state.selected_station_label = clicked_label
            st.rerun()

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
    if not met_site_df.empty:
        site_name = met_site_df.iloc[0]["SITE_NAME"]
        dist_m = met_site_df.iloc[0]["DIST_M"]
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

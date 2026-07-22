import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import date

from data import get_water_temp_daily

st.title("Climate Signal — Air & Water Temperature")

# Sidebar controls
date_range = st.sidebar.date_input(
    "Date range",
    value=(date(2024, 1, 1), date(2026, 7, 21)),
)
if len(date_range) == 2:
    start_str = date_range[0].strftime("%Y-%m-%d")
    end_str = date_range[1].strftime("%Y-%m-%d")
else:
    start_str = date_range[0].strftime("%Y-%m-%d")
    end_str = "2026-07-21"

# Section 1: Air Temperature
st.header("Thames Corridor Air Temperature (116-site average)")

conn = st.connection("snowflake")
daily_air = conn.query(f"""
    SELECT DATE_TRUNC('day', VALIDITY_TIME) AS day,
           AVG(SCREEN_TEMPERATURE_C) AS mean_c,
           MIN(SCREEN_TEMPERATURE_C) AS min_c,
           MAX(SCREEN_TEMPERATURE_C) AS max_c
    FROM MET_SCRATCH.CLIMATE.THAMES_TEMPERATURE_TIMESERIES
    WHERE VALIDITY_TIME >= '{start_str}' AND VALIDITY_TIME <= '{end_str}'
    GROUP BY 1
    ORDER BY 1
""")

if not daily_air.empty:
    daily_air.columns = daily_air.columns.str.upper()
    daily_air["DAY"] = pd.to_datetime(daily_air["DAY"])
    daily_air = daily_air.sort_values("DAY")
    daily_air["rolling_30d"] = daily_air["MEAN_C"].rolling(30).mean()

    fig_air = go.Figure()
    fig_air.add_trace(go.Scatter(
        x=daily_air["DAY"], y=daily_air["MAX_C"],
        mode="lines", name="Daily Max", line=dict(width=0),
        showlegend=False,
    ))
    fig_air.add_trace(go.Scatter(
        x=daily_air["DAY"], y=daily_air["MIN_C"],
        mode="lines", name="Min–Max Range", line=dict(width=0),
        fill="tonexty", fillcolor="rgba(70,130,180,0.15)",
    ))
    fig_air.add_trace(go.Scatter(
        x=daily_air["DAY"], y=daily_air["MEAN_C"],
        mode="lines", name="Daily Mean", line=dict(color="steelblue", width=1),
    ))
    fig_air.add_trace(go.Scatter(
        x=daily_air["DAY"], y=daily_air["rolling_30d"],
        mode="lines", name="30-day Rolling Mean", line=dict(color="darkred", width=2),
    ))
    fig_air.update_layout(yaxis_title="Temperature (°C)", xaxis_title="Date", height=400)
    st.plotly_chart(fig_air, use_container_width=True)
else:
    st.warning("No air temperature data available for the selected range.")

# Section 2: Water Temperature
st.header("Thames Daily Mean Water Temperature (EA stations)")

water_df = get_water_temp_daily()
if not water_df.empty:
    water_df.columns = water_df.columns.str.lower()
    water_df["date"] = pd.to_datetime(water_df["date"])
    water_df = water_df.sort_values("date")
    mask = (water_df["date"] >= start_str) & (water_df["date"] <= end_str)
    water_filtered = water_df[mask]

    fig_water = go.Figure()
    fig_water.add_trace(go.Scatter(
        x=water_filtered["date"], y=water_filtered["water_temp_max_c"],
        mode="lines", name="Daily Max", line=dict(width=0),
        showlegend=False,
    ))
    fig_water.add_trace(go.Scatter(
        x=water_filtered["date"], y=water_filtered["water_temp_min_c"],
        mode="lines", name="Min–Max Range", line=dict(width=0),
        fill="tonexty", fillcolor="rgba(0,128,128,0.15)",
    ))
    fig_water.add_trace(go.Scatter(
        x=water_filtered["date"], y=water_filtered["water_temp_c"],
        mode="lines", name="Mean Water Temp", line=dict(color="teal", width=1.5),
    ))
    fig_water.add_hline(y=26, line_dash="dash", line_color="orange",
                        annotation_text="Stress (sensitive species)")
    fig_water.add_hline(y=30, line_dash="dash", line_color="red",
                        annotation_text="Stress (most species)")
    fig_water.add_hline(y=33, line_dash="dash", line_color="darkred",
                        annotation_text="Lethal zone")
    fig_water.update_layout(yaxis_title="Temperature (°C)", xaxis_title="Date", height=400)
    st.plotly_chart(fig_water, use_container_width=True)
else:
    st.warning("No water temperature data available.")

# Section 3: Summer Stress Hours by Year
st.header("Summer Stress Hours by Year")

stress_df = conn.query("""
    SELECT YEAR(VALIDITY_TIME) AS yr,
           COUNT_IF(SCREEN_TEMPERATURE_C >= 26) AS hours_above_26c,
           COUNT_IF(SCREEN_TEMPERATURE_C >= 30) AS hours_above_30c,
           COUNT_IF(SCREEN_TEMPERATURE_C >= 33) AS hours_above_33c
    FROM MET_SCRATCH.CLIMATE.THAMES_TEMPERATURE_TIMESERIES
    WHERE MONTH(VALIDITY_TIME) BETWEEN 5 AND 9
    GROUP BY 1 ORDER BY 1
""")

if not stress_df.empty:
    stress_df.columns = stress_df.columns.str.upper()
    stress_melted = stress_df.melt(
        id_vars=["YR"],
        value_vars=["HOURS_ABOVE_26C", "HOURS_ABOVE_30C", "HOURS_ABOVE_33C"],
        var_name="threshold",
        value_name="hours",
    )
    labels = {
        "HOURS_ABOVE_26C": "≥26°C",
        "HOURS_ABOVE_30C": "≥30°C",
        "HOURS_ABOVE_33C": "≥33°C",
    }
    stress_melted["threshold"] = stress_melted["threshold"].map(labels)

    fig_stress = px.bar(
        stress_melted, x="YR", y="hours", color="threshold",
        barmode="group", color_discrete_map={"≥26°C": "orange", "≥30°C": "red", "≥33°C": "darkred"},
    )
    fig_stress.update_layout(xaxis_title="Year", yaxis_title="Hours", height=400)
    st.plotly_chart(fig_stress, use_container_width=True)
else:
    st.warning("No summer stress data available.")

st.info(
    "Air temperatures along the Thames corridor have been rising, with increasing hours above "
    "fish thermal stress thresholds each summer. The water temperature model translates this "
    "into actionable forecasts."
)

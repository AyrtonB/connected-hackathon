import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from data import (
    get_fish_species,
    get_population_simulation,
    get_population_summary,
)

st.title("Fish at Risk — Thermal Forecast & Population Model")

species_df = get_fish_species()
species_list = species_df["COMMON_NAME"].tolist() if not species_df.empty else []
selected_species = st.sidebar.multiselect(
    "Species", species_list, default=["Roach", "Dace", "Bleak", "Pike"]
)

conn = st.connection("snowflake")

# ==========================================================================
# SECTION 1: River Temperature Model — Forecast vs Actual (Walk-Forward)
# ==========================================================================
st.header("River Temperature Model — Forecast vs Actual")
st.caption("Walk-forward validation: how well does the air→water temperature model predict actual river temperature?")

walkforward = conn.query("""
    SELECT "date", "actual_c", "forecast_c"
    FROM SNOWFLAKE_INTELLIGENCE.PUBLIC.THAMES_RIVERTEMP_WALKFORWARD
    ORDER BY "date"
""")

if not walkforward.empty:
    walkforward["date"] = pd.to_datetime(walkforward["date"])

    fig_wf = go.Figure()
    fig_wf.add_trace(go.Scatter(
        x=walkforward["date"], y=walkforward["actual_c"],
        mode="lines", name="Actual Water Temp", line=dict(color="teal", width=2),
    ))
    fig_wf.add_trace(go.Scatter(
        x=walkforward["date"], y=walkforward["forecast_c"],
        mode="lines", name="Forecast Water Temp", line=dict(color="orange", width=2, dash="dash"),
    ))
    # Fish stress thresholds
    fig_wf.add_hline(y=26, line_dash="dot", line_color="orange", annotation_text="Stress onset")
    fig_wf.add_hline(y=30, line_dash="dot", line_color="red", annotation_text="Stress (most species)")
    fig_wf.update_layout(
        yaxis_title="Water Temperature (°C)", xaxis_title="Date", height=400,
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
    )
    st.plotly_chart(fig_wf, use_container_width=True)
else:
    st.warning("No walk-forward data available.")

# ==========================================================================
# SECTION 2: Population Impact — Forecast-Driven vs Actual
# ==========================================================================
st.header("Population Impact — Forecast vs Actual Temperature")
st.caption("Population model driven by forecast river temperature vs actual observations. Shows how well the forecast predicts ecological impact.")

pop_ts = conn.query("""
    SELECT "date", "species", "driver", "population"
    FROM SNOWFLAKE_INTELLIGENCE.PUBLIC.THAMES_FISH_POP_TIMESERIES
    ORDER BY "date"
""")

if not pop_ts.empty:
    pop_ts["date"] = pd.to_datetime(pop_ts["date"])
    pop_filtered = pop_ts[pop_ts["species"].isin(selected_species)]

    if not pop_filtered.empty:
        fig_pop_fc = px.line(
            pop_filtered, x="date", y="population", color="species",
            line_dash="driver", title="Population: Actual vs Forecast drivers",
        )
        fig_pop_fc.update_layout(height=450, xaxis_title="Date", yaxis_title="Population")
        st.plotly_chart(fig_pop_fc, use_container_width=True)

    # Forecast vs actual summary table
    fc_summary = conn.query("SELECT * FROM SNOWFLAKE_INTELLIGENCE.PUBLIC.THAMES_FISH_FORECAST_VS_ACTUAL")
    if not fc_summary.empty:
        st.subheader("Forecast Accuracy — Population Model")
        st.dataframe(
            fc_summary,
            column_config={
                "species": "Species",
                "stress_c": st.column_config.NumberColumn("Stress °C"),
                "lethal_c": st.column_config.NumberColumn("Lethal °C"),
                "actual_final_pop": st.column_config.NumberColumn("Actual Final Pop"),
                "forecast_final_pop": st.column_config.NumberColumn("Forecast Final Pop"),
                "actual_thermal_deaths": st.column_config.NumberColumn("Actual Deaths"),
                "forecast_thermal_deaths": st.column_config.NumberColumn("Forecast Deaths"),
                "pop_error": st.column_config.NumberColumn("Pop Error"),
                "death_error": st.column_config.NumberColumn("Death Error"),
            },
            use_container_width=True,
            hide_index=True,
        )
else:
    st.warning("No population timeseries data available.")

# ==========================================================================
# SECTION 3: Climate Scenario Simulations (baseline / +3°C / +5°C)
# ==========================================================================
st.header("Climate Scenario Projections")
st.caption("What happens to fish populations under sustained warming? Simulations using synthetic temperature profiles.")

scenario = st.sidebar.selectbox("Climate scenario", ["baseline", "+3C", "+5C"], index=1)

sim_df = get_population_simulation()
if not sim_df.empty:
    sim_filtered = sim_df[
        (sim_df["species"].isin(selected_species)) & (sim_df["scenario"] == scenario)
    ]

    if not sim_filtered.empty:
        st.subheader(f"Population Simulation — {scenario} scenario")
        fig_pop = px.line(
            sim_filtered, x="day", y="population", color="species",
        )
        fig_pop.update_layout(height=400, xaxis_title="Simulation Day", yaxis_title="Population")
        st.plotly_chart(fig_pop, use_container_width=True)

        # Thermal deaths chart
        st.subheader("Thermal Deaths per Day")
        fig_deaths = px.area(
            sim_filtered, x="day", y="thermal_deaths", color="species",
        )
        fig_deaths.update_layout(height=350, xaxis_title="Simulation Day", yaxis_title="Thermal Deaths")
        st.plotly_chart(fig_deaths, use_container_width=True)
    else:
        st.warning("No simulation data for the selected species/scenario.")
else:
    st.warning("No population simulation data available.")

# Summary Table
st.header("Scenario Outcomes Summary")
summary_df = get_population_summary()
if not summary_df.empty:
    st.dataframe(
        summary_df[["species", "scenario", "final_pop", "thermal_deaths", "thermal_tol"]],
        column_config={
            "species": "Species",
            "scenario": "Scenario",
            "final_pop": st.column_config.NumberColumn("Final Population", format="%d"),
            "thermal_deaths": st.column_config.NumberColumn("Thermal Deaths", format="%d"),
            "thermal_tol": st.column_config.NumberColumn("Thermal Tolerance", format="%.4f"),
        },
        use_container_width=True,
        hide_index=True,
    )

# Key insight
st.info(
    "The forecast-driven model closely tracks the actual population outcomes — Dace and Pike "
    "show the largest impacts due to their lower thermal tolerance. Under climate scenarios, "
    "+3°C causes 624 Dace thermal deaths; +5°C raises this to 2,701."
)

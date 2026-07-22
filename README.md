# Fried Fish — Thames Climate Risk Dashboard

A real-time early-warning system for thermal stress events threatening fish in the River Thames.

**Live app:** [connected-hackathon.streamlit.app](https://connected-hackathon.streamlit.app)

## The Hackathon

Built in a single day at **"Improving the Use of Weather and Climate Data for Smarter Decision Making"** (22 July 2026, London) — a collaborative hackathon hosted by:

- **Connected Places Catapult** — venue and innovation support
- **Met Office** — weather and climate data (15 years of hourly pseudo-observations)
- **Snowflake** — cloud data platform and AI tooling
- **Government Digital Service (GDS)** — digital strategy and public sector context

Delivered in partnership with UKRI / Innovate UK.

### Challenge

> *"What extra value appears when AI can search, summarise, join and explain weather data in the context of real operational choices?"*

We chose the **Resilience & Emergency Response** theme and framed our challenge as:

> **How might we** join weather and climate data with river monitoring and fish ecology **so that** Thames fisheries officers **can** anticipate thermal stress events before they cause fish mortality?

### Approach

Following the hackathon's human-centred design methodology:
1. Defined a user persona (Dr. Nicholas Sturgeon, Thames Fisheries Officer)
2. Mapped current vs. future user journey (reactive → predictive)
3. Joined 4 fragmented datasets in Snowflake using geospatial queries
4. Built an air-to-water temperature forecast model
5. Simulated fish population impacts under climate scenarios (+3°C, +5°C)
6. Delivered an interactive Streamlit dashboard as the prototype

### Judging Criteria

| Criterion | Weight | What it assesses |
|---|---|---|
| Technology & Innovation | 50% | Originality, improvement over existing services, potential to increase data use |
| Impact & Value | 30% | How well the challenge is addressed, benefit to users/society |
| Feasibility | 20% | Practicality of implementation into existing systems |

## What it does

Joins fragmented weather, river monitoring, and fish ecology data into a single dashboard so Thames fisheries officers can **anticipate** thermal stress before fish kills occur.

| Page | Purpose |
|------|---------|
| The Challenge | Problem statement, user persona, data overview |
| The River | Interactive map of EA monitoring stations with catchment boundaries |
| Climate Signal | Air & water temperature trends, summer stress hours by year |
| Fish at Risk | Water temp forecast model, population simulations under climate scenarios |

## Architecture

```
Met Office pseudo-obs (15yr, 116 sites)
EA Hydrology API (flow, level, temp)          ──►  Snowflake (MET_SCRATCH)  ──►  Streamlit app
NRFA catchment boundaries (11 polygons)                                          (st.connection)
Fish thermal tolerance data (10 species)
```

## Data sources

- **Met Office** — Hourly pseudo-observations (temperature, precipitation) for 116 Thames corridor sites, 2011–2026
- **Environment Agency Hydrology API** — River flow, level, and water temperature from 11 NRFA gauges
- **NRFA catchment boundaries** — Drainage polygons for upstream aggregation
- **Fish ecology** — Thermal tolerance thresholds for 10 key Thames species

## Run locally

```bash
# Install dependencies
cd streamlit
pip install -r requirements.txt

# Add Snowflake credentials
mkdir -p .streamlit
cat > .streamlit/secrets.toml << 'EOF'
[connections.snowflake]
account = "your-account"
user = "your-user"
password = "your-password"
warehouse = "DEFAULT_WH"
database = "MET_SCRATCH"
schema = "THAMES"
authenticator = "snowflake"
EOF

# Run
streamlit run streamlit_app.py
```

## Project layout

```
streamlit/              Streamlit app (deployed to Streamlit Cloud)
  streamlit_app.py      Entry point (st.navigation)
  data.py              Data layer — all Snowflake queries
  pages/               Multi-page app pages
  images/              App assets
src/wxdecide/          Python package — data connectors & schemas
scripts/               SQL DDL, data loading, notebooks
data/                  Static GeoJSON (River Thames)
docs/                  Hackathon briefing docs
tests/                 Unit tests
```

## Tech stack

- **Snowflake** — Data warehouse, geospatial queries, time-series analytics
- **Streamlit** — Dashboard UI (deployed on Streamlit Community Cloud)
- **Plotly** — Interactive charts
- **Folium** — Interactive maps with GeoJSON layers
- **Python** — Data connectors (EA Hydrology API, catchment boundaries)

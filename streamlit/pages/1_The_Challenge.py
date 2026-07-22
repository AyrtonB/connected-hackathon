import streamlit as st

st.title("The Challenge: Saving Thames Fish — A Matter of Time and Plaice")

st.markdown(
    "Climate change is warming our rivers. Fish species that have thrived in the Thames "
    "for centuries now face lethal thermal conditions — and that's no red herring. "
    "This tool joins fragmented data into a single early-warning system, "
    "because we can't afford to flounder."
)

# ─── Challenge Statement ───────────────────────────────────────────────────────
st.info(
    "**How might we** join weather and climate data with river monitoring and fish ecology "
    "**so that** Thames fisheries officers **can** anticipate thermal stress events "
    "before they cause fish mortality?"
)

st.divider()

# ─── User Persona ──────────────────────────────────────────────────────────────
st.subheader("User Persona")

with st.container():
    col_img, col_info = st.columns([1, 4])
    with col_img:
        st.image("images/michael-fish.webp", width=140)
    with col_info:
        st.markdown("**Dr. Nicholas Sturgeon** — *Thames Fisheries & Biodiversity Officer, Environment Agency*")
        st.markdown(
            '*"As a fisheries officer, I need an integrated view of upstream climate, '
            "river conditions, and species vulnerability so I can issue early warnings "
            'before thermal events cause fish kills."*'
        )
    st.markdown("")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**Responsibilities**")
        st.markdown(
            "- Monitors fish populations across 11 Thames catchments\n"
            "- Assesses climate risk to aquatic biodiversity\n"
            "- Advises on interventions (oxygenation, flow management)\n"
            "- Reports to EA National Fisheries on Thames health"
        )
    with col2:
        st.markdown("**Pain Points**")
        st.markdown(
            "- Data scattered all over the plaice — no joined view\n"
            "- No forecast link between air temp and water temp\n"
            "- Fish surveys are annual; thermal events happen in hours\n"
            "- Always reactive — needs to trout problems early"
        )
    with col3:
        st.markdown("**Needs**")
        st.markdown(
            "- 7-day water temperature forecast per reach\n"
            "- Upstream catchment precipitation (low-flow risk)\n"
            "- Species-specific thermal alerts\n"
            "- Plain-English briefing for multi-agency calls"
        )

st.divider()

# ─── Stakeholder Mapping ───────────────────────────────────────────────────────
st.subheader("Stakeholders")

col_high, col_med, col_low = st.columns(3)
with col_high:
    with st.container():
        st.markdown("**Direct Users**")
        st.markdown(
            "- EA Fisheries Officers\n"
            "- EA Incident Response\n"
            "- Angling Trust / fisheries managers"
        )
with col_med:
    with st.container():
        st.markdown("**Indirect**")
        st.markdown(
            "- Water companies (abstraction impact)\n"
            "- Local councils (public health)\n"
            "- Conservation NGOs (Rivers Trust)"
        )
with col_low:
    with st.container():
        st.markdown("**Contextual**")
        st.markdown(
            "- Recreational anglers\n"
            "- Academic researchers\n"
            "- Met Office (downstream impact)"
        )

st.divider()

# ─── User Journey ─────────────────────────────────────────────────────────────
st.subheader("User Journey — Current vs Future")

tab_current, tab_future = st.tabs(["Something Fishy (Today)", "Reeling It In (With Tool)"])

with tab_current:
    cols = st.columns(5)
    steps = [
        ("Hear about heatwave", "BBC / news", "No river-specific context"),
        ("Check Met Office", "Separate portal", "Air temp only — no water translation"),
        ("Check EA monitoring", "Another system", "Historic only, no forecast"),
        ("Cross-reference manually", "Excel + phone calls", "Hours of manual joining"),
        ("React after fish kill", "Incident forms", "Too late — damage done"),
    ]
    for col, (step, tool, pain) in zip(cols, steps):
        with col:
            st.markdown(f"**{step}**")
            st.caption(tool)
            st.error(pain, icon="🐟")

with tab_future:
    cols = st.columns(5)
    steps = [
        ("Alert fires automatically", "Threshold trigger", "48h lead time"),
        ("Open single dashboard", "All data pre-joined", "Seconds, not hours"),
        ("Assess upstream signal", "Catchment precip + flow", "See the cause, not just the symptom"),
        ("Issue early warning", "Species-specific risk", "Right time and plaice"),
        ("Monitor & verify", "Live readings + forecast", "Closed-loop: predict → act → confirm"),
    ]
    for col, (step, tool, benefit) in zip(cols, steps):
        with col:
            st.markdown(f"**{step}**")
            st.caption(tool)
            st.success(benefit, icon="✅")

st.divider()

# ─── Data Exploration ──────────────────────────────────────────────────────────
st.subheader("Data Joined")

st.dataframe(
    {
        "Dataset": [
            "Met Office pseudo-obs (hourly, 116 sites, 15 years)",
            "EA Hydrology (flow, level, temperature — 11 NRFA gauges)",
            "Catchment-aggregated precip & temp (11 upstream polygons)",
            "Fish thermal tolerance (10 key Thames species)",
            "Population simulation (3 climate scenarios)",
        ],
        "Insight": [
            "Air temp rising; summer stress hours increasing year-on-year",
            "Water temp lags air by ~2 days; low flow amplifies warming",
            "Catchment-scale precip predicts flow 12–48h later",
            "Most species stressed >26°C; lethal >30–33°C",
            "Under +3°C, Dace suffer 624 thermal deaths/season",
        ],
        "Decision": [
            "When will stress thresholds be crossed?",
            "Which reaches are already warming?",
            "Will flow drop below critical cooling this week?",
            "Which species are at risk right now?",
            "What happens if we don't intervene?",
        ],
    },
    use_container_width=True,
    hide_index=True,
)

# ─── Metrics ───────────────────────────────────────────────────────────────────
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Climate Obs", "15.6M", "Hourly, 2011–2026")
m2.metric("River Readings", "11M+", "Flow, level, temp")
m3.metric("Catchments", "11", "With boundary polygons")
m4.metric("Fish Species", "10", "Thermal thresholds")
m5.metric("Scenarios", "3", "Baseline, +3°C, +5°C")

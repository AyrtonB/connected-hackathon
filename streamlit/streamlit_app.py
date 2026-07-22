import streamlit as st

st.set_page_config(
    page_title="Fried Fish — Thames Climate Risk",
    page_icon="🐟",
    layout="wide",
)

pg = st.navigation([
    st.Page("pages/1_The_Challenge.py", title="The Challenge", icon="🎯"),
    st.Page("pages/2_The_River.py", title="The River", icon="🗺️"),
    st.Page("pages/3_Climate_Signal.py", title="Climate Signal", icon="🌡️"),
    st.Page("pages/4_Fish_at_Risk.py", title="Fish at Risk", icon="🐟"),
])

pg.run()

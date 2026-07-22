import streamlit as st

st.set_page_config(
    page_title="Fried Fish — Thames Climate Risk",
    page_icon="🐟",
    layout="wide",
)

PAGES = {
    "The Challenge": "pages/1_The_Challenge.py",
    "The River": "pages/2_The_River.py",
    "Climate Signal": "pages/3_Climate_Signal.py",
    "Fish at Risk": "pages/4_Fish_at_Risk.py",
}

page = st.sidebar.radio("Navigate", list(PAGES.keys()), index=1)

with open(PAGES[page]) as f:
    exec(f.read())

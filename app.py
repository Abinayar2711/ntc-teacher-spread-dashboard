"""NTC Desk teachers dashboard -- two pages, same numbers.

Charts for the headline read, Tables for the detail. Run with
`streamlit run app.py` (port 8531, set in .streamlit/config.toml).
"""
import streamlit as st

st.set_page_config(page_title="NTC Desk · Teachers", layout="wide")

st.navigation([
    st.Page("pages/charts.py", title="Charts", icon="📊", default=True),
    st.Page("pages/tables.py", title="Tables", icon="🧾"),
    st.Page("pages/by_state.py", title="By state", icon="📍"),
]).run()

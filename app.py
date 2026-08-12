"""NTC Desk teachers dashboard -- two pages, same numbers.

Tables for the detail, Diagrams for the picture. Sign-in first: the file
carries teacher names and locations, so only Art of Living accounts get in.
Run with `streamlit run app.py` (port 8501 locally, to match the redirect URI
registered with Google).
"""
import streamlit as st

st.set_page_config(page_title="NTC Desk · Teachers", layout="wide")

# Must come straight after set_page_config and before anything renders.
from auth_gate import require_login, sidebar_account   # noqa: E402

require_login("NTC Desk · Teachers by region and programme")
sidebar_account()

st.navigation([
    st.Page("pages/tables.py", title="Tables", icon="🧾", default=True),
    st.Page("pages/diagrams.py", title="Diagrams", icon="📊"),
]).run()

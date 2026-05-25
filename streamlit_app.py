"""Streamlit Cloud entrypoint.

Streamlit Community Cloud can point directly to app.py, but this wrapper gives
an obvious default filename for deployment dashboards that expect streamlit_app.py.
"""
from app import *  # noqa: F401,F403

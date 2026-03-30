import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

st.set_page_config(
    page_title="PH Government Budget Analytics",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Global styles — dark theme overrides
# ---------------------------------------------------------------------------
st.markdown("""
    <style>
        [data-testid="stSidebar"] {
            background-color: #0d1117;
        }
        [data-testid="stSidebar"] * {
            color: #e6edf3;
        }
        .main {
            background-color: #0e1117;
        }
        h1, h2, h3, h4 {
            color: #e6edf3;
            font-family: Inter, sans-serif;
        }
        .metric-card {
            background-color: #161b22;
            border: 1px solid #21262d;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
        }
        .metric-value {
            font-size: 1.8rem;
            font-weight: 700;
            color: #58a6ff;
        }
        .metric-label {
            font-size: 0.85rem;
            color: #8b949e;
            margin-top: 4px;
        }
        div[data-testid="stMetric"] {
            background-color: #161b22;
            border: 1px solid #21262d;
            border-radius: 8px;
            padding: 16px;
        }
        div[data-testid="stMetric"] label {
            color: #8b949e;
        }
        div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
            color: #58a6ff;
        }
    </style>
""", unsafe_allow_html=True)

st.sidebar.title("PH Budget Analytics")
st.sidebar.caption("FY2021 General Appropriations Act")
st.sidebar.markdown("---")
st.sidebar.markdown("Navigate using the pages above.")

st.title("Philippine Government Budget Analytics")
st.markdown(
    "Explore FY2021 budget allocations sourced from the Department of Budget "
    "and Management General Appropriations Act."
)
st.markdown("Select a page from the sidebar to begin.")
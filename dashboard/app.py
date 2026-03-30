import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st

st.set_page_config(
    page_title="PhilGAA Analytics Pipeline",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
    <style>
        /* ── Base ── */
        .main, [data-testid="stAppViewContainer"] {
            background-color: #0e1117;
        }
        [data-testid="stSidebar"] {
            background-color: #0d1117;
            border-right: 1px solid #21262d;
        }

        /* ── Typography ── */
        h1, h2, h3, h4, p, span, label {
            font-family: Inter, -apple-system, sans-serif;
            color: #e6edf3;
        }
        .caption-text {
            color: #8b949e;
            font-size: 0.85rem;
        }

        /* ── Metric Cards ── */
        div[data-testid="stMetric"] {
            background-color: #161b22;
            border: 1px solid #21262d;
            border-radius: 10px;
            padding: 20px 24px;
        }
        div[data-testid="stMetric"] label {
            color: #8b949e !important;
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        div[data-testid="stMetricValue"] > div {
        color: #f0b429 !important;
        font-size: 1.75rem;
        font-weight: 700;
        }

        /* ── Slider ── */
        [data-testid="stSlider"] > div > div > div {
            background-color: #1f6feb;
        }

        /* ── Dataframe ── */
        [data-testid="stDataFrame"] {
            border: 1px solid #21262d;
            border-radius: 8px;
        }

        /* ── Divider ── */
        hr {
            border-color: #21262d;
        }

        /* ── Hero block ── */
        .hero-container {
            background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
            border: 1px solid #21262d;
            border-radius: 12px;
            padding: 40px 48px;
            margin-bottom: 32px;
        }
        .hero-title {
            font-size: 2.2rem;
            font-weight: 700;
            color: #e6edf3;
            margin: 0 0 8px 0;
            line-height: 1.2;
        }
        .hero-subtitle {
            font-size: 1rem;
            color: #8b949e;
            margin: 0 0 24px 0;
        }
        .hero-tag {
            display: inline-block;
            background-color: #1f3a5f;
            color: #58a6ff;
            border: 1px solid #1f6feb;
            border-radius: 20px;
            padding: 4px 12px;
            font-size: 0.78rem;
            margin-right: 8px;
            font-family: Inter, sans-serif;
        }
        .stat-row {
            display: flex;
            gap: 32px;
            margin-top: 28px;
        }
        .stat-item {
            text-align: left;
        }
        .stat-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #f0b429;
        }
        .stat-label {
            font-size: 0.78rem;
            color: #8b949e;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        /* ── Sidebar branding ── */
        .sidebar-brand {
            padding: 8px 0 16px 0;
        }
        .sidebar-brand-title {
            font-size: 1rem;
            font-weight: 700;
            color: #e6edf3;
        }
        .sidebar-brand-sub {
            font-size: 0.75rem;
            color: #8b949e;
            margin-top: 2px;
        }
        .sidebar-divider {
            border-top: 1px solid #21262d;
            margin: 12px 0;
        }
        .sidebar-section-label {
            font-size: 0.7rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #6e7681;
            padding: 8px 0 4px 0;
        }
    </style>
""", unsafe_allow_html=True)

# ── Sidebar ──
st.sidebar.markdown("""
    <div class="sidebar-brand">
        <div class="sidebar-brand-title">PhilGAA Analytics</div>
        <div class="sidebar-brand-sub">FY2021 General Appropriations Act</div>
    </div>
    <div class="sidebar-divider"></div>
    <div class="sidebar-section-label">Navigation</div>
""", unsafe_allow_html=True)

# ── Hero landing ──
st.markdown("""
    <div class="hero-container">
        <div class="hero-title">PhilGAA Analytics Pipeline</div>
        <div class="hero-subtitle">
            End-to-end budget intelligence built on the Philippine FY2021
            General Appropriations Act — Department of Budget and Management
        </div>
        <span class="hero-tag">498,342 budget line items</span>
        <span class="hero-tag">PHP 4.51T appropriations</span>
        <span class="hero-tag">375 government agencies</span>
        <span class="hero-tag">37 departments</span>
        <div class="stat-row">
            <div class="stat-item">
                <div class="stat-value">PHP 4.51T</div>
                <div class="stat-label">Total Appropriation</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">375</div>
                <div class="stat-label">Agencies</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">37</div>
                <div class="stat-label">Departments</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">32,461</div>
                <div class="stat-label">Programs</div>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

st.markdown(
    "Select a page from the sidebar to explore budget allocations, "
    "agency rankings, expense class breakdowns, and program-level analysis."
)

st.markdown("---")
st.markdown("""
    <span class="caption-text">
    Data source: Department of Budget and Management — 
    Republic Act No. 11518, General Appropriations Act FY2021 (Volume I-A).
    All amounts in Philippine Peso (PHP).
    </span>
""", unsafe_allow_html=True)
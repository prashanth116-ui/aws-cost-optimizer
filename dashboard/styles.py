"""Shared styles for all dashboard pages."""

import streamlit as st

SHARED_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

* {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

.stApp {
    background: linear-gradient(180deg, #0f1419 0%, #1a1f2e 100%);
}

#MainMenu, footer, header {visibility: hidden;}

.main .block-container {
    padding: 1.5rem 2.5rem;
    max-width: 100%;
}

/* ===== SIDEBAR ===== */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1a1f2e 0%, #0f1419 100%);
    border-right: 1px solid rgba(255, 153, 0, 0.15);
    min-width: 320px !important;
}

[data-testid="stSidebar"] * {
    color: #cbd5e1 !important;
}

[data-testid="stSidebar"] [data-testid="stSidebarNavLink"] {
    padding: 0.9rem 1.25rem !important;
    margin: 0.3rem 0.5rem !important;
    border-radius: 10px !important;
    font-size: 1.05rem !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
    border: 1px solid transparent !important;
    text-transform: capitalize !important;
}

[data-testid="stSidebar"] [data-testid="stSidebarNavLink"]:hover {
    background: rgba(255, 153, 0, 0.1) !important;
    border-color: rgba(255, 153, 0, 0.3) !important;
}

[data-testid="stSidebar"] [data-testid="stSidebarNavLink"]:hover span {
    color: #FF9900 !important;
}

[data-testid="stSidebar"] [data-testid="stSidebarNavLink"][aria-current="page"] {
    background: rgba(255, 153, 0, 0.15) !important;
    border: 1px solid #FF9900 !important;
}

[data-testid="stSidebar"] [data-testid="stSidebarNavLink"][aria-current="page"] span {
    color: #FF9900 !important;
    font-weight: 600 !important;
}

[data-testid="stSidebar"] .stButton button {
    background: linear-gradient(135deg, #FF9900 0%, #e68a00 100%) !important;
    color: #000 !important;
    border: none !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    padding: 0.75rem 1.25rem !important;
    border-radius: 10px !important;
    box-shadow: 0 4px 12px rgba(255, 153, 0, 0.25) !important;
}

[data-testid="stSidebar"] .stButton button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 16px rgba(255, 153, 0, 0.35) !important;
}

[data-testid="stSidebar"] .stRadio label span {
    font-size: 1.02rem !important;
    font-weight: 500 !important;
}

/* ===== PAGE HEADERS ===== */
.page-title {
    font-size: 2.4rem;
    font-weight: 800;
    background: linear-gradient(135deg, #FF9900 0%, #FFB84D 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: -0.5px;
    margin-bottom: 0.25rem;
}

.page-subtitle {
    font-size: 1.1rem;
    font-weight: 500;
    color: #64748b;
    margin-bottom: 1.5rem;
}

.section-title {
    font-size: 1.4rem;
    font-weight: 700;
    color: #f1f5f9;
    margin: 1.75rem 0 1rem 0;
    padding-bottom: 0.5rem;
    border-bottom: 3px solid #FF9900;
    display: inline-block;
}

.chart-title {
    font-size: 1.15rem;
    font-weight: 700;
    color: #e2e8f0;
    margin-bottom: 0.75rem;
    padding-bottom: 0.4rem;
    border-bottom: 2px solid rgba(255, 153, 0, 0.3);
}

/* ===== METRIC CARDS ===== */
.metrics-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 1rem;
    margin: 1.25rem 0 1.75rem 0;
}

.metric-card {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 1.25rem 1rem;
    text-align: center;
    transition: all 0.25s ease;
}

.metric-card:hover {
    background: rgba(255, 255, 255, 0.05);
    border-color: rgba(255, 153, 0, 0.3);
    transform: translateY(-3px);
}

.metric-icon {
    font-size: 1.5rem;
    margin-bottom: 0.4rem;
    display: block;
}

.metric-value {
    font-size: 1.8rem;
    font-weight: 800;
    color: #ffffff;
    line-height: 1.1;
    margin: 0.4rem 0;
}

.metric-value.green { color: #10b981; }
.metric-value.orange { color: #FF9900; }
.metric-value.red { color: #ef4444; }

.metric-label {
    font-size: 0.8rem;
    font-weight: 600;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.75px;
}

/* ===== INFO BOX ===== */
.info-box {
    background: rgba(255, 153, 0, 0.1);
    border: 1px solid rgba(255, 153, 0, 0.3);
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    margin: 1rem 0;
    color: #e2e8f0;
}

.info-box.success {
    background: rgba(16, 185, 129, 0.1);
    border-color: rgba(16, 185, 129, 0.3);
}

.info-box.warning {
    background: rgba(245, 158, 11, 0.1);
    border-color: rgba(245, 158, 11, 0.3);
}

.info-box.error {
    background: rgba(239, 68, 68, 0.1);
    border-color: rgba(239, 68, 68, 0.3);
}

/* ===== DATA TABLES ===== */
.stDataFrame {
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    overflow: hidden;
}

/* ===== TABS ===== */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.5rem;
    background: rgba(255, 255, 255, 0.02);
    padding: 0.4rem;
    border-radius: 12px;
}

.stTabs [data-baseweb="tab"] {
    background: transparent;
    border: none;
    border-radius: 10px;
    padding: 0.8rem 1.5rem;
    font-size: 1rem;
    font-weight: 600;
    color: #64748b;
}

.stTabs [data-baseweb="tab"]:hover {
    background: rgba(255, 153, 0, 0.1);
    color: #FF9900;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #FF9900 0%, #e68a00 100%) !important;
    color: #000 !important;
}

/* ===== EXPANDERS ===== */
.streamlit-expanderHeader {
    background: rgba(255, 255, 255, 0.03) !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    color: #e2e8f0 !important;
}

/* ===== BUTTONS ===== */
.stButton > button {
    background: linear-gradient(135deg, #FF9900 0%, #e68a00 100%);
    color: #000;
    border: none;
    font-weight: 700;
    border-radius: 10px;
    transition: all 0.2s ease;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(255, 153, 0, 0.3);
}

/* ===== METRICS (Native) ===== */
[data-testid="stMetricValue"] {
    font-size: 1.8rem !important;
    font-weight: 800 !important;
    color: #ffffff !important;
}

[data-testid="stMetricLabel"] {
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    color: #94a3b8 !important;
    text-transform: uppercase !important;
}

[data-testid="stMetricDelta"] {
    font-size: 0.9rem !important;
    font-weight: 600 !important;
}

/* ===== DIVIDERS ===== */
hr {
    border-color: rgba(255, 255, 255, 0.1) !important;
    margin: 1.5rem 0 !important;
}

/* ===== SCROLLBAR ===== */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: #0f1419;
}

::-webkit-scrollbar-thumb {
    background: #FF9900;
    border-radius: 4px;
}

/* ===== HEADERS (Native) ===== */
h1, h2, h3 {
    color: #f1f5f9 !important;
}

h1 {
    font-size: 2rem !important;
    font-weight: 800 !important;
    color: #FF9900 !important;
}

h2 {
    font-size: 1.5rem !important;
    font-weight: 700 !important;
}

h3 {
    font-size: 1.2rem !important;
    font-weight: 600 !important;
}
</style>
"""


def inject_styles():
    """Inject shared CSS styles into the page."""
    st.markdown(SHARED_CSS, unsafe_allow_html=True)


def page_header(title, subtitle=None):
    """Render a consistent page header."""
    st.markdown(f'<div class="page-title">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="page-subtitle">{subtitle}</div>', unsafe_allow_html=True)


def section_header(title):
    """Render a section header."""
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)


def chart_header(title):
    """Render a chart header."""
    st.markdown(f'<div class="chart-title">{title}</div>', unsafe_allow_html=True)


def metric_card(icon, value, label, color=""):
    """Render a metric card."""
    return f"""
    <div class="metric-card">
        <span class="metric-icon">{icon}</span>
        <div class="metric-value {color}">{value}</div>
        <div class="metric-label">{label}</div>
    </div>
    """


def metrics_row(metrics):
    """Render a row of metric cards.

    Args:
        metrics: List of tuples (icon, value, label, color)
    """
    cards = "".join([metric_card(m[0], m[1], m[2], m[3] if len(m) > 3 else "") for m in metrics])
    return f'<div class="metrics-row">{cards}</div>'


def info_box(content, box_type="info"):
    """Render an info box."""
    return f'<div class="info-box {box_type}">{content}</div>'

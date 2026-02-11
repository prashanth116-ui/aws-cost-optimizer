"""Streamlit dashboard main application - Enhanced UI."""

import streamlit as st
import pandas as pd
import numpy as np
import sys
import io
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

st.set_page_config(
    page_title="AWS Cost Optimizer",
    page_icon="☁️",
    layout="wide",
    initial_sidebar_state="expanded"
)


def get_theme_css():
    """Get CSS based on current theme."""
    theme = st.session_state.get("theme", "dark")

    if theme == "dark":
        return """
        <style>
        /* ===== DARK THEME ===== */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

        /* Root variables */
        :root {
            --bg-primary: #0f1419;
            --bg-secondary: #1a1f2e;
            --bg-card: rgba(26, 31, 46, 0.8);
            --bg-glass: rgba(255, 255, 255, 0.05);
            --text-primary: #ffffff;
            --text-secondary: #a0aec0;
            --accent: #FF9900;
            --accent-light: #FFB84D;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --border: rgba(255, 255, 255, 0.1);
        }

        /* Global styles */
        .stApp {
            background: linear-gradient(135deg, var(--bg-primary) 0%, #1a1f2e 50%, #0d1117 100%);
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        /* Hide default elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}

        /* Main content area */
        .main .block-container {
            padding: 2rem 3rem;
            max-width: 100%;
        }

        /* ===== SIDEBAR ===== */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #1a1f2e 0%, #0f1419 100%);
            border-right: 1px solid var(--border);
            min-width: 340px !important;
        }

        [data-testid="stSidebar"] > div:first-child {
            padding: 0;
        }

        /* Sidebar navigation links */
        [data-testid="stSidebar"] * {
            color: var(--text-secondary) !important;
        }

        [data-testid="stSidebar"] [data-testid="stSidebarNavLink"] {
            background: transparent !important;
            padding: 1rem 1.5rem !important;
            margin: 0.25rem 0.75rem !important;
            border-radius: 12px !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            font-size: 1.1rem !important;
            font-weight: 500 !important;
            border: 1px solid transparent !important;
        }

        [data-testid="stSidebar"] [data-testid="stSidebarNavLink"]:hover {
            background: rgba(255, 153, 0, 0.1) !important;
            border-color: rgba(255, 153, 0, 0.3) !important;
            transform: translateX(4px);
        }

        [data-testid="stSidebar"] [data-testid="stSidebarNavLink"]:hover span {
            color: var(--accent) !important;
        }

        [data-testid="stSidebar"] [data-testid="stSidebarNavLink"][aria-current="page"] {
            background: linear-gradient(135deg, rgba(255, 153, 0, 0.2) 0%, rgba(255, 153, 0, 0.1) 100%) !important;
            border-color: var(--accent) !important;
            border-left: 4px solid var(--accent) !important;
        }

        [data-testid="stSidebar"] [data-testid="stSidebarNavLink"][aria-current="page"] span {
            color: var(--accent) !important;
            font-weight: 600 !important;
        }

        /* Sidebar labels and inputs */
        [data-testid="stSidebar"] label {
            font-size: 1.05rem !important;
            font-weight: 600 !important;
            color: var(--text-primary) !important;
        }

        [data-testid="stSidebar"] .stRadio label span {
            font-size: 1.1rem !important;
            padding: 0.75rem 0 !important;
        }

        [data-testid="stSidebar"] .stButton button {
            background: linear-gradient(135deg, var(--accent) 0%, #e68a00 100%) !important;
            color: #000 !important;
            border: none !important;
            font-weight: 700 !important;
            font-size: 1.05rem !important;
            padding: 0.75rem 1.5rem !important;
            border-radius: 12px !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 4px 15px rgba(255, 153, 0, 0.3) !important;
        }

        [data-testid="stSidebar"] .stButton button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(255, 153, 0, 0.4) !important;
        }

        /* ===== GLASSMORPHISM CARDS ===== */
        .glass-card {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 1.5rem;
            transition: all 0.3s ease;
        }

        .glass-card:hover {
            background: rgba(255, 255, 255, 0.05);
            border-color: rgba(255, 153, 0, 0.3);
            transform: translateY(-4px);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
        }

        /* ===== ANIMATED KPI CARDS ===== */
        .kpi-card {
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.02) 100%);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 1.75rem;
            text-align: center;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }

        .kpi-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, var(--accent), var(--accent-light));
            opacity: 0;
            transition: opacity 0.3s ease;
        }

        .kpi-card:hover {
            transform: translateY(-8px) scale(1.02);
            box-shadow: 0 25px 50px rgba(255, 153, 0, 0.15);
            border-color: var(--accent);
        }

        .kpi-card:hover::before {
            opacity: 1;
        }

        .kpi-icon {
            font-size: 2.5rem;
            margin-bottom: 0.75rem;
            display: block;
            filter: drop-shadow(0 4px 8px rgba(255, 153, 0, 0.3));
        }

        .kpi-value {
            font-size: 2.5rem;
            font-weight: 800;
            color: var(--text-primary);
            margin: 0.5rem 0;
            background: linear-gradient(135deg, #fff 0%, #a0aec0 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .kpi-label {
            font-size: 0.95rem;
            font-weight: 600;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 1.5px;
        }

        .kpi-delta {
            font-size: 1rem;
            font-weight: 600;
            margin-top: 0.5rem;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            display: inline-block;
        }

        .kpi-delta.positive {
            background: rgba(16, 185, 129, 0.2);
            color: var(--success);
        }

        .kpi-delta.negative {
            background: rgba(239, 68, 68, 0.2);
            color: var(--danger);
        }

        /* ===== HEADERS ===== */
        .main-header {
            font-size: 3.5rem;
            font-weight: 800;
            background: linear-gradient(135deg, var(--accent) 0%, #FFD700 50%, var(--accent) 100%);
            background-size: 200% auto;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: gradient-shift 3s ease infinite;
            margin-bottom: 0.5rem;
            letter-spacing: -1px;
        }

        @keyframes gradient-shift {
            0%, 100% { background-position: 0% center; }
            50% { background-position: 100% center; }
        }

        .sub-header {
            color: var(--text-secondary);
            font-size: 1.3rem;
            margin-bottom: 2rem;
            font-weight: 500;
        }

        .section-header {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--text-primary);
            margin: 2rem 0 1rem 0;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid var(--accent);
            display: inline-block;
        }

        /* Sidebar headers */
        .sidebar-header {
            color: var(--accent) !important;
            font-size: 1.4rem !important;
            font-weight: 700 !important;
            margin: 2rem 0 1rem 0 !important;
            padding: 0.5rem 0 !important;
            border-bottom: 3px solid var(--accent) !important;
            letter-spacing: 0.5px !important;
        }

        .sidebar-subheader {
            color: var(--text-secondary) !important;
            font-size: 1rem !important;
            font-weight: 600 !important;
            margin-top: 1.5rem !important;
            text-transform: uppercase !important;
            letter-spacing: 2px !important;
        }

        /* ===== SERVICE CARDS ===== */
        .service-card {
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.02) 100%);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            padding: 2rem;
            height: 220px;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }

        .service-card::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 100%;
            background: linear-gradient(180deg, transparent 0%, rgba(0,0,0,0.3) 100%);
            pointer-events: none;
        }

        .service-card:hover {
            transform: translateY(-10px) scale(1.02);
            box-shadow: 0 30px 60px rgba(0, 0, 0, 0.4);
        }

        .service-card h3 {
            margin: 0 0 0.75rem 0;
            font-size: 1.4rem;
            font-weight: 700;
            position: relative;
            z-index: 1;
        }

        .service-card p {
            font-size: 1rem;
            opacity: 0.9;
            position: relative;
            z-index: 1;
            line-height: 1.6;
        }

        .service-card .savings-badge {
            position: absolute;
            bottom: 1.5rem;
            left: 2rem;
            background: rgba(255, 255, 255, 0.15);
            padding: 0.4rem 1rem;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 600;
            z-index: 1;
        }

        /* ===== TABS ===== */
        .stTabs [data-baseweb="tab-list"] {
            gap: 12px;
            background: transparent;
            padding: 0.5rem;
        }

        .stTabs [data-baseweb="tab"] {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 1rem 2rem;
            font-size: 1.1rem;
            font-weight: 600;
            color: var(--text-secondary);
            transition: all 0.3s ease;
        }

        .stTabs [data-baseweb="tab"]:hover {
            background: rgba(255, 153, 0, 0.1);
            border-color: rgba(255, 153, 0, 0.3);
        }

        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, var(--accent) 0%, #e68a00 100%) !important;
            color: #000 !important;
            border-color: var(--accent) !important;
            box-shadow: 0 4px 15px rgba(255, 153, 0, 0.3);
        }

        /* ===== METRICS ===== */
        [data-testid="stMetricValue"] {
            font-size: 2.5rem !important;
            font-weight: 800 !important;
            color: var(--text-primary) !important;
        }

        [data-testid="stMetricLabel"] {
            font-size: 1rem !important;
            font-weight: 600 !important;
            color: var(--text-secondary) !important;
            text-transform: uppercase !important;
            letter-spacing: 1px !important;
        }

        [data-testid="stMetricDelta"] {
            font-size: 1.1rem !important;
            font-weight: 600 !important;
        }

        /* ===== DATA TABLES ===== */
        .stDataFrame {
            border: 1px solid var(--border);
            border-radius: 16px;
            overflow: hidden;
        }

        .stDataFrame [data-testid="stDataFrameContainer"] {
            background: rgba(255, 255, 255, 0.02);
        }

        /* ===== BUTTONS ===== */
        .stButton > button {
            background: linear-gradient(135deg, var(--accent) 0%, #e68a00 100%);
            color: #000;
            border: none;
            font-weight: 700;
            font-size: 1rem;
            padding: 0.75rem 2rem;
            border-radius: 12px;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(255, 153, 0, 0.2);
        }

        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(255, 153, 0, 0.35);
        }

        /* ===== ALERTS ===== */
        .stAlert {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border);
            border-radius: 12px;
        }

        /* ===== DATA SOURCE INDICATORS ===== */
        .data-indicator {
            padding: 0.75rem 1.5rem;
            border-radius: 12px;
            margin-bottom: 1.5rem;
            text-align: center;
            font-weight: 600;
            font-size: 1rem;
            backdrop-filter: blur(10px);
        }

        .data-indicator.sample {
            background: linear-gradient(135deg, rgba(245, 158, 11, 0.2) 0%, rgba(245, 158, 11, 0.1) 100%);
            border: 1px solid rgba(245, 158, 11, 0.3);
            color: var(--warning);
        }

        .data-indicator.live {
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.2) 0%, rgba(16, 185, 129, 0.1) 100%);
            border: 1px solid rgba(16, 185, 129, 0.3);
            color: var(--success);
        }

        .data-indicator.uploaded {
            background: linear-gradient(135deg, rgba(59, 130, 246, 0.2) 0%, rgba(59, 130, 246, 0.1) 100%);
            border: 1px solid rgba(59, 130, 246, 0.3);
            color: #3b82f6;
        }

        /* ===== EXPANDERS ===== */
        .streamlit-expanderHeader {
            background: rgba(255, 255, 255, 0.05) !important;
            border-radius: 12px !important;
            font-weight: 600 !important;
        }

        /* ===== SCROLLBAR ===== */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }

        ::-webkit-scrollbar-track {
            background: var(--bg-secondary);
        }

        ::-webkit-scrollbar-thumb {
            background: var(--accent);
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: var(--accent-light);
        }

        /* ===== ANIMATIONS ===== */
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .animate-in {
            animation: fadeInUp 0.5s ease forwards;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }

        .pulse {
            animation: pulse 2s ease-in-out infinite;
        }

        /* ===== CHARTS ===== */
        .js-plotly-plot .plotly .modebar {
            background: var(--bg-secondary) !important;
            border-radius: 8px;
        }
        </style>
        """
    else:  # Light theme
        return """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

        :root {
            --bg-primary: #f8fafc;
            --bg-secondary: #ffffff;
            --bg-card: rgba(255, 255, 255, 0.9);
            --text-primary: #1e293b;
            --text-secondary: #64748b;
            --accent: #FF9900;
            --accent-light: #FFB84D;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --border: rgba(0, 0, 0, 0.1);
        }

        .stApp {
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #232F3E 0%, #1a242f 100%);
            min-width: 340px !important;
        }

        [data-testid="stSidebar"] * {
            color: #ffffff !important;
        }

        .glass-card {
            background: rgba(255, 255, 255, 0.8);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(0, 0, 0, 0.1);
            border-radius: 20px;
            padding: 1.5rem;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
        }

        .kpi-card {
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            border: 1px solid rgba(0, 0, 0, 0.08);
            border-radius: 20px;
            padding: 1.75rem;
            text-align: center;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.08);
            transition: all 0.4s ease;
        }

        .kpi-card:hover {
            transform: translateY(-8px);
            box-shadow: 0 20px 60px rgba(255, 153, 0, 0.15);
        }

        .kpi-value {
            font-size: 2.5rem;
            font-weight: 800;
            color: var(--text-primary);
        }

        .main-header {
            font-size: 3.5rem;
            font-weight: 800;
            background: linear-gradient(135deg, #232F3E 0%, var(--accent) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .section-header {
            color: var(--text-primary);
        }

        .sidebar-header {
            color: var(--accent) !important;
        }

        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, var(--accent) 0%, #e68a00 100%) !important;
            color: white !important;
        }
        </style>
        """


# Inject theme CSS
def inject_css():
    st.markdown(get_theme_css(), unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables."""
    if "implementation_status" not in st.session_state:
        st.session_state["implementation_status"] = load_persisted_state("implementation_status", {})
    if "thresholds" not in st.session_state:
        st.session_state["thresholds"] = load_persisted_state("thresholds", {
            "cpu_oversized": 40,
            "cpu_undersized": 70,
            "mem_oversized": 50,
            "mem_undersized": 75,
        })
    if "selected_service" not in st.session_state:
        st.session_state["selected_service"] = "EC2"
    if "data_source" not in st.session_state:
        st.session_state["data_source"] = "none"
    if "theme" not in st.session_state:
        st.session_state["theme"] = "dark"


def get_state_file_path():
    """Get path for persisted state file."""
    return Path(__file__).parent / ".dashboard_state.json"


def load_persisted_state(key: str, default):
    """Load persisted state from file."""
    import json
    state_file = get_state_file_path()
    if state_file.exists():
        try:
            with open(state_file, "r") as f:
                all_state = json.load(f)
                return all_state.get(key, default)
        except Exception:
            pass
    return default


def save_persisted_state():
    """Save session state to file for persistence."""
    import json
    state_file = get_state_file_path()
    try:
        if state_file.exists():
            with open(state_file, "r") as f:
                all_state = json.load(f)
        else:
            all_state = {}

        all_state["implementation_status"] = st.session_state.get("implementation_status", {})
        all_state["thresholds"] = st.session_state.get("thresholds", {})

        with open(state_file, "w") as f:
            json.dump(all_state, f, indent=2)
        return True
    except Exception as e:
        st.error(f"Failed to save state: {e}")
        return False


def render_kpi_card(icon, value, label, delta=None, delta_type="positive"):
    """Render an animated KPI card."""
    delta_html = ""
    if delta:
        delta_class = "positive" if delta_type == "positive" else "negative"
        delta_html = f'<div class="kpi-delta {delta_class}">{delta}</div>'

    return f"""
    <div class="kpi-card">
        <span class="kpi-icon">{icon}</span>
        <div class="kpi-value">{value}</div>
        <div class="kpi-label">{label}</div>
        {delta_html}
    </div>
    """


def render_data_source_indicator():
    """Render a visual indicator for the data source."""
    source = st.session_state.get("data_source", "none")

    indicators = {
        "sample": ("sample", "⚠️ SAMPLE DATA - Demo/synthetic data for illustration"),
        "uploaded": ("uploaded", "📤 Uploaded Report Data"),
        "live": ("live", "🔗 Live AWS Connection - Real-time data")
    }

    if source in indicators:
        css_class, text = indicators[source]
        st.markdown(f'<div class="data-indicator {css_class}">{text}</div>', unsafe_allow_html=True)


def render_sidebar():
    """Render the enhanced sidebar."""
    with st.sidebar:
        # Logo and title
        st.markdown("""
            <div style="text-align: center; padding: 2rem 0 1.5rem 0;">
                <div style="font-size: 4rem; margin-bottom: 0.5rem; filter: drop-shadow(0 4px 8px rgba(255, 153, 0, 0.4));">☁️</div>
                <h1 style="color: #FF9900; margin: 0; font-weight: 800; font-size: 1.6rem; letter-spacing: -0.5px;">
                    AWS Cost Optimizer
                </h1>
                <p style="color: #a0aec0; font-size: 0.95rem; margin-top: 0.5rem; font-weight: 500;">
                    Enterprise Cloud Optimization
                </p>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # Theme toggle
        st.markdown('<p class="sidebar-header">🎨 Theme</p>', unsafe_allow_html=True)
        theme = st.radio(
            "Select theme:",
            ["🌙 Dark Mode", "☀️ Light Mode"],
            index=0 if st.session_state.get("theme") == "dark" else 1,
            label_visibility="collapsed"
        )
        new_theme = "dark" if "Dark" in theme else "light"
        if new_theme != st.session_state.get("theme"):
            st.session_state["theme"] = new_theme
            st.rerun()

        st.markdown("---")

        # AWS Services Section
        st.markdown('<p class="sidebar-header">🔧 AWS Services</p>', unsafe_allow_html=True)

        services = [
            "💻 EC2 Instances",
            "🗄️ RDS Databases",
            "💾 EBS Volumes",
            "⚡ ElastiCache",
            "λ Lambda Functions",
            "🪣 S3 Buckets"
        ]

        service = st.radio(
            "Select Service to Analyze:",
            options=services,
            index=0,
            label_visibility="collapsed"
        )
        st.session_state["selected_service"] = service.split()[1] if len(service.split()) > 1 else service.split()[0]

        st.markdown("---")

        # Data Source Section
        st.markdown('<p class="sidebar-header">📂 Data Source</p>', unsafe_allow_html=True)

        source = st.radio(
            "Select data source:",
            ["📤 Upload Report", "🔗 Live AWS Connection"],
            label_visibility="collapsed"
        )

        if "Upload" in source:
            uploaded_file = st.file_uploader(
                "Drop your Excel report here",
                type=["xlsx", "xls"],
                label_visibility="collapsed"
            )
            if uploaded_file:
                st.session_state["report_file"] = uploaded_file
                st.session_state["data_source"] = "uploaded"
                st.success("✅ Report loaded!")
        else:
            st.markdown('<p class="sidebar-subheader">Connection Settings</p>', unsafe_allow_html=True)

            region = st.selectbox(
                "AWS Region",
                ["us-east-1", "us-east-2", "us-west-1", "us-west-2",
                 "eu-west-1", "eu-central-1", "ap-southeast-1", "ap-northeast-1"],
                label_visibility="collapsed"
            )
            st.session_state["aws_region"] = region

            months = st.slider("Analysis Period (months)", min_value=1, max_value=12, value=3)
            st.session_state["analysis_months"] = months

            if st.button("🚀 Run Analysis", type="primary", use_container_width=True):
                st.session_state["run_analysis"] = True
                st.session_state["data_source"] = "live"

            st.markdown('<p class="sidebar-subheader">Quick Demo</p>', unsafe_allow_html=True)
            if st.button("📊 Load Sample Data", use_container_width=True):
                load_sample_data()
                st.rerun()

        st.markdown("---")

        # Quick Filters
        st.markdown('<p class="sidebar-header">🎯 Filters</p>', unsafe_allow_html=True)

        with st.expander("⚙️ Classification Thresholds", expanded=False):
            cpu_over = st.slider("CPU Oversized below (%):", 10, 60,
                                st.session_state["thresholds"]["cpu_oversized"])
            cpu_under = st.slider("CPU Undersized above (%):", 50, 95,
                                 st.session_state["thresholds"]["cpu_undersized"])
            mem_over = st.slider("Memory Oversized below (%):", 10, 70,
                                st.session_state["thresholds"]["mem_oversized"])
            mem_under = st.slider("Memory Undersized above (%):", 50, 95,
                                 st.session_state["thresholds"]["mem_undersized"])

            if st.button("Apply Thresholds", use_container_width=True):
                st.session_state["thresholds"] = {
                    "cpu_oversized": cpu_over,
                    "cpu_undersized": cpu_under,
                    "mem_oversized": mem_over,
                    "mem_undersized": mem_under,
                }
                st.success("✅ Updated!")
                st.rerun()

        st.markdown("---")

        # Version info
        st.markdown("""
            <div style="text-align: center; padding: 1.5rem; margin-top: 2rem; border-top: 1px solid rgba(255,255,255,0.1);">
                <p style="font-size: 1rem; margin: 0; color: #FF9900; font-weight: 700;">Version 2.0</p>
                <p style="font-size: 0.85rem; margin: 0.5rem 0 0 0; color: #a0aec0;">
                    EC2 • RDS • EBS • Lambda • S3
                </p>
                <p style="font-size: 0.75rem; margin: 0.5rem 0 0 0; color: #666;">
                    Powered by Claude AI
                </p>
            </div>
        """, unsafe_allow_html=True)


def load_sample_data():
    """Load sample data for demo purposes."""
    st.session_state["sample_df"] = generate_sample_dataframe()
    st.session_state["data_source"] = "sample"


def generate_sample_dataframe():
    """Generate sample DataFrame for demo."""
    import random

    instance_types = ["t3.micro", "t3.small", "t3.medium", "t3.large", "m5.large", "m5.xlarge", "m5.2xlarge", "r5.large", "c5.large", "c5.xlarge"]
    environments = ["Production", "Staging", "Development"]

    data = []
    for i in range(25):
        env = random.choice(environments)
        instance_type = random.choice(instance_types)

        classification = random.choice(["oversized", "right_sized", "undersized"])
        if classification == "oversized":
            cpu_p95 = random.uniform(10, 35)
            mem_p95 = random.uniform(15, 45)
            monthly_savings = random.uniform(50, 500)
        elif classification == "undersized":
            cpu_p95 = random.uniform(75, 95)
            mem_p95 = random.uniform(80, 95)
            monthly_savings = 0
        else:
            cpu_p95 = random.uniform(40, 65)
            mem_p95 = random.uniform(50, 70)
            monthly_savings = 0

        current_monthly = random.uniform(50, 1000)

        data.append({
            "server_id": f"i-sample{i:04d}",
            "hostname": f"sample-server-{i:02d}",
            "instance_type": instance_type,
            "vcpu": {"t3.micro": 2, "t3.small": 2, "t3.medium": 2, "t3.large": 2, "m5.large": 2, "m5.xlarge": 4, "m5.2xlarge": 8, "r5.large": 2, "c5.large": 2, "c5.xlarge": 4}.get(instance_type, 2),
            "memory_gb": {"t3.micro": 1, "t3.small": 2, "t3.medium": 4, "t3.large": 8, "m5.large": 8, "m5.xlarge": 16, "m5.2xlarge": 32, "r5.large": 16, "c5.large": 4, "c5.xlarge": 8}.get(instance_type, 4),
            "Environment": env,
            "GSI": random.choice(["WebPlatform", "Database", "Analytics", "API", "Backend"]),
            "cpu_avg": cpu_p95 * 0.6,
            "cpu_p95": cpu_p95,
            "memory_avg": mem_p95 * 0.7,
            "memory_p95": mem_p95,
            "classification": classification,
            "recommended_type": None if classification == "right_sized" else (instance_types[instance_types.index(instance_type) - 1] if classification == "oversized" and instance_types.index(instance_type) > 0 else instance_types[min(instance_types.index(instance_type) + 1, len(instance_types) - 1)]),
            "current_monthly": current_monthly,
            "recommended_monthly": current_monthly - monthly_savings,
            "monthly_savings": monthly_savings,
            "confidence": random.uniform(0.6, 0.95),
            "risk_level": random.choice(["low", "medium", "high"]),
            "has_contention": classification == "undersized" and random.random() > 0.5,
            "contention_events": random.randint(0, 10) if classification == "undersized" else 0,
        })

    return pd.DataFrame(data)


def run_live_analysis():
    """Run live analysis against AWS."""
    region = st.session_state.get("aws_region", "us-east-1")

    with st.spinner("Connecting to AWS..."):
        try:
            from src.utils.helpers import load_credentials, validate_credentials
            from src.clients.aws_client import AWSClient

            creds = load_credentials()
            cred_status = validate_credentials(creds)

            if not cred_status["aws_configured"]:
                st.error("AWS credentials not configured. Please set up credentials in config/credentials.yaml")
                return None

            aws_creds = creds.get("aws", {})
            aws_client = AWSClient(
                access_key_id=aws_creds.get("access_key_id"),
                secret_access_key=aws_creds.get("secret_access_key"),
                region=region,
                profile_name=aws_creds.get("profile_name")
            )

            st.info("Fetching EC2 instances...")
            instances = aws_client.get_instances()

            if not instances:
                st.warning("No EC2 instances found in the selected region.")
                return None

            data = []
            for instance in instances:
                data.append({
                    "server_id": instance.get("instance_id", ""),
                    "hostname": instance.get("name", instance.get("private_ip", "")),
                    "instance_type": instance.get("instance_type", ""),
                    "Environment": instance.get("tags", {}).get("Environment", "Unknown"),
                    "GSI": instance.get("tags", {}).get("GSI", "Unknown"),
                    "cpu_p95": None,
                    "memory_p95": None,
                    "classification": "unknown",
                    "current_monthly": 0,
                    "monthly_savings": 0,
                })

            df = pd.DataFrame(data)
            st.success(f"Loaded {len(df)} instances from AWS!")
            return df

        except ImportError as e:
            st.error(f"Missing dependency: {e}")
            return None
        except Exception as e:
            st.error(f"Failed to connect: {e}")
            return None


def main():
    init_session_state()
    inject_css()
    render_sidebar()

    # Main header
    st.markdown('<div class="main-header animate-in">AWS Cost Optimizer</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-header">Analyzing: {st.session_state.get("selected_service", "EC2")} Resources</div>', unsafe_allow_html=True)

    render_data_source_indicator()

    if st.session_state.get("run_analysis"):
        df = run_live_analysis()
        if df is not None:
            st.session_state["live_df"] = df
            st.session_state["data_source"] = "live"
        st.session_state["run_analysis"] = False

    if "report_file" in st.session_state or "sample_df" in st.session_state or "live_df" in st.session_state:
        display_dashboard()
    else:
        display_welcome()


def display_welcome():
    """Display welcome page when no data is loaded."""
    st.markdown('<div class="section-header">🎯 Supported AWS Services</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    services = [
        (col1, "#FF9900", "#FF6600", "💻", "EC2 Instances", "Analyze compute utilization, rightsize instances, and identify Graviton migration opportunities.", "Up to 40%"),
        (col1, "#3B48CC", "#2E3AB5", "🗄️", "RDS Databases", "Optimize database instances, identify idle DBs, and recommend Reserved Instance coverage.", "Up to 50%"),
        (col2, "#1ABC9C", "#16A085", "💾", "EBS Volumes", "Find unattached volumes, optimize IOPS provisioning, and identify gp2 to gp3 migrations.", "Up to 30%"),
        (col2, "#9B59B6", "#8E44AD", "⚡", "ElastiCache", "Analyze cache hit rates, optimize node types, and identify underutilized clusters.", "Up to 35%"),
        (col3, "#E74C3C", "#C0392B", "λ", "Lambda Functions", "Optimize memory allocation, identify over-provisioned functions, and reduce costs.", "Up to 25%"),
        (col3, "#34495E", "#2C3E50", "🪣", "S3 Buckets", "Analyze storage classes, implement lifecycle policies, and optimize request patterns.", "Up to 70%"),
    ]

    for i, (col, c1, c2, icon, title, desc, savings) in enumerate(services):
        with col:
            st.markdown(f"""
            <div class="service-card" style="background: linear-gradient(135deg, {c1} 0%, {c2} 100%); color: white; margin-bottom: 1rem;">
                <h3>{icon} {title}</h3>
                <p>{desc}</p>
                <div class="savings-badge">Savings: {savings}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="section-header">🚀 Getting Started</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="glass-card">
            <ol style="font-size: 1.1rem; line-height: 2;">
                <li><strong>Select a Service</strong> from the sidebar</li>
                <li><strong>Upload a Report</strong> or connect to AWS</li>
                <li><strong>Review Recommendations</strong> and savings</li>
                <li><strong>Export</strong> Terraform/CLI commands</li>
            </ol>
            <p style="margin-top: 1rem; padding: 1rem; background: rgba(255, 153, 0, 0.1); border-radius: 8px; border-left: 4px solid #FF9900;">
                <strong>💡 Tip:</strong> Start with EC2 instances for the biggest impact on most AWS bills.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="section-header">📊 Quick Demo</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="glass-card">
            <p style="font-size: 1.1rem; margin-bottom: 1.5rem;">
                No data loaded yet. Click the button below to load sample data and explore the dashboard.
            </p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("📊 Load Sample Data Now", type="primary", use_container_width=True):
            load_sample_data()
            st.rerun()


def display_dashboard():
    """Display the main dashboard with analysis results."""
    df = None

    if "report_file" in st.session_state:
        try:
            report_file = st.session_state["report_file"]
            if isinstance(report_file, (str, Path)):
                df = pd.read_excel(report_file, sheet_name="Server Details")
            else:
                df = pd.read_excel(report_file, sheet_name="Server Details")
            df = normalize_column_names(df)
        except Exception as e:
            st.error(f"Failed to read report: {e}")
            return
    elif "sample_df" in st.session_state:
        df = st.session_state["sample_df"]
    elif "live_df" in st.session_state:
        df = st.session_state["live_df"]
    else:
        st.warning("No data loaded.")
        return

    if df is None or len(df) == 0:
        st.warning("No data available.")
        return

    if "server_id" not in df.columns and "hostname" in df.columns:
        df["server_id"] = df["hostname"]

    df = reclassify_with_thresholds(df)
    class_col = "classification"

    # Calculate summary stats
    total_spend = df["current_monthly"].sum() if "current_monthly" in df.columns else 0
    total_savings = df[df["monthly_savings"] > 0]["monthly_savings"].sum() if "monthly_savings" in df.columns else 0
    savings_pct = (total_savings / total_spend * 100) if total_spend > 0 else 0

    # KPI Cards
    st.markdown('<div class="section-header">📊 Key Metrics</div>', unsafe_allow_html=True)

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.markdown(render_kpi_card("📦", len(df), "Total Resources"), unsafe_allow_html=True)
    with col2:
        st.markdown(render_kpi_card("💰", f"${total_spend:,.0f}", "Monthly Spend"), unsafe_allow_html=True)
    with col3:
        st.markdown(render_kpi_card("💵", f"${total_savings:,.0f}", "Potential Savings", f"-{savings_pct:.1f}%", "positive"), unsafe_allow_html=True)
    with col4:
        oversized = len(df[df[class_col] == "oversized"])
        st.markdown(render_kpi_card("📉", oversized, "Oversized"), unsafe_allow_html=True)
    with col5:
        undersized = len(df[df[class_col] == "undersized"])
        st.markdown(render_kpi_card("📈", undersized, "Undersized"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Resource Analysis",
        "💡 Recommendations",
        "💰 Cost Breakdown",
        "⚠️ Contention"
    ])

    with tab1:
        display_server_analysis(df, class_col)

    with tab2:
        display_recommendations(df, class_col)

    with tab3:
        display_cost_breakdown(df)

    with tab4:
        display_contention(df)


def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names to expected format."""
    column_mapping = {
        "Server": "hostname",
        "Instance ID": "server_id",
        "Instance Type": "instance_type",
        "Current Type": "instance_type",
        "CPU P95 %": "cpu_p95",
        "Mem P95 %": "memory_p95",
        "Classification": "classification",
        "Recommended Type": "recommended_type",
        "Monthly Savings": "monthly_savings",
        "Current Monthly": "current_monthly",
        "Confidence": "confidence",
        "Risk Level": "risk_level",
        "Has Contention": "has_contention",
        "Contention Events": "contention_events",
    }

    rename_dict = {old: new for old, new in column_mapping.items() if old in df.columns}
    if rename_dict:
        df = df.rename(columns=rename_dict)

    return df


def reclassify_with_thresholds(df):
    """Reclassify resources based on custom thresholds."""
    thresholds = st.session_state["thresholds"]

    def classify_row(row):
        cpu = row.get("cpu_p95")
        mem = row.get("memory_p95")

        if pd.isna(cpu) and pd.isna(mem):
            return row.get("classification", "unknown")

        cpu_val = cpu if pd.notna(cpu) else 50
        mem_val = mem if pd.notna(mem) else 50

        if cpu_val > thresholds["cpu_undersized"] or mem_val > thresholds["mem_undersized"]:
            return "undersized"

        if cpu_val < thresholds["cpu_oversized"] and mem_val < thresholds["mem_oversized"]:
            return "oversized"

        return "right_sized"

    df["classification"] = df.apply(classify_row, axis=1)
    return df


def display_server_analysis(df, class_col="classification"):
    """Display resource analysis tab."""
    import plotly.express as px
    import plotly.graph_objects as go

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("#### Classification Breakdown")
        if class_col in df.columns:
            class_counts = df[class_col].value_counts()
            colors = {'oversized': '#10b981', 'right_sized': '#6b7280', 'undersized': '#ef4444', 'unknown': '#f59e0b'}

            fig = go.Figure(data=[go.Pie(
                labels=class_counts.index,
                values=class_counts.values,
                hole=0.65,
                marker_colors=[colors.get(x, '#6b7280') for x in class_counts.index]
            )])

            fig.update_layout(
                height=350,
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2),
                annotations=[dict(text=f'{len(df)}', x=0.5, y=0.5, font_size=32, font_weight='bold', showarrow=False)],
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#a0aec0')
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### Resource Utilization Map")
        thresholds = st.session_state["thresholds"]

        if "cpu_p95" in df.columns and "memory_p95" in df.columns:
            fig = px.scatter(
                df,
                x="cpu_p95",
                y="memory_p95",
                color=class_col,
                size="current_monthly" if "current_monthly" in df.columns else None,
                hover_data=["hostname", "instance_type"],
                color_discrete_map={
                    "oversized": "#10b981",
                    "right_sized": "#6b7280",
                    "undersized": "#ef4444",
                    "unknown": "#f59e0b"
                }
            )

            fig.add_shape(type="rect", x0=0, y0=0,
                         x1=thresholds["cpu_oversized"], y1=thresholds["mem_oversized"],
                         fillcolor="rgba(16, 185, 129, 0.1)", line=dict(width=0))

            fig.update_layout(
                height=350,
                xaxis_title="CPU P95 (%)",
                yaxis_title="Memory P95 (%)",
                xaxis=dict(range=[0, 100]),
                yaxis=dict(range=[0, 100]),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#a0aec0')
            )
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Resource Details")
    cols = ["hostname", "instance_type", "cpu_p95", "memory_p95", class_col, "monthly_savings"]
    available = [c for c in cols if c in df.columns]

    st.dataframe(
        df[available].sort_values("monthly_savings", ascending=False) if "monthly_savings" in df.columns else df[available],
        use_container_width=True,
        height=400,
        column_config={
            "monthly_savings": st.column_config.NumberColumn("Savings", format="$%.2f"),
            "cpu_p95": st.column_config.NumberColumn("CPU P95 %", format="%.1f"),
            "memory_p95": st.column_config.NumberColumn("Mem P95 %", format="%.1f"),
        }
    )


def display_recommendations(df, class_col="classification"):
    """Display recommendations."""
    if "recommended_type" not in df.columns:
        st.info("Recommendation data not available for this dataset.")
        return

    recs_df = df[df["recommended_type"].notna()].copy()

    if len(recs_df) == 0:
        st.success("🎉 All resources are appropriately sized!")
        return

    recs_df = recs_df.sort_values("monthly_savings", ascending=False)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📋 Total Recommendations", len(recs_df))
    with col2:
        total_savings = recs_df["monthly_savings"].sum()
        st.metric("💵 Potential Savings", f"${total_savings:,.0f}/mo")
    with col3:
        yearly = total_savings * 12
        st.metric("📅 Annual Savings", f"${yearly:,.0f}")

    st.markdown("---")

    cols = ["hostname", "instance_type", "recommended_type", "monthly_savings", "confidence", "risk_level"]
    available = [c for c in cols if c in recs_df.columns]

    st.dataframe(
        recs_df[available].head(20),
        use_container_width=True,
        column_config={
            "monthly_savings": st.column_config.NumberColumn("Monthly Savings", format="$%.2f"),
            "confidence": st.column_config.ProgressColumn("Confidence", format="%.0f%%", min_value=0, max_value=1),
        },
        hide_index=True
    )


def display_cost_breakdown(df):
    """Display cost analysis."""
    import plotly.graph_objects as go

    if "current_monthly" not in df.columns:
        st.info("Cost data not available.")
        return

    current = df["current_monthly"].sum()
    savings = df[df["monthly_savings"] > 0]["monthly_savings"].sum() if "monthly_savings" in df.columns else 0
    optimized = current - savings

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Current vs. Optimized Spend")
        fig = go.Figure(data=[
            go.Bar(name='Current', x=['Monthly Spend'], y=[current], marker_color='#ef4444'),
            go.Bar(name='Optimized', x=['Monthly Spend'], y=[optimized], marker_color='#10b981')
        ])
        fig.update_layout(
            height=300,
            barmode='group',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#a0aec0')
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### 12-Month Savings Projection")
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        cumulative = [savings * (i+1) for i in range(12)]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=months, y=cumulative,
            mode='lines+markers',
            fill='tozeroy',
            fillcolor='rgba(255, 153, 0, 0.2)',
            line=dict(color='#FF9900', width=3)
        ))
        fig.update_layout(
            height=300,
            yaxis_title="Cumulative Savings ($)",
            yaxis_tickformat="$,.0f",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#a0aec0')
        )
        st.plotly_chart(fig, use_container_width=True)


def display_contention(df):
    """Display contention analysis."""
    if "has_contention" not in df.columns:
        st.info("Contention data not available.")
        return

    contention_df = df[df["has_contention"] == True]

    if len(contention_df) == 0:
        st.success("✅ No resource contention detected!")
        return

    st.warning(f"⚠️ Found {len(contention_df)} resources with contention issues")

    cols = ["hostname", "instance_type", "contention_events", "cpu_p95", "memory_p95"]
    available = [c for c in cols if c in contention_df.columns]

    st.dataframe(
        contention_df[available].sort_values("contention_events", ascending=False) if "contention_events" in contention_df.columns else contention_df[available],
        use_container_width=True
    )


if __name__ == "__main__":
    main()

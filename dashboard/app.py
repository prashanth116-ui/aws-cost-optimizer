"""Streamlit dashboard - Professional & Clean UI."""

import streamlit as st
import pandas as pd
import numpy as np
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

st.set_page_config(
    page_title="AWS Cost Optimizer",
    page_icon="☁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional Clean CSS - Balanced & Refined
st.markdown("""
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

/* ===== HEADERS ===== */
.main-title {
    font-size: 2.8rem;
    font-weight: 800;
    background: linear-gradient(135deg, #FF9900 0%, #FFB84D 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: -1px;
    margin-bottom: 0.25rem;
}

.sub-title {
    font-size: 1.15rem;
    font-weight: 500;
    color: #64748b;
    margin-bottom: 1.5rem;
}

.section-title {
    font-size: 1.5rem;
    font-weight: 700;
    color: #f1f5f9;
    margin: 2rem 0 1rem 0;
    padding-bottom: 0.5rem;
    border-bottom: 3px solid #FF9900;
    display: inline-block;
}

.chart-title {
    font-size: 1.2rem;
    font-weight: 700;
    color: #e2e8f0;
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid rgba(255, 153, 0, 0.3);
}

/* ===== METRIC CARDS ===== */
.metrics-row {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 1.25rem;
    margin: 1.5rem 0 2rem 0;
}

.metric-card {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px;
    padding: 1.5rem 1.25rem;
    text-align: center;
    transition: all 0.25s ease;
}

.metric-card:hover {
    background: rgba(255, 255, 255, 0.05);
    border-color: rgba(255, 153, 0, 0.3);
    transform: translateY(-4px);
}

.metric-icon {
    font-size: 1.8rem;
    margin-bottom: 0.5rem;
    display: block;
}

.metric-value {
    font-size: 2.2rem;
    font-weight: 800;
    color: #ffffff;
    line-height: 1.1;
    margin: 0.5rem 0;
}

.metric-value.green {
    color: #10b981;
}

.metric-value.orange {
    color: #FF9900;
}

.metric-value.red {
    color: #ef4444;
}

.metric-label {
    font-size: 0.85rem;
    font-weight: 600;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.metric-delta {
    font-size: 0.9rem;
    font-weight: 700;
    margin-top: 0.5rem;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    display: inline-block;
}

.metric-delta.positive {
    background: rgba(16, 185, 129, 0.15);
    color: #10b981;
}

/* ===== SAVINGS BOX ===== */
.savings-box {
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(16, 185, 129, 0.05) 100%);
    border: 2px solid rgba(16, 185, 129, 0.4);
    border-radius: 16px;
    padding: 1.75rem 2rem;
    margin: 1.5rem 0;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.savings-left {
    display: flex;
    align-items: center;
    gap: 1rem;
}

.savings-icon {
    font-size: 2.5rem;
}

.savings-label {
    font-size: 1rem;
    font-weight: 600;
    color: #10b981;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.savings-amount {
    font-size: 2.8rem;
    font-weight: 800;
    color: #10b981;
}

.savings-right {
    text-align: right;
}

.savings-annual {
    font-size: 1.1rem;
    font-weight: 600;
    color: #94a3b8;
}

.savings-annual span {
    color: #10b981;
    font-weight: 700;
}

.savings-pct {
    font-size: 1.5rem;
    font-weight: 800;
    color: #10b981;
    margin-top: 0.25rem;
}

/* ===== DATA BANNER ===== */
.data-banner {
    padding: 0.6rem 1.25rem;
    border-radius: 8px;
    margin-bottom: 1.25rem;
    font-size: 0.95rem;
    font-weight: 600;
    text-align: center;
}

.data-banner.sample {
    background: rgba(245, 158, 11, 0.15);
    border: 1px solid rgba(245, 158, 11, 0.4);
    color: #f59e0b;
}

.data-banner.live {
    background: rgba(16, 185, 129, 0.15);
    border: 1px solid rgba(16, 185, 129, 0.4);
    color: #10b981;
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
    padding: 0.9rem 1.75rem;
    font-size: 1.05rem;
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

/* ===== SERVICE CARDS ===== */
.service-card {
    border-radius: 16px;
    padding: 1.75rem;
    height: 200px;
    position: relative;
    transition: all 0.3s ease;
    color: white;
}

.service-card:hover {
    transform: translateY(-6px);
    box-shadow: 0 15px 40px rgba(0, 0, 0, 0.3);
}

.service-card h3 {
    font-size: 1.35rem;
    font-weight: 700;
    margin: 0 0 0.75rem 0;
}

.service-card p {
    font-size: 0.95rem;
    line-height: 1.6;
    opacity: 0.9;
}

.service-card .badge {
    position: absolute;
    bottom: 1.5rem;
    left: 1.75rem;
    background: rgba(255, 255, 255, 0.2);
    padding: 0.4rem 1rem;
    border-radius: 20px;
    font-size: 0.9rem;
    font-weight: 700;
}

/* ===== SIDEBAR HEADERS ===== */
.sidebar-header {
    font-size: 1.15rem !important;
    font-weight: 700 !important;
    color: #FF9900 !important;
    margin: 1.5rem 0 0.75rem 0 !important;
    padding-bottom: 0.5rem !important;
    border-bottom: 2px solid #FF9900 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
}

.sidebar-subheader {
    font-size: 0.9rem !important;
    font-weight: 600 !important;
    color: #64748b !important;
    margin-top: 1rem !important;
    text-transform: uppercase !important;
    letter-spacing: 1px !important;
}

/* ===== TABLES ===== */
.stDataFrame {
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    overflow: hidden;
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
</style>
""", unsafe_allow_html=True)


def init_session_state():
    if "thresholds" not in st.session_state:
        st.session_state["thresholds"] = {"cpu_oversized": 40, "cpu_undersized": 70, "mem_oversized": 50, "mem_undersized": 75}
    if "selected_service" not in st.session_state:
        st.session_state["selected_service"] = "EC2"
    if "data_source" not in st.session_state:
        st.session_state["data_source"] = "none"


def render_metric(icon, value, label, color="", delta=None):
    delta_html = f'<div class="metric-delta positive">{delta}</div>' if delta else ""
    return f"""
    <div class="metric-card">
        <span class="metric-icon">{icon}</span>
        <div class="metric-value {color}">{value}</div>
        <div class="metric-label">{label}</div>
        {delta_html}
    </div>
    """


def render_savings_box(monthly, annual, pct):
    return f"""
    <div class="savings-box">
        <div class="savings-left">
            <span class="savings-icon">💰</span>
            <div>
                <div class="savings-label">Potential Savings</div>
                <div class="savings-amount">${monthly:,.0f}/mo</div>
            </div>
        </div>
        <div class="savings-right">
            <div class="savings-annual">Annual: <span>${annual:,.0f}</span></div>
            <div class="savings-pct">↓ {pct:.1f}%</div>
        </div>
    </div>
    """


def render_data_banner():
    source = st.session_state.get("data_source", "none")
    if source == "sample":
        st.markdown('<div class="data-banner sample">⚠️ Sample Data - For demonstration only</div>', unsafe_allow_html=True)
    elif source == "live":
        st.markdown('<div class="data-banner live">🔗 Live AWS Connection</div>', unsafe_allow_html=True)


def render_sidebar():
    with st.sidebar:
        st.markdown("""
            <div style="text-align: center; padding: 1.5rem 0;">
                <div style="font-size: 3rem; margin-bottom: 0.25rem;">☁️</div>
                <h1 style="color: #FF9900; margin: 0; font-weight: 800; font-size: 1.4rem;">AWS Cost Optimizer</h1>
                <p style="color: #64748b; font-size: 0.9rem; margin-top: 0.25rem;">Enterprise Edition</p>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        st.markdown('<p class="sidebar-header">Services</p>', unsafe_allow_html=True)
        services = ["💻 EC2 Instances", "🗄️ RDS Databases", "💾 EBS Volumes", "⚡ ElastiCache", "λ Lambda", "🪣 S3"]
        service = st.radio("Service:", services, index=0, label_visibility="collapsed")
        st.session_state["selected_service"] = service.split()[1] if len(service.split()) > 1 else "EC2"

        st.markdown("---")

        st.markdown('<p class="sidebar-header">Data Source</p>', unsafe_allow_html=True)
        source = st.radio("Source:", ["📤 Upload Report", "🔗 Live AWS"], label_visibility="collapsed")

        if "Upload" in source:
            uploaded = st.file_uploader("Upload", type=["xlsx"], label_visibility="collapsed")
            if uploaded:
                st.session_state["report_file"] = uploaded
                st.session_state["data_source"] = "uploaded"
                st.success("✅ Loaded!")
        else:
            region = st.selectbox("Region", ["us-east-1", "us-east-2", "us-west-1", "us-west-2"], label_visibility="collapsed")
            st.session_state["aws_region"] = region
            if st.button("🚀 Run Analysis", type="primary", use_container_width=True):
                st.session_state["run_analysis"] = True

        st.markdown('<p class="sidebar-subheader">Quick Demo</p>', unsafe_allow_html=True)
        if st.button("📊 Load Sample Data", use_container_width=True):
            st.session_state["sample_df"] = generate_sample_dataframe()
            st.session_state["data_source"] = "sample"
            st.rerun()

        st.markdown("---")

        st.markdown('<p class="sidebar-header">Settings</p>', unsafe_allow_html=True)
        with st.expander("Thresholds"):
            cpu_o = st.slider("CPU Oversized %", 10, 60, st.session_state["thresholds"]["cpu_oversized"])
            cpu_u = st.slider("CPU Undersized %", 50, 95, st.session_state["thresholds"]["cpu_undersized"])
            if st.button("Apply"):
                st.session_state["thresholds"]["cpu_oversized"] = cpu_o
                st.session_state["thresholds"]["cpu_undersized"] = cpu_u
                st.rerun()

        st.markdown("""
            <div style="text-align: center; padding: 1.5rem 0; margin-top: 1rem; border-top: 1px solid rgba(255,255,255,0.1);">
                <p style="color: #FF9900; font-weight: 700; font-size: 0.95rem;">Version 2.0</p>
            </div>
        """, unsafe_allow_html=True)


def generate_sample_dataframe():
    import random
    instance_types = ["t3.micro", "t3.small", "t3.medium", "t3.large", "m5.large", "m5.xlarge", "m5.2xlarge", "r5.large"]
    data = []
    for i in range(25):
        classification = random.choice(["oversized", "right_sized", "undersized"])
        if classification == "oversized":
            cpu, mem, savings = random.uniform(10, 35), random.uniform(15, 45), random.uniform(100, 600)
        elif classification == "undersized":
            cpu, mem, savings = random.uniform(75, 95), random.uniform(80, 95), 0
        else:
            cpu, mem, savings = random.uniform(40, 65), random.uniform(50, 70), 0

        current = random.uniform(200, 1200)
        inst_type = random.choice(instance_types)
        data.append({
            "server_id": f"i-{i:08x}",
            "hostname": f"server-{i:02d}",
            "instance_type": inst_type,
            "Environment": random.choice(["Production", "Staging", "Dev"]),
            "cpu_p95": cpu,
            "memory_p95": mem,
            "classification": classification,
            "recommended_type": instance_types[max(0, instance_types.index(inst_type) - 1)] if classification == "oversized" else None,
            "current_monthly": current,
            "monthly_savings": savings,
            "confidence": random.uniform(0.7, 0.98),
            "risk_level": random.choice(["Low", "Medium", "High"]),
            "has_contention": classification == "undersized" and random.random() > 0.6,
            "contention_events": random.randint(5, 40) if classification == "undersized" else 0,
        })
    return pd.DataFrame(data)


def main():
    init_session_state()
    render_sidebar()

    st.markdown('<div class="main-title">AWS Cost Optimizer</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-title">Analyzing {st.session_state.get("selected_service", "EC2")} Resources</div>', unsafe_allow_html=True)

    render_data_banner()

    if st.session_state.get("run_analysis"):
        st.info("Connecting to AWS...")
        st.session_state["run_analysis"] = False

    if "report_file" in st.session_state or "sample_df" in st.session_state or "live_df" in st.session_state:
        display_dashboard()
    else:
        display_welcome()


def display_welcome():
    st.markdown('<div class="section-title">Supported Services</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    services = [
        (col1, "#FF9900", "💻", "EC2 Instances", "Rightsize compute and identify Graviton opportunities.", "40%"),
        (col1, "#3B48CC", "🗄️", "RDS Databases", "Optimize databases and Reserved Instances.", "50%"),
        (col2, "#10b981", "💾", "EBS Volumes", "Find unattached volumes, optimize IOPS.", "30%"),
        (col2, "#8b5cf6", "⚡", "ElastiCache", "Analyze cache hit rates and node types.", "35%"),
        (col3, "#ef4444", "λ", "Lambda", "Optimize memory and execution costs.", "25%"),
        (col3, "#475569", "🪣", "S3 Buckets", "Lifecycle policies and storage classes.", "70%"),
    ]

    for col, color, icon, title, desc, savings in services:
        with col:
            st.markdown(f"""
            <div class="service-card" style="background: {color}; margin-bottom: 1rem;">
                <h3>{icon} {title}</h3>
                <p>{desc}</p>
                <div class="badge">Up to {savings} savings</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    col1, col2 = st.columns([1.2, 1])
    with col1:
        st.markdown('<div class="section-title">Getting Started</div>', unsafe_allow_html=True)
        st.markdown("""
        <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); border-radius: 14px; padding: 1.75rem;">
            <ol style="font-size: 1.1rem; line-height: 2.2; color: #cbd5e1; margin: 0; padding-left: 1.25rem;">
                <li><strong style="color: #FF9900;">Select a Service</strong> from the sidebar</li>
                <li><strong style="color: #FF9900;">Upload a Report</strong> or connect to AWS</li>
                <li><strong style="color: #FF9900;">Review Recommendations</strong></li>
                <li><strong style="color: #FF9900;">Export Commands</strong></li>
            </ol>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="section-title">Quick Demo</div>', unsafe_allow_html=True)
        st.markdown("""
        <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); border-radius: 14px; padding: 1.75rem; text-align: center;">
            <p style="font-size: 1.05rem; color: #94a3b8; margin-bottom: 1.5rem;">Load sample data to explore the dashboard.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("📊 Load Sample Data", type="primary", use_container_width=True, key="welcome_load"):
            st.session_state["sample_df"] = generate_sample_dataframe()
            st.session_state["data_source"] = "sample"
            st.rerun()


def display_dashboard():
    df = st.session_state.get("sample_df")
    if df is None:
        df = st.session_state.get("live_df")
    if df is None and "report_file" in st.session_state:
        try:
            df = pd.read_excel(st.session_state["report_file"], sheet_name="Server Details")
        except:
            st.error("Failed to read report")
            return

    if df is None or len(df) == 0:
        st.warning("No data available")
        return

    # Metrics
    total = len(df)
    spend = df["current_monthly"].sum() if "current_monthly" in df.columns else 0
    savings = df[df["monthly_savings"] > 0]["monthly_savings"].sum() if "monthly_savings" in df.columns else 0
    pct = (savings / spend * 100) if spend > 0 else 0
    oversized = len(df[df["classification"] == "oversized"]) if "classification" in df.columns else 0
    undersized = len(df[df["classification"] == "undersized"]) if "classification" in df.columns else 0

    st.markdown('<div class="section-title">Executive Summary</div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="metrics-row">
        {render_metric("📦", total, "Resources")}
        {render_metric("💰", f"${spend:,.0f}", "Monthly Spend", "orange")}
        {render_metric("💵", f"${savings:,.0f}", "Savings", "green", f"↓{pct:.0f}%")}
        {render_metric("📉", oversized, "Oversized", "green")}
        {render_metric("📈", undersized, "Undersized", "red")}
    </div>
    """, unsafe_allow_html=True)

    if savings > 0:
        st.markdown(render_savings_box(savings, savings * 12, pct), unsafe_allow_html=True)

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Analysis", "💡 Recommendations", "💰 Costs", "⚠️ Issues"])

    with tab1:
        display_analysis(df)
    with tab2:
        display_recommendations(df)
    with tab3:
        display_costs(df)
    with tab4:
        display_issues(df)


def display_analysis(df):
    import plotly.express as px
    import plotly.graph_objects as go

    col1, col2 = st.columns([1, 1.5])

    with col1:
        st.markdown('<div class="chart-title">Classification</div>', unsafe_allow_html=True)
        if "classification" in df.columns:
            counts = df["classification"].value_counts()
            colors = {'oversized': '#10b981', 'right_sized': '#64748b', 'undersized': '#ef4444'}
            fig = go.Figure(data=[go.Pie(
                labels=[x.replace("_", " ").title() for x in counts.index],
                values=counts.values,
                hole=0.65,
                marker_colors=[colors.get(x, '#64748b') for x in counts.index],
                textinfo='label+percent',
                textfont_size=12
            )])
            fig.update_layout(
                height=320,
                showlegend=False,
                annotations=[dict(text=f'{len(df)}', x=0.5, y=0.5, font_size=28, font_weight='bold', font_color='white', showarrow=False)],
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(t=10, b=10, l=10, r=10)
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown('<div class="chart-title">Utilization Map</div>', unsafe_allow_html=True)
        if "cpu_p95" in df.columns and "memory_p95" in df.columns:
            fig = px.scatter(df, x="cpu_p95", y="memory_p95", color="classification",
                           size="current_monthly" if "current_monthly" in df.columns else None,
                           hover_data=["hostname", "instance_type"],
                           color_discrete_map={'oversized': '#10b981', 'right_sized': '#64748b', 'undersized': '#ef4444'})
            fig.update_layout(
                height=320,
                xaxis_title="CPU P95 %", yaxis_title="Memory P95 %",
                xaxis=dict(range=[0, 100], gridcolor='rgba(255,255,255,0.05)'),
                yaxis=dict(range=[0, 100], gridcolor='rgba(255,255,255,0.05)'),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#94a3b8', size=11),
                legend=dict(font=dict(size=11))
            )
            st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="chart-title">Resource Details</div>', unsafe_allow_html=True)
    cols = ["hostname", "instance_type", "cpu_p95", "memory_p95", "classification", "monthly_savings"]
    available = [c for c in cols if c in df.columns]
    st.dataframe(
        df[available].sort_values("monthly_savings", ascending=False) if "monthly_savings" in df.columns else df[available],
        use_container_width=True, height=350,
        column_config={
            "monthly_savings": st.column_config.NumberColumn("Savings", format="$%.0f"),
            "cpu_p95": st.column_config.NumberColumn("CPU %", format="%.1f"),
            "memory_p95": st.column_config.NumberColumn("Mem %", format="%.1f"),
        }
    )


def display_recommendations(df):
    if "recommended_type" not in df.columns:
        st.info("No recommendations available")
        return

    recs = df[df["recommended_type"].notna()]
    if len(recs) == 0:
        st.success("🎉 All resources are optimally sized!")
        return

    savings = recs["monthly_savings"].sum() if "monthly_savings" in recs.columns else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Recommendations", len(recs))
    col2.metric("Monthly Savings", f"${savings:,.0f}")
    col3.metric("Annual Savings", f"${savings*12:,.0f}")

    st.markdown("<br>", unsafe_allow_html=True)

    cols = ["hostname", "instance_type", "recommended_type", "monthly_savings", "confidence", "risk_level"]
    available = [c for c in cols if c in recs.columns]
    st.dataframe(recs[available].sort_values("monthly_savings", ascending=False), use_container_width=True, height=350,
                column_config={"monthly_savings": st.column_config.NumberColumn("Savings", format="$%.0f"),
                              "confidence": st.column_config.ProgressColumn("Confidence", min_value=0, max_value=1)})


def display_costs(df):
    import plotly.graph_objects as go

    if "current_monthly" not in df.columns:
        st.info("No cost data")
        return

    current = df["current_monthly"].sum()
    savings = df["monthly_savings"].sum() if "monthly_savings" in df.columns else 0
    optimized = current - savings

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="chart-title">Current vs Optimized</div>', unsafe_allow_html=True)
        fig = go.Figure(data=[
            go.Bar(name='Current', x=['Cost'], y=[current], marker_color='#ef4444', text=[f'${current:,.0f}'], textposition='auto'),
            go.Bar(name='Optimized', x=['Cost'], y=[optimized], marker_color='#10b981', text=[f'${optimized:,.0f}'], textposition='auto')
        ])
        fig.update_layout(height=300, barmode='group', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#94a3b8'))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown('<div class="chart-title">12-Month Projection</div>', unsafe_allow_html=True)
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        cumulative = [savings * (i+1) for i in range(12)]
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=months, y=cumulative, mode='lines+markers', fill='tozeroy',
                                fillcolor='rgba(16, 185, 129, 0.15)', line=dict(color='#10b981', width=3)))
        fig.update_layout(height=300, yaxis_tickformat="$,.0f", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#94a3b8'))
        st.plotly_chart(fig, use_container_width=True)


def display_issues(df):
    if "has_contention" not in df.columns:
        st.info("No contention data")
        return

    issues = df[df["has_contention"] == True]
    if len(issues) == 0:
        st.success("✅ No contention detected!")
        return

    st.warning(f"⚠️ {len(issues)} resources with performance issues")
    cols = ["hostname", "instance_type", "contention_events", "cpu_p95", "memory_p95"]
    available = [c for c in cols if c in issues.columns]
    st.dataframe(issues[available].sort_values("contention_events", ascending=False) if "contention_events" in issues.columns else issues[available], use_container_width=True)


if __name__ == "__main__":
    main()

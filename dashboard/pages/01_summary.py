"""Summary page for the dashboard."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from styles import inject_styles, page_header, section_header, chart_header, metrics_row

st.set_page_config(page_title="Summary", page_icon="📊", layout="wide")
inject_styles()

page_header("📊 Executive Summary", "Overview of your AWS resource optimization")


def load_data():
    """Load data from session state."""
    if "sample_df" in st.session_state:
        return st.session_state["sample_df"]
    if "report_file" in st.session_state:
        try:
            return pd.read_excel(st.session_state["report_file"], sheet_name="Server Details")
        except:
            return None
    return None


df = load_data()

if df is None:
    st.markdown("""
    <div class="info-box warning">
        <strong>No data loaded.</strong> Please go to the Home page and load sample data or upload a report.
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# Calculate metrics
total_servers = len(df)
total_spend = df["current_monthly"].sum() if "current_monthly" in df.columns else 0
total_savings = df[df["monthly_savings"] > 0]["monthly_savings"].sum() if "monthly_savings" in df.columns else 0
savings_pct = (total_savings / total_spend * 100) if total_spend > 0 else 0
oversized = len(df[df["classification"] == "oversized"]) if "classification" in df.columns else 0
undersized = len(df[df["classification"] == "undersized"]) if "classification" in df.columns else 0

# Key Metrics
section_header("Key Metrics")

st.markdown(metrics_row([
    ("📦", total_servers, "Total Resources"),
    ("💰", f"${total_spend:,.0f}", "Monthly Spend", "orange"),
    ("💵", f"${total_savings:,.0f}", "Potential Savings", "green"),
    ("📉", oversized, "Oversized", "green"),
    ("📈", undersized, "Undersized", "red"),
]), unsafe_allow_html=True)

st.divider()

# Classification breakdown
section_header("Resource Classification")

col1, col2 = st.columns([1, 1.5])

with col1:
    if "classification" in df.columns:
        class_counts = df["classification"].value_counts()
        colors = {'oversized': '#10b981', 'right_sized': '#64748b', 'undersized': '#ef4444'}

        fig = go.Figure(data=[go.Pie(
            labels=[x.replace("_", " ").title() for x in class_counts.index],
            values=class_counts.values,
            hole=0.6,
            marker_colors=[colors.get(x, '#64748b') for x in class_counts.index],
            textinfo='label+percent',
            textfont_size=12
        )])

        fig.update_layout(
            height=320,
            showlegend=False,
            annotations=[dict(text=f'{len(df)}', x=0.5, y=0.5, font_size=28, font_weight='bold', font_color='white', showarrow=False)],
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=20, b=20, l=20, r=20)
        )
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("""
    | Classification | Description | Action |
    |----------------|-------------|--------|
    | **Oversized** | Resources underutilized | Downsize for savings |
    | **Right-sized** | Properly matched | No change needed |
    | **Undersized** | Resource constrained | Consider upgrade |
    """)

    if oversized > 0:
        st.markdown(f"""
        <div class="info-box success">
            <strong>✅ {oversized} resources</strong> can be downsized for <strong>${total_savings:,.0f}/month</strong> in savings
        </div>
        """, unsafe_allow_html=True)

    if undersized > 0:
        st.markdown(f"""
        <div class="info-box warning">
            <strong>⚠️ {undersized} resources</strong> may need upgrades to improve performance
        </div>
        """, unsafe_allow_html=True)

st.divider()

# Savings by Environment
section_header("Savings by Environment")

if "monthly_savings" in df.columns and "Environment" in df.columns:
    by_env = df.groupby("Environment").agg({
        "current_monthly": "sum",
        "monthly_savings": "sum"
    }).sort_values("monthly_savings", ascending=False)

    fig = px.bar(
        by_env.reset_index(),
        x="Environment",
        y="monthly_savings",
        color="monthly_savings",
        color_continuous_scale=[[0, '#064e3b'], [1, '#10b981']],
        text="monthly_savings"
    )

    fig.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
    fig.update_layout(
        height=350,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#94a3b8'),
        xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
        yaxis=dict(gridcolor='rgba(255,255,255,0.05)', title="Monthly Savings ($)"),
        coloraxis_showscale=False
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Environment data not available.")

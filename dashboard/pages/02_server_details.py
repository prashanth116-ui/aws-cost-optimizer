"""Server details page for the dashboard."""

import streamlit as st
import pandas as pd
import plotly.express as px
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from styles import inject_styles, page_header, section_header, chart_header, metrics_row

st.set_page_config(page_title="Server Details", page_icon="🖥️", layout="wide")
inject_styles()

page_header("🖥️ Server Details", "Explore individual resource metrics and configurations")


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

# Filters
st.sidebar.markdown("### Filters")

# Classification filter
if "classification" in df.columns:
    selected_class = st.sidebar.multiselect(
        "Classification",
        options=df["classification"].unique(),
        default=list(df["classification"].unique())
    )
    df = df[df["classification"].isin(selected_class)]

# Instance type filter
if "instance_type" in df.columns:
    instance_types = st.sidebar.multiselect(
        "Instance Type",
        options=sorted(df["instance_type"].unique()),
        default=[]
    )
    if instance_types:
        df = df[df["instance_type"].isin(instance_types)]

# GSI filter
tag_columns = [c for c in df.columns if c.upper() in ["GSI", "COST_CENTER", "PROJECT", "ENVIRONMENT"]]
if tag_columns:
    tag_col = tag_columns[0]
    gsi_values = st.sidebar.multiselect(
        tag_col.replace("_", " ").title(),
        options=sorted(df[tag_col].dropna().unique()),
        default=[]
    )
    if gsi_values:
        df = df[df[tag_col].isin(gsi_values)]

# Summary metrics
section_header("Server Summary")

total = len(df)
oversized = len(df[df["classification"] == "oversized"]) if "classification" in df.columns else 0
right_sized = len(df[df["classification"] == "right_sized"]) if "classification" in df.columns else 0
undersized = len(df[df["classification"] == "undersized"]) if "classification" in df.columns else 0

st.markdown(metrics_row([
    ("📦", total, "Total Servers"),
    ("📉", oversized, "Oversized", "green"),
    ("✅", right_sized, "Right Sized"),
    ("📈", undersized, "Undersized", "red"),
]), unsafe_allow_html=True)

st.divider()

# Server table
section_header("All Servers")

# Select columns to display
default_cols = ["hostname", "instance_type", "vcpu", "memory_gb",
                "cpu_p95", "memory_p95", "classification", "monthly_savings"]
available_defaults = [c for c in default_cols if c in df.columns]

display_cols = st.multiselect(
    "Columns to display:",
    options=df.columns.tolist(),
    default=available_defaults
)

if display_cols:
    st.dataframe(
        df[display_cols],
        use_container_width=True,
        height=400,
        column_config={
            "monthly_savings": st.column_config.NumberColumn(
                "Monthly Savings",
                format="$%.2f"
            ),
            "current_monthly": st.column_config.NumberColumn(
                "Current Monthly",
                format="$%.2f"
            ),
            "cpu_p95": st.column_config.NumberColumn(
                "CPU P95 %",
                format="%.1f"
            ),
            "memory_p95": st.column_config.NumberColumn(
                "Memory P95 %",
                format="%.1f"
            ),
            "confidence": st.column_config.ProgressColumn(
                "Confidence",
                format="%.0f%%",
                min_value=0,
                max_value=1
            )
        }
    )

st.divider()

# Individual server detail
section_header("Server Deep Dive")

server_col = "hostname" if "hostname" in df.columns else "server_id" if "server_id" in df.columns else None

if server_col:
    server_options = df[server_col].tolist()
    selected_server = st.selectbox("Select a server:", server_options)

    if selected_server:
        server_data = df[df[server_col] == selected_server].iloc[0]

        col1, col2, col3 = st.columns(3)

        with col1:
            chart_header("Instance Info")
            st.markdown(f"**Hostname:** {server_data.get('hostname', 'N/A')}")
            st.markdown(f"**Instance ID:** {server_data.get('instance_id', 'N/A')}")
            st.markdown(f"**Instance Type:** {server_data.get('instance_type', 'N/A')}")
            st.markdown(f"**vCPU:** {server_data.get('vcpu', 'N/A')}")
            st.markdown(f"**Memory:** {server_data.get('memory_gb', 'N/A')} GB")

        with col2:
            chart_header("Utilization")
            if "cpu_avg" in server_data:
                st.metric("CPU Average", f"{server_data['cpu_avg']:.1f}%")
            if "cpu_p95" in server_data:
                st.metric("CPU P95", f"{server_data['cpu_p95']:.1f}%")
            if "memory_p95" in server_data:
                st.metric("Memory P95", f"{server_data['memory_p95']:.1f}%")

        with col3:
            chart_header("Recommendation")
            classification = server_data.get("classification", "unknown")

            if classification == "oversized":
                st.markdown(f"""
                <div class="info-box success">
                    <strong>Classification:</strong> {classification.upper()}
                </div>
                """, unsafe_allow_html=True)
            elif classification == "undersized":
                st.markdown(f"""
                <div class="info-box error">
                    <strong>Classification:</strong> {classification.upper()}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="info-box">
                    <strong>Classification:</strong> {classification.upper()}
                </div>
                """, unsafe_allow_html=True)

            if pd.notna(server_data.get("recommended_type")):
                st.markdown(f"**Recommended Type:** {server_data['recommended_type']}")
                st.markdown(f"**Monthly Savings:** ${server_data.get('monthly_savings', 0):,.2f}")
                st.markdown(f"**Confidence:** {server_data.get('confidence', 0)*100:.0f}%")
                st.markdown(f"**Risk Level:** {server_data.get('risk_level', 'N/A')}")
else:
    st.info("No server identifier column found in data.")

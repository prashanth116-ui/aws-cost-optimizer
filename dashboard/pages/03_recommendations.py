"""Recommendations page for the dashboard."""

import streamlit as st
import pandas as pd
import plotly.express as px
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from styles import inject_styles, page_header, section_header, metrics_row

st.set_page_config(page_title="Recommendations", page_icon="💡", layout="wide")
inject_styles()

page_header("💡 Rightsizing Recommendations", "Optimize your AWS resources for cost and performance")


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

# Filter to servers with recommendations
if "recommended_type" not in df.columns:
    st.markdown("""
    <div class="info-box warning">
        <strong>No recommendation data</strong> available in this report.
    </div>
    """, unsafe_allow_html=True)
    st.stop()

recs_df = df[df["recommended_type"].notna()].copy()

if len(recs_df) == 0:
    st.markdown("""
    <div class="info-box success">
        <strong>All servers are appropriately sized!</strong> No recommendations needed.
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# Sidebar filters
st.sidebar.markdown("### Filters")

# Risk level filter
if "risk_level" in recs_df.columns:
    risk_levels = st.sidebar.multiselect(
        "Risk Level",
        options=recs_df["risk_level"].unique(),
        default=["low", "medium"] if set(["low", "medium"]).issubset(recs_df["risk_level"].unique()) else list(recs_df["risk_level"].unique())
    )
    recs_df = recs_df[recs_df["risk_level"].isin(risk_levels)]

# Minimum savings filter
if "monthly_savings" in recs_df.columns:
    min_savings = st.sidebar.slider(
        "Minimum Monthly Savings ($)",
        min_value=0,
        max_value=int(recs_df["monthly_savings"].max()),
        value=0
    )
    recs_df = recs_df[recs_df["monthly_savings"] >= min_savings]

# Minimum confidence filter
if "confidence" in recs_df.columns:
    min_confidence = st.sidebar.slider(
        "Minimum Confidence",
        min_value=0.0,
        max_value=1.0,
        value=0.5
    )
    recs_df = recs_df[recs_df["confidence"] >= min_confidence]

# Summary metrics
section_header("Recommendation Summary")

total_savings = recs_df[recs_df["monthly_savings"] > 0]["monthly_savings"].sum() if "monthly_savings" in recs_df.columns else 0
yearly_savings = total_savings * 12
low_risk = len(recs_df[recs_df["risk_level"] == "low"]) if "risk_level" in recs_df.columns else 0

st.markdown(metrics_row([
    ("📋", len(recs_df), "With Recommendations"),
    ("💵", f"${total_savings:,.0f}", "Monthly Savings", "green"),
    ("📅", f"${yearly_savings:,.0f}", "Yearly Savings", "green"),
    ("✅", low_risk, "Low Risk", "green"),
]), unsafe_allow_html=True)

st.divider()

# Implementation phases
section_header("Implementation Phases")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown('<div class="chart-title">Quick Wins</div>', unsafe_allow_html=True)
    st.caption("Low risk, high confidence")

    quick_wins = recs_df[
        (recs_df["risk_level"] == "low") &
        (recs_df["confidence"] >= 0.7) &
        (recs_df["monthly_savings"] > 0)
    ] if "risk_level" in recs_df.columns and "confidence" in recs_df.columns else pd.DataFrame()

    if len(quick_wins) > 0:
        qw_savings = quick_wins["monthly_savings"].sum()
        st.markdown(f"""
        <div class="info-box success">
            <strong>{len(quick_wins)}</strong> servers | <strong>${qw_savings:,.0f}</strong>/month
        </div>
        """, unsafe_allow_html=True)

        st.dataframe(
            quick_wins[["hostname", "instance_type", "recommended_type", "monthly_savings"]].head(10),
            use_container_width=True,
            hide_index=True,
            column_config={
                "monthly_savings": st.column_config.NumberColumn("Savings", format="$%.0f")
            }
        )
    else:
        st.info("No quick wins identified")

with col2:
    st.markdown('<div class="chart-title">Medium Term</div>', unsafe_allow_html=True)
    st.caption("Moderate risk or confidence")

    medium_term = recs_df[
        ((recs_df["risk_level"] == "medium") |
         ((recs_df["confidence"] >= 0.5) & (recs_df["confidence"] < 0.7))) &
        (recs_df["monthly_savings"] > 0)
    ] if "risk_level" in recs_df.columns and "confidence" in recs_df.columns else pd.DataFrame()

    if len(medium_term) > 0:
        mt_savings = medium_term["monthly_savings"].sum()
        st.markdown(f"""
        <div class="info-box warning">
            <strong>{len(medium_term)}</strong> servers | <strong>${mt_savings:,.0f}</strong>/month
        </div>
        """, unsafe_allow_html=True)

        st.dataframe(
            medium_term[["hostname", "instance_type", "recommended_type", "monthly_savings"]].head(10),
            use_container_width=True,
            hide_index=True,
            column_config={
                "monthly_savings": st.column_config.NumberColumn("Savings", format="$%.0f")
            }
        )
    else:
        st.info("No medium term changes identified")

with col3:
    st.markdown('<div class="chart-title">Long Term</div>', unsafe_allow_html=True)
    st.caption("Higher risk, requires validation")

    long_term = recs_df[
        (recs_df["risk_level"] == "high") |
        (recs_df["confidence"] < 0.5)
    ] if "risk_level" in recs_df.columns and "confidence" in recs_df.columns else pd.DataFrame()

    if len(long_term) > 0:
        lt_savings = long_term[long_term["monthly_savings"] > 0]["monthly_savings"].sum()
        st.markdown(f"""
        <div class="info-box error">
            <strong>{len(long_term)}</strong> servers | <strong>${lt_savings:,.0f}</strong>/month
        </div>
        """, unsafe_allow_html=True)

        st.dataframe(
            long_term[["hostname", "instance_type", "recommended_type", "monthly_savings"]].head(10),
            use_container_width=True,
            hide_index=True,
            column_config={
                "monthly_savings": st.column_config.NumberColumn("Savings", format="$%.0f")
            }
        )
    else:
        st.info("No long term changes identified")

st.divider()

# Full recommendations table
section_header("All Recommendations")

col1, col2 = st.columns([3, 1])
with col1:
    sort_by = st.selectbox(
        "Sort by:",
        options=["monthly_savings", "confidence", "hostname"],
        index=0
    )
with col2:
    sort_ascending = st.checkbox("Ascending", value=False)

recs_sorted = recs_df.sort_values(sort_by, ascending=sort_ascending)

display_cols = ["hostname", "instance_type", "recommended_type", "classification", "monthly_savings"]
if "yearly_savings" in recs_sorted.columns:
    display_cols.append("yearly_savings")
if "confidence" in recs_sorted.columns:
    display_cols.append("confidence")
if "risk_level" in recs_sorted.columns:
    display_cols.append("risk_level")
if "reason" in recs_sorted.columns:
    display_cols.append("reason")

st.dataframe(
    recs_sorted[display_cols],
    use_container_width=True,
    height=400,
    column_config={
        "monthly_savings": st.column_config.NumberColumn("Monthly Savings", format="$%.2f"),
        "yearly_savings": st.column_config.NumberColumn("Yearly Savings", format="$%.2f"),
        "confidence": st.column_config.ProgressColumn("Confidence", format="%.0f%%", min_value=0, max_value=1)
    }
)

# Download button
csv = recs_sorted.to_csv(index=False)
st.download_button(
    label="📥 Download Recommendations CSV",
    data=csv,
    file_name="rightsizing_recommendations.csv",
    mime="text/csv"
)

"""Drill-Down Analysis page - explore by GSI, Environment, Team."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from styles import inject_styles, page_header, section_header, chart_header, metrics_row

st.set_page_config(page_title="Drill-Down Analysis", page_icon="🔍", layout="wide")
inject_styles()

page_header("🔍 Drill-Down Analysis", "Explore cost optimization opportunities by GSI, Environment, Team, and more")


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

# Determine available grouping columns
grouping_options = []
potential_groups = ["Environment", "GSI", "Team", "classification", "instance_type", "risk_level"]

for col in potential_groups:
    if col in df.columns and df[col].notna().any():
        grouping_options.append(col)

if not grouping_options:
    st.markdown("""
    <div class="info-box warning">
        <strong>No grouping columns</strong> available in the data.
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# Sidebar for drill-down selection
st.sidebar.markdown("### Drill-Down Selection")

primary_group = st.sidebar.selectbox(
    "Primary Grouping",
    options=grouping_options,
    index=0
)

# Get available values for primary group
primary_values = df[primary_group].dropna().unique().tolist()

selected_primary = st.sidebar.selectbox(
    f"Select {primary_group}",
    options=["All"] + primary_values
)

# Secondary grouping (optional)
secondary_options = [g for g in grouping_options if g != primary_group]
if secondary_options:
    secondary_group = st.sidebar.selectbox(
        "Secondary Grouping (optional)",
        options=["None"] + secondary_options
    )
else:
    secondary_group = "None"

# Filter data
if selected_primary != "All":
    filtered_df = df[df[primary_group] == selected_primary]
else:
    filtered_df = df.copy()

# Main content
section_header(f"Analysis by {primary_group}")

if selected_primary != "All":
    st.markdown(f"**Showing:** {selected_primary}")

# Summary metrics for selection
total_servers = len(filtered_df)
total_spend = filtered_df["current_monthly"].sum() if "current_monthly" in filtered_df.columns else 0
total_savings = filtered_df[filtered_df["monthly_savings"] > 0]["monthly_savings"].sum() if "monthly_savings" in filtered_df.columns else 0
oversized = len(filtered_df[filtered_df["classification"] == "oversized"]) if "classification" in filtered_df.columns else 0

st.markdown(metrics_row([
    ("🖥️", total_servers, "Servers"),
    ("💵", f"${total_spend:,.0f}", "Monthly Spend", "orange"),
    ("💰", f"${total_savings:,.0f}", "Potential Savings", "green"),
    ("📉", oversized, "Oversized", "green"),
]), unsafe_allow_html=True)

st.divider()

# Breakdown charts
col1, col2 = st.columns(2)

with col1:
    chart_header(f"Cost by {primary_group}")

    if selected_primary == "All":
        by_group = df.groupby(primary_group).agg({
            "current_monthly": "sum",
            "monthly_savings": lambda x: x[x > 0].sum() if "monthly_savings" in df.columns else 0
        }).reset_index()

        fig = px.bar(
            by_group,
            x=primary_group,
            y="current_monthly",
            color="monthly_savings",
            color_continuous_scale=[[0, '#064e3b'], [1, '#10b981']],
            labels={"current_monthly": "Monthly Cost ($)", "monthly_savings": "Savings Potential"}
        )
        fig.update_layout(
            height=400,
            xaxis_tickangle=45,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#94a3b8'),
            xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
            yaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
            coloraxis_showscale=False
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        if secondary_group != "None":
            by_secondary = filtered_df.groupby(secondary_group).agg({
                "current_monthly": "sum"
            }).reset_index()

            fig = go.Figure(data=[go.Pie(
                labels=by_secondary[secondary_group],
                values=by_secondary["current_monthly"],
                hole=0.5,
                marker_colors=['#FF9900', '#10b981', '#3b82f6', '#f59e0b', '#8b5cf6'],
                textinfo='label+percent',
                textfont_size=11
            )])
            fig.update_layout(
                height=400,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#94a3b8'),
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            if "classification" in filtered_df.columns:
                by_class = filtered_df["classification"].value_counts()
                fig = go.Figure(data=[go.Pie(
                    labels=by_class.index,
                    values=by_class.values,
                    hole=0.5,
                    marker_colors=['#10b981' if x == 'oversized' else '#64748b' if x == 'right_sized' else '#ef4444' for x in by_class.index],
                    textinfo='label+percent',
                    textfont_size=11
                )])
                fig.update_layout(
                    height=400,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#94a3b8'),
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True)

with col2:
    chart_header("Savings Opportunity")

    if "monthly_savings" in filtered_df.columns:
        savings_df = filtered_df[filtered_df["monthly_savings"] > 0].nlargest(10, "monthly_savings")

        if len(savings_df) > 0:
            fig = px.bar(
                savings_df,
                x="hostname" if "hostname" in savings_df.columns else savings_df.index,
                y="monthly_savings",
                color="classification" if "classification" in savings_df.columns else None,
                color_discrete_map={
                    "oversized": "#10b981",
                    "undersized": "#ef4444",
                },
                text="monthly_savings"
            )
            fig.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
            fig.update_layout(
                height=400,
                xaxis_tickangle=45,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#94a3b8'),
                xaxis=dict(gridcolor='rgba(255,255,255,0.05)', title=""),
                yaxis=dict(gridcolor='rgba(255,255,255,0.05)', title="Monthly Savings ($)"),
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No savings opportunities in this selection.")
    else:
        st.info("Savings data not available.")

st.divider()

# Detailed server list
section_header("Server Details")

available_cols = filtered_df.columns.tolist()
default_cols = ["hostname", "instance_type", "classification", "cpu_p95", "memory_p95", "current_monthly", "monthly_savings"]
display_cols = [c for c in default_cols if c in available_cols]

selected_cols = st.multiselect(
    "Select columns to display:",
    options=available_cols,
    default=display_cols
)

if selected_cols:
    st.dataframe(
        filtered_df[selected_cols].sort_values("monthly_savings" if "monthly_savings" in selected_cols else selected_cols[0], ascending=False),
        use_container_width=True,
        height=400,
        column_config={
            "current_monthly": st.column_config.NumberColumn("Monthly Cost", format="$%.2f"),
            "monthly_savings": st.column_config.NumberColumn("Savings", format="$%.2f"),
            "cpu_p95": st.column_config.NumberColumn("CPU P95 %", format="%.1f"),
            "memory_p95": st.column_config.NumberColumn("Mem P95 %", format="%.1f"),
        }
    )

st.divider()

# Comparison view (if showing all)
if selected_primary == "All" and len(primary_values) > 1:
    section_header(f"Compare {primary_group}s")

    compare_values = st.multiselect(
        f"Select {primary_group}s to compare:",
        options=primary_values,
        default=primary_values[:min(5, len(primary_values))]
    )

    if len(compare_values) >= 2:
        compare_df = df[df[primary_group].isin(compare_values)]

        agg_dict = {
            "hostname": "count",
            "current_monthly": "sum",
        }
        if "monthly_savings" in df.columns:
            agg_dict["monthly_savings"] = lambda x: x[x > 0].sum()
        if "cpu_p95" in df.columns:
            agg_dict["cpu_p95"] = "mean"
        if "memory_p95" in df.columns:
            agg_dict["memory_p95"] = "mean"

        comparison_data = compare_df.groupby(primary_group).agg(agg_dict).rename(columns={"hostname": "server_count"})

        if "monthly_savings" in comparison_data.columns:
            comparison_data["savings_pct"] = (comparison_data["monthly_savings"] / comparison_data["current_monthly"] * 100).fillna(0)

        col1, col2 = st.columns(2)

        with col1:
            fig = px.bar(
                comparison_data.reset_index(),
                x=primary_group,
                y=["current_monthly", "monthly_savings"] if "monthly_savings" in comparison_data.columns else ["current_monthly"],
                barmode="group",
                color_discrete_sequence=['#f59e0b', '#10b981']
            )
            fig.update_layout(
                height=350,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#94a3b8'),
                xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
                yaxis=dict(gridcolor='rgba(255,255,255,0.05)')
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            if "cpu_p95" in comparison_data.columns and "memory_p95" in comparison_data.columns:
                fig = px.scatter(
                    comparison_data.reset_index(),
                    x="cpu_p95",
                    y="memory_p95",
                    size="server_count",
                    color=primary_group,
                    labels={"cpu_p95": "Avg CPU P95 %", "memory_p95": "Avg Memory P95 %"}
                )
                fig.update_layout(
                    height=350,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#94a3b8'),
                    xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
                    yaxis=dict(gridcolor='rgba(255,255,255,0.05)')
                )
                st.plotly_chart(fig, use_container_width=True)

        col_config = {
            "current_monthly": st.column_config.NumberColumn("Monthly Cost", format="$%.0f"),
        }
        if "monthly_savings" in comparison_data.columns:
            col_config["monthly_savings"] = st.column_config.NumberColumn("Savings", format="$%.0f")
            col_config["savings_pct"] = st.column_config.NumberColumn("Savings %", format="%.1f%%")
        if "cpu_p95" in comparison_data.columns:
            col_config["cpu_p95"] = st.column_config.NumberColumn("Avg CPU %", format="%.1f")
        if "memory_p95" in comparison_data.columns:
            col_config["memory_p95"] = st.column_config.NumberColumn("Avg Mem %", format="%.1f")

        st.dataframe(
            comparison_data.round(2),
            use_container_width=True,
            column_config=col_config
        )

# Export filtered data
st.divider()
csv = filtered_df.to_csv(index=False)
st.download_button(
    label="📥 Download Filtered Data (CSV)",
    data=csv,
    file_name=f"drill_down_{primary_group}_{selected_primary}.csv".replace(" ", "_"),
    mime="text/csv"
)

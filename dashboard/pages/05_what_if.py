"""What-If Scenario Analysis page."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from styles import inject_styles, page_header, section_header, chart_header, metrics_row

st.set_page_config(page_title="What-If Analysis", page_icon="🔮", layout="wide")
inject_styles()

page_header("🔮 What-If Scenario Analysis", "Model different optimization scenarios and compare outcomes")


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

# Scenario Builder
section_header("Scenario Builder")

col1, col2 = st.columns([2, 1])

with col1:
    chart_header("Select Servers to Optimize")

    # Filter options
    filter_col1, filter_col2, filter_col3 = st.columns(3)

    with filter_col1:
        class_filter = st.multiselect(
            "Classification",
            options=list(df["classification"].unique()) if "classification" in df.columns else [],
            default=["oversized"] if "classification" in df.columns and "oversized" in df["classification"].values else []
        )

    with filter_col2:
        if "risk_level" in df.columns:
            risk_filter = st.multiselect(
                "Risk Level",
                options=list(df["risk_level"].dropna().unique()),
                default=["low"] if "low" in df["risk_level"].values else []
            )
        else:
            risk_filter = []

    with filter_col3:
        min_savings = st.number_input(
            "Min Monthly Savings ($)",
            min_value=0,
            max_value=int(df["monthly_savings"].max()) if "monthly_savings" in df.columns else 1000,
            value=0
        )

    # Apply filters
    filtered_df = df.copy()
    if class_filter and "classification" in df.columns:
        filtered_df = filtered_df[filtered_df["classification"].isin(class_filter)]
    if risk_filter and "risk_level" in df.columns:
        filtered_df = filtered_df[filtered_df["risk_level"].isin(risk_filter)]
    if "monthly_savings" in df.columns:
        filtered_df = filtered_df[filtered_df["monthly_savings"] >= min_savings]

    # Server selection
    st.markdown(f"**{len(filtered_df)}** servers match your criteria")

    select_all = st.checkbox("Select all matching servers", value=True)

    if not select_all:
        selected_servers = st.multiselect(
            "Select specific servers:",
            options=filtered_df["hostname"].tolist() if "hostname" in filtered_df.columns else filtered_df.index.tolist(),
            default=[]
        )
        if selected_servers:
            filtered_df = filtered_df[filtered_df["hostname"].isin(selected_servers)]

with col2:
    chart_header("Scenario Summary")

    if len(filtered_df) > 0:
        current_cost = filtered_df["current_monthly"].sum() if "current_monthly" in filtered_df.columns else 0
        potential_savings = filtered_df[filtered_df["monthly_savings"] > 0]["monthly_savings"].sum() if "monthly_savings" in filtered_df.columns else 0

        st.metric("Servers Selected", len(filtered_df))
        st.metric("Current Monthly Cost", f"${current_cost:,.2f}")
        st.metric("Potential Savings", f"${potential_savings:,.2f}")
        st.metric("New Monthly Cost", f"${current_cost - potential_savings:,.2f}")

        savings_pct = (potential_savings / current_cost * 100) if current_cost > 0 else 0
        st.progress(min(savings_pct / 100, 1.0))
        st.caption(f"{savings_pct:.1f}% reduction")
    else:
        st.markdown("""
        <div class="info-box warning">
            No servers selected
        </div>
        """, unsafe_allow_html=True)

st.divider()

# Scenario Comparison
section_header("Scenario Comparison")

col1, col2 = st.columns(2)

with col1:
    chart_header("Implementation Timeline")

    implementation_pct = st.slider(
        "What percentage of recommendations will you implement?",
        min_value=0,
        max_value=100,
        value=75,
        step=5
    )

    months_to_implement = st.slider(
        "Over how many months?",
        min_value=1,
        max_value=12,
        value=3
    )

with col2:
    chart_header("Projected Savings")

    if len(filtered_df) > 0 and "monthly_savings" in filtered_df.columns:
        total_potential = filtered_df[filtered_df["monthly_savings"] > 0]["monthly_savings"].sum()
        actual_savings = total_potential * (implementation_pct / 100)

        # Build projection
        months = list(range(1, 13))
        monthly_implementation = actual_savings / months_to_implement

        cumulative_savings = []
        for m in months:
            if m <= months_to_implement:
                implemented = monthly_implementation * m
            else:
                implemented = actual_savings
            cumulative_savings.append(implemented * (m - (m - min(m, months_to_implement)) / 2))

        fig = go.Figure()

        # Actual projection
        fig.add_trace(go.Scatter(
            x=[f"Month {m}" for m in months],
            y=cumulative_savings,
            mode='lines+markers',
            name='Projected Savings',
            fill='tozeroy',
            fillcolor='rgba(16, 185, 129, 0.2)',
            line=dict(color='#10b981', width=3)
        ))

        # Maximum potential
        max_potential = [total_potential * m for m in months]
        fig.add_trace(go.Scatter(
            x=[f"Month {m}" for m in months],
            y=max_potential,
            mode='lines',
            name='Maximum Potential (100%)',
            line=dict(color='#64748b', dash='dash')
        ))

        fig.update_layout(
            height=350,
            yaxis_title="Cumulative Savings ($)",
            yaxis_tickformat="$,.0f",
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#94a3b8'),
            xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
            yaxis=dict(gridcolor='rgba(255,255,255,0.05)')
        )

        st.plotly_chart(fig, use_container_width=True)

        # Summary metrics
        year_end_savings = cumulative_savings[-1]
        st.markdown(f"""
        <div class="info-box success">
            <strong>12-Month Savings Projection: ${year_end_savings:,.0f}</strong>
        </div>
        """, unsafe_allow_html=True)

st.divider()

# Detailed Breakdown
section_header("Detailed Breakdown")

if len(filtered_df) > 0:
    available_groups = ["classification", "instance_type"]
    if "Environment" in filtered_df.columns:
        available_groups.append("Environment")

    group_by = st.selectbox(
        "Group by:",
        options=available_groups,
        index=0
    )

    if group_by in filtered_df.columns:
        grouped = filtered_df.groupby(group_by).agg({
            "current_monthly": "sum",
            "monthly_savings": lambda x: x[x > 0].sum(),
            "hostname": "count"
        }).rename(columns={"hostname": "server_count"})

        grouped["savings_after_implementation"] = grouped["monthly_savings"] * (implementation_pct / 100)

        st.dataframe(
            grouped.sort_values("savings_after_implementation", ascending=False),
            use_container_width=True,
            column_config={
                "current_monthly": st.column_config.NumberColumn("Current Cost", format="$%.2f"),
                "monthly_savings": st.column_config.NumberColumn("Max Savings", format="$%.2f"),
                "savings_after_implementation": st.column_config.NumberColumn("Projected Savings", format="$%.2f"),
                "server_count": st.column_config.NumberColumn("Servers"),
            }
        )

st.divider()

# Export scenario
section_header("Export Scenario")

col1, col2 = st.columns(2)

with col1:
    if len(filtered_df) > 0:
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Selected Servers (CSV)",
            data=csv,
            file_name="optimization_scenario.csv",
            mime="text/csv"
        )

with col2:
    st.markdown("""
    **Next Steps:**
    1. Review the selected servers
    2. Create change tickets for each server
    3. Schedule maintenance windows
    4. Implement changes incrementally
    5. Monitor for issues
    """)

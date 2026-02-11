"""Cost analysis page for the dashboard."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from styles import inject_styles, page_header, section_header, chart_header, metrics_row

st.set_page_config(page_title="Cost Analysis", page_icon="💰", layout="wide")
inject_styles()

page_header("💰 Cost Analysis", "Analyze current spend and potential savings")


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

if "current_monthly" not in df.columns:
    st.markdown("""
    <div class="info-box warning">
        <strong>Cost data not available</strong> in this report.
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# Summary metrics
section_header("Cost Overview")

total_current = df["current_monthly"].sum()
total_savings = df[df["monthly_savings"] > 0]["monthly_savings"].sum() if "monthly_savings" in df.columns else 0
total_optimized = total_current - total_savings
savings_pct = (total_savings / total_current * 100) if total_current > 0 else 0

st.markdown(metrics_row([
    ("💵", f"${total_current:,.0f}", "Current Monthly", "orange"),
    ("💰", f"${total_optimized:,.0f}", "After Optimization", "green"),
    ("📉", f"${total_savings:,.0f}", "Monthly Savings", "green"),
    ("📅", f"${total_savings * 12:,.0f}", "Yearly Savings", "green"),
]), unsafe_allow_html=True)

st.divider()

# Current vs Optimized comparison
section_header("Spend Comparison")

col1, col2 = st.columns(2)

with col1:
    chart_header("Current vs. Optimized Monthly Spend")
    fig = go.Figure(data=[
        go.Bar(name='Current', x=['Monthly Spend'], y=[total_current], marker_color='#f59e0b'),
        go.Bar(name='Optimized', x=['Monthly Spend'], y=[total_optimized], marker_color='#10b981')
    ])
    fig.update_layout(
        barmode='group',
        height=350,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#94a3b8'),
        xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
        yaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    chart_header("Savings Waterfall")
    fig = go.Figure(go.Waterfall(
        name="Savings",
        orientation="v",
        measure=["absolute", "relative", "total"],
        x=["Current Spend", "Savings", "Optimized Spend"],
        text=[f"${total_current:,.0f}", f"-${total_savings:,.0f}", f"${total_optimized:,.0f}"],
        y=[total_current, -total_savings, total_optimized],
        connector={"line": {"color": "rgba(255,255,255,0.2)"}},
        decreasing={"marker": {"color": "#10b981"}},
        increasing={"marker": {"color": "#ef4444"}},
        totals={"marker": {"color": "#3b82f6"}}
    ))
    fig.update_layout(
        height=350,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#94a3b8'),
        xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
        yaxis=dict(gridcolor='rgba(255,255,255,0.05)')
    )
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# Cost breakdown by instance type
section_header("Cost Breakdown")

col1, col2 = st.columns(2)

with col1:
    chart_header("By Instance Type")

    by_type = df.groupby("instance_type")["current_monthly"].sum().sort_values(ascending=False).head(10)

    fig = go.Figure(data=[go.Pie(
        labels=by_type.index,
        values=by_type.values,
        hole=0.5,
        marker_colors=['#FF9900', '#f59e0b', '#fbbf24', '#fcd34d', '#fde68a',
                       '#10b981', '#34d399', '#6ee7b7', '#a7f3d0', '#d1fae5'],
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
    chart_header("By Classification")

    if "classification" in df.columns:
        by_class = df.groupby("classification").agg({
            "current_monthly": "sum",
        }).reset_index()

        fig = px.bar(
            by_class,
            x="classification",
            y="current_monthly",
            color="classification",
            color_discrete_map={
                "oversized": "#10b981",
                "right_sized": "#64748b",
                "undersized": "#ef4444",
                "unknown": "#f59e0b"
            },
            text="current_monthly"
        )
        fig.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
        fig.update_layout(
            height=400,
            showlegend=False,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#94a3b8'),
            xaxis=dict(gridcolor='rgba(255,255,255,0.05)', title=""),
            yaxis=dict(gridcolor='rgba(255,255,255,0.05)', title="Monthly Spend ($)")
        )
        st.plotly_chart(fig, use_container_width=True)

st.divider()

# Savings by Environment/Tag
section_header("Savings by Environment")

tag_columns = [c for c in df.columns if c.upper() in ["GSI", "COST_CENTER", "PROJECT", "ENVIRONMENT"]]

if tag_columns and "monthly_savings" in df.columns:
    tag_col = tag_columns[0]

    by_tag = df.groupby(tag_col).agg({
        "current_monthly": "sum",
        "monthly_savings": lambda x: x[x > 0].sum()
    }).sort_values("monthly_savings", ascending=True).tail(15).reset_index()

    fig = px.bar(
        by_tag,
        y=tag_col,
        x="monthly_savings",
        orientation="h",
        color="monthly_savings",
        color_continuous_scale=[[0, '#064e3b'], [1, '#10b981']],
        text="monthly_savings"
    )
    fig.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
    fig.update_layout(
        height=500,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#94a3b8'),
        xaxis=dict(gridcolor='rgba(255,255,255,0.05)', title="Monthly Savings ($)"),
        yaxis=dict(gridcolor='rgba(255,255,255,0.05)', title=""),
        coloraxis_showscale=False
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No environment/tag data available for breakdown.")

st.divider()

# 12-month projection
section_header("12-Month Savings Projection")

months = list(range(1, 13))
month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
cumulative = [total_savings * m for m in months]

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=month_names,
    y=cumulative,
    mode='lines+markers',
    name='Cumulative Savings',
    line=dict(color='#10b981', width=3),
    fill='tozeroy',
    fillcolor='rgba(16, 185, 129, 0.15)'
))

fig.add_trace(go.Scatter(
    x=month_names,
    y=[total_savings] * 12,
    mode='lines',
    name='Monthly Savings',
    line=dict(color='#FF9900', dash='dash', width=2)
))

fig.update_layout(
    xaxis_title="Month",
    yaxis_title="Savings ($)",
    height=400,
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(color='#94a3b8'),
    xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
    yaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

st.plotly_chart(fig, use_container_width=True)

# Summary table
chart_header("Monthly Projection Details")

projection_data = []
running_total = 0

for i, month in enumerate(month_names):
    running_total += total_savings
    projection_data.append({
        "Month": month,
        "Monthly Savings": f"${total_savings:,.0f}",
        "Cumulative Savings": f"${running_total:,.0f}"
    })

st.dataframe(
    pd.DataFrame(projection_data),
    use_container_width=True,
    hide_index=True
)

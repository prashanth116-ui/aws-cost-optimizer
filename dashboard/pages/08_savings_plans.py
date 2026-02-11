"""Savings Plans & Reserved Instances Analysis page."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from styles import inject_styles, page_header, section_header, chart_header, metrics_row

st.set_page_config(page_title="Savings Plans", page_icon="💳", layout="wide")
inject_styles()

page_header("💳 Savings Plans & Reserved Instances", "Compare On-Demand, Savings Plans, and Reserved Instance pricing")

# Discount rates (approximate)
PRICING_OPTIONS = {
    "On-Demand": {"discount": 0, "commitment": "None", "flexibility": "High"},
    "Savings Plan (1yr, No Upfront)": {"discount": 25, "commitment": "1 year", "flexibility": "Medium"},
    "Savings Plan (1yr, All Upfront)": {"discount": 32, "commitment": "1 year", "flexibility": "Medium"},
    "Savings Plan (3yr, No Upfront)": {"discount": 40, "commitment": "3 years", "flexibility": "Medium"},
    "Savings Plan (3yr, All Upfront)": {"discount": 52, "commitment": "3 years", "flexibility": "Medium"},
    "Reserved (1yr, No Upfront)": {"discount": 30, "commitment": "1 year", "flexibility": "Low"},
    "Reserved (1yr, All Upfront)": {"discount": 37, "commitment": "1 year", "flexibility": "Low"},
    "Reserved (3yr, No Upfront)": {"discount": 45, "commitment": "3 years", "flexibility": "Low"},
    "Reserved (3yr, All Upfront)": {"discount": 60, "commitment": "3 years", "flexibility": "Low"},
}


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

# Current spend
if "current_monthly" not in df.columns:
    st.markdown("""
    <div class="info-box warning">
        <strong>Cost data not available</strong> in this report.
    </div>
    """, unsafe_allow_html=True)
    st.stop()

total_on_demand = df["current_monthly"].sum()

section_header("Current Spend Overview")

st.markdown(metrics_row([
    ("💵", f"${total_on_demand:,.0f}", "Monthly (On-Demand)", "orange"),
    ("📅", f"${total_on_demand * 12:,.0f}", "Yearly (On-Demand)", "orange"),
    ("🖥️", len(df), "Servers Analyzed"),
]), unsafe_allow_html=True)

st.divider()

# Pricing comparison
section_header("Pricing Model Comparison")

comparison_data = []
for option, details in PRICING_OPTIONS.items():
    discount = details["discount"]
    monthly = total_on_demand * (1 - discount / 100)
    yearly = monthly * 12
    savings_monthly = total_on_demand - monthly
    savings_yearly = savings_monthly * 12

    comparison_data.append({
        "Pricing Option": option,
        "Discount": f"{discount}%",
        "Monthly Cost": monthly,
        "Yearly Cost": yearly,
        "Monthly Savings": savings_monthly,
        "Yearly Savings": savings_yearly,
        "Commitment": details["commitment"],
        "Flexibility": details["flexibility"],
    })

comparison_df = pd.DataFrame(comparison_data)

st.dataframe(
    comparison_df,
    use_container_width=True,
    column_config={
        "Monthly Cost": st.column_config.NumberColumn(format="$%.0f"),
        "Yearly Cost": st.column_config.NumberColumn(format="$%.0f"),
        "Monthly Savings": st.column_config.NumberColumn(format="$%.0f"),
        "Yearly Savings": st.column_config.NumberColumn(format="$%.0f"),
    },
    hide_index=True
)

chart_header("Cost Comparison Chart")

fig = go.Figure()

fig.add_trace(go.Bar(
    name="Monthly Cost",
    x=comparison_df["Pricing Option"],
    y=comparison_df["Monthly Cost"],
    marker_color=["#ef4444" if "On-Demand" in x else "#10b981" for x in comparison_df["Pricing Option"]]
))

fig.add_hline(
    y=total_on_demand,
    line_dash="dash",
    line_color="#ef4444",
    annotation_text="On-Demand Baseline",
    annotation_font_color="#94a3b8"
)

fig.update_layout(
    height=400,
    xaxis_tickangle=45,
    yaxis_title="Monthly Cost ($)",
    yaxis_tickformat="$,.0f",
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(color='#94a3b8'),
    xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
    yaxis=dict(gridcolor='rgba(255,255,255,0.05)')
)

st.plotly_chart(fig, use_container_width=True)

st.divider()

# Recommendation Engine
section_header("Recommendation")

col1, col2 = st.columns(2)

with col1:
    chart_header("Your Workload Profile")

    workload_stability = st.select_slider(
        "Workload Stability",
        options=["Highly Variable", "Somewhat Variable", "Mostly Stable", "Very Stable"],
        value="Mostly Stable"
    )

    commitment_preference = st.select_slider(
        "Commitment Preference",
        options=["No Commitment", "1 Year OK", "3 Years OK"],
        value="1 Year OK"
    )

    flexibility_need = st.select_slider(
        "Flexibility Need",
        options=["Must Change Frequently", "Occasional Changes", "Rarely Changes"],
        value="Occasional Changes"
    )

with col2:
    chart_header("Our Recommendation")

    # Simple recommendation logic
    if workload_stability in ["Highly Variable", "Somewhat Variable"]:
        if commitment_preference == "No Commitment":
            recommended = "On-Demand"
            reason = "Your variable workload and no-commitment preference make On-Demand the safest choice."
        else:
            recommended = "Savings Plan (1yr, No Upfront)"
            reason = "Savings Plans offer flexibility for variable workloads with good savings."
    elif commitment_preference == "3 Years OK" and flexibility_need == "Rarely Changes":
        recommended = "Reserved (3yr, All Upfront)"
        reason = "Stable workload with long commitment = maximum savings with Reserved Instances."
    elif commitment_preference == "3 Years OK":
        recommended = "Savings Plan (3yr, All Upfront)"
        reason = "Good savings with flexibility to change instance types."
    elif commitment_preference == "1 Year OK":
        recommended = "Savings Plan (1yr, All Upfront)"
        reason = "Balanced savings and flexibility with 1-year commitment."
    else:
        recommended = "On-Demand"
        reason = "No commitment preference suggests staying with On-Demand."

    rec_details = PRICING_OPTIONS[recommended]
    rec_monthly = total_on_demand * (1 - rec_details["discount"] / 100)
    rec_savings = total_on_demand - rec_monthly

    st.markdown(f"""
    <div class="info-box success">
        <strong>Recommended: {recommended}</strong><br>
        {reason}
    </div>
    """, unsafe_allow_html=True)

    st.metric("Projected Monthly Cost", f"${rec_monthly:,.0f}")
    st.metric("Monthly Savings vs On-Demand", f"${rec_savings:,.0f}")
    st.metric("Yearly Savings", f"${rec_savings * 12:,.0f}")

st.divider()

# Break-even analysis
section_header("Break-Even Analysis")

st.markdown("When does the upfront payment pay off?")

# Calculate break-even for 1yr All Upfront Reserved
reserved_discount = PRICING_OPTIONS["Reserved (1yr, All Upfront)"]["discount"]
reserved_monthly = total_on_demand * (1 - reserved_discount / 100)
monthly_savings = total_on_demand - reserved_monthly

upfront_cost = reserved_monthly * 12 * 0.9
break_even_months = upfront_cost / monthly_savings if monthly_savings > 0 else 12

col1, col2 = st.columns(2)

with col1:
    months = list(range(1, 37))

    on_demand_cumulative = [total_on_demand * m for m in months]
    reserved_cumulative = [upfront_cost + (reserved_monthly * m) for m in months]
    savings_plan_monthly = total_on_demand * (1 - PRICING_OPTIONS["Savings Plan (1yr, All Upfront)"]["discount"] / 100)
    savings_plan_cumulative = [savings_plan_monthly * m for m in months]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=months, y=on_demand_cumulative,
        name="On-Demand",
        line=dict(color="#ef4444", width=2)
    ))

    fig.add_trace(go.Scatter(
        x=months, y=reserved_cumulative,
        name="Reserved (1yr, All Upfront)",
        line=dict(color="#10b981", width=2)
    ))

    fig.add_trace(go.Scatter(
        x=months, y=savings_plan_cumulative,
        name="Savings Plan (1yr)",
        line=dict(color="#3b82f6", width=2)
    ))

    fig.update_layout(
        xaxis_title="Months",
        yaxis_title="Cumulative Cost ($)",
        yaxis_tickformat="$,.0f",
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#94a3b8'),
        xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
        yaxis=dict(gridcolor='rgba(255,255,255,0.05)')
    )

    st.plotly_chart(fig, use_container_width=True)

with col2:
    chart_header("Key Insights")

    st.markdown(f"""
    - **Break-even point**: ~{break_even_months:.0f} months for Reserved with upfront
    - **3-year savings**: Reserved Instances save up to 60% over On-Demand
    - **Flexibility trade-off**: Savings Plans allow instance family changes
    - **Recommendation**: Consider Savings Plans for most workloads

    **Tips:**
    1. Start with Savings Plans for new commitments
    2. Use Reserved Instances for stable, predictable workloads
    3. Keep some On-Demand capacity for variable needs
    4. Review commitments quarterly
    """)

st.divider()

# Coverage calculator
section_header("Coverage Calculator")

st.markdown("How much of your workload should be covered by commitments?")

coverage_pct = st.slider(
    "Commitment Coverage (%)",
    min_value=0,
    max_value=100,
    value=70,
    help="Percentage of workload to cover with Savings Plans or Reserved Instances"
)

commitment_type = st.selectbox(
    "Commitment Type",
    options=["Savings Plan (1yr, No Upfront)", "Savings Plan (3yr, No Upfront)",
             "Reserved (1yr, All Upfront)", "Reserved (3yr, All Upfront)"]
)

committed_spend = total_on_demand * (coverage_pct / 100)
on_demand_spend = total_on_demand * (1 - coverage_pct / 100)

commitment_discount = PRICING_OPTIONS[commitment_type]["discount"]
committed_after_discount = committed_spend * (1 - commitment_discount / 100)

total_blended = committed_after_discount + on_demand_spend
blended_savings = total_on_demand - total_blended
effective_discount = (blended_savings / total_on_demand * 100) if total_on_demand > 0 else 0

st.markdown(metrics_row([
    ("💵", f"${total_blended:,.0f}", "Blended Monthly", "green"),
    ("💰", f"${blended_savings:,.0f}", "Monthly Savings", "green"),
    ("📉", f"{effective_discount:.1f}%", "Effective Discount", "green"),
]), unsafe_allow_html=True)

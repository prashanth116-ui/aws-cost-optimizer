"""Multi-Account Analysis page."""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from styles import inject_styles, page_header, section_header, chart_header, metrics_row

st.set_page_config(page_title="Multi-Account", page_icon="🏢", layout="wide")
inject_styles()

page_header("🏢 Multi-Account Analysis", "Analyze costs and optimization opportunities across AWS accounts")


def load_multi_account_data():
    """Load multi-account data from session state."""
    if "multi_account_summary" in st.session_state:
        return st.session_state["multi_account_summary"]
    return None


def simulate_multi_account_data():
    """Generate sample multi-account data."""
    return {
        "total_accounts": 4, "successful_accounts": 3, "failed_accounts": 1, "total_instances": 245,
        "total_current_monthly": 125000.00, "total_potential_savings": 28750.00,
        "by_account": {
            "123456789012": {"name": "Production", "instance_count": 120, "monthly_cost": 75000.00, "potential_savings": 15000.00, "savings_percent": 20.0, "oversized": 25, "right_sized": 85, "undersized": 10, "status": "success"},
            "234567890123": {"name": "Development", "instance_count": 80, "monthly_cost": 32000.00, "potential_savings": 9600.00, "savings_percent": 30.0, "oversized": 35, "right_sized": 40, "undersized": 5, "status": "success"},
            "345678901234": {"name": "Staging", "instance_count": 45, "monthly_cost": 18000.00, "potential_savings": 4150.00, "savings_percent": 23.1, "oversized": 12, "right_sized": 28, "undersized": 5, "status": "success"},
            "456789012345": {"name": "Sandbox", "instance_count": 0, "monthly_cost": 0, "potential_savings": 0, "savings_percent": 0, "status": "failed", "error": "Access denied: Role assumption failed"},
        },
        "analysis_duration_seconds": 45.3,
    }


data = load_multi_account_data()
if data is None:
    st.info("No multi-account data loaded. Showing sample data for demonstration.")
    data = simulate_multi_account_data()

section_header("Organization Overview")

savings = data.get("total_potential_savings", 0)
savings_pct = (savings / data['total_current_monthly'] * 100) if data['total_current_monthly'] > 0 else 0

st.markdown(metrics_row([
    ("🏢", data["total_accounts"], "Accounts"),
    ("✅", data["successful_accounts"], "Successful", "green"),
    ("🖥️", data["total_instances"], "Total Instances"),
    ("💵", f"${data['total_current_monthly']:,.0f}", "Monthly Spend", "orange"),
    ("💰", f"${savings:,.0f}", f"Savings ({savings_pct:.0f}%)", "green"),
]), unsafe_allow_html=True)

if data.get("analysis_duration_seconds"):
    st.caption(f"Analysis completed in {data['analysis_duration_seconds']:.1f} seconds")

st.divider()

section_header("Account Breakdown")

by_account = data.get("by_account", {})

if by_account:
    successful_accounts = {k: v for k, v in by_account.items() if v.get("status") == "success"}
    failed_accounts = {k: v for k, v in by_account.items() if v.get("status") != "success"}

    if successful_accounts:
        account_df = pd.DataFrame([{
            "Account ID": aid, "Name": info["name"], "Instances": info["instance_count"],
            "Monthly Cost": info["monthly_cost"], "Potential Savings": info.get("potential_savings", 0),
            "Savings %": info.get("savings_percent", 0), "Oversized": info.get("oversized", 0),
            "Right-sized": info.get("right_sized", 0), "Undersized": info.get("undersized", 0),
        } for aid, info in successful_accounts.items()])

        st.dataframe(account_df, use_container_width=True, column_config={
            "Monthly Cost": st.column_config.NumberColumn("Monthly Cost", format="$%.0f"),
            "Potential Savings": st.column_config.NumberColumn("Potential Savings", format="$%.0f"),
            "Savings %": st.column_config.NumberColumn("Savings %", format="%.1f%%"),
        })

        col1, col2 = st.columns(2)
        with col1:
            chart_header("Cost by Account")
            fig = go.Figure(data=[go.Pie(labels=account_df["Name"], values=account_df["Monthly Cost"], hole=0.5, marker_colors=['#FF9900', '#10b981', '#3b82f6', '#f59e0b'])])
            fig.update_layout(height=350, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#94a3b8'))
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            chart_header("Savings Opportunity by Account")
            fig = px.bar(account_df.sort_values("Potential Savings", ascending=True), x="Potential Savings", y="Name", orientation="h", color="Savings %", color_continuous_scale=[[0, '#064e3b'], [1, '#10b981']])
            fig.update_layout(height=350, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#94a3b8'), xaxis=dict(gridcolor='rgba(255,255,255,0.05)', title="Monthly Savings ($)"), yaxis=dict(gridcolor='rgba(255,255,255,0.05)', title=""), coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)

        chart_header("Instance Classification by Account")
        class_data = []
        for aid, info in successful_accounts.items():
            class_data.extend([
                {"Account": info["name"], "Classification": "Oversized", "Count": info.get("oversized", 0)},
                {"Account": info["name"], "Classification": "Right-sized", "Count": info.get("right_sized", 0)},
                {"Account": info["name"], "Classification": "Undersized", "Count": info.get("undersized", 0)},
            ])
        class_df = pd.DataFrame(class_data)
        fig = px.bar(class_df, x="Account", y="Count", color="Classification", barmode="stack", color_discrete_map={"Oversized": "#10b981", "Right-sized": "#64748b", "Undersized": "#ef4444"})
        fig.update_layout(height=400, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#94a3b8'), xaxis=dict(gridcolor='rgba(255,255,255,0.05)'), yaxis=dict(gridcolor='rgba(255,255,255,0.05)'))
        st.plotly_chart(fig, use_container_width=True)

    if failed_accounts:
        chart_header("Failed Accounts")
        st.markdown(f"""
        <div class="info-box error">
            <strong>{len(failed_accounts)} account(s)</strong> could not be analyzed
        </div>
        """, unsafe_allow_html=True)

        for aid, info in failed_accounts.items():
            with st.expander(f"{info.get('name', aid)} ({aid})"):
                st.error(info.get("error", "Unknown error"))
                st.markdown("**To fix:** Ensure `CostOptimizerRole` exists with correct trust policy and permissions")
else:
    st.info("No account data available.")

st.divider()

section_header("Configuration")

with st.expander("Multi-Account Setup Guide"):
    st.markdown("""
    ### Prerequisites
    1. **AWS Organizations** - Accounts must be part of an AWS Organization
    2. **Cross-Account Role** - Each member account needs a role that can be assumed

    ### Step 1: Create IAM Role in Member Accounts
    Create `CostOptimizerRole` with trust policy and EC2/Cost Explorer permissions.

    ### Step 2: Configure Multi-Account Mode
    ```yaml
    organizations:
      enabled: true
      role_name: "CostOptimizerRole"
      accounts:
        - account_id: "123456789012"
          name: "Production"
    ```

    ### Step 3: Run Analysis
    ```bash
    python run.py --multi-account --output multi_account_report.xlsx
    ```
    """)

if by_account:
    export_data = [{"account_id": aid, "account_name": info.get("name", ""), "status": info.get("status", ""), "instance_count": info.get("instance_count", 0), "monthly_cost": info.get("monthly_cost", 0), "potential_savings": info.get("potential_savings", 0)} for aid, info in by_account.items()]
    csv = pd.DataFrame(export_data).to_csv(index=False)
    st.download_button(label="📥 Download Account Summary CSV", data=csv, file_name=f"multi_account_summary_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")

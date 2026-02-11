"""Multi-Account Analysis page."""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Multi-Account", page_icon="", layout="wide")

st.title("Multi-Account Analysis")
st.markdown("Analyze costs and optimization opportunities across AWS accounts.")


def load_multi_account_data():
    """Load multi-account data from session state."""
    if "multi_account_summary" in st.session_state:
        return st.session_state["multi_account_summary"]
    return None


def simulate_multi_account_data():
    """Generate sample multi-account data for demonstration."""
    return {
        "total_accounts": 4,
        "successful_accounts": 3,
        "failed_accounts": 1,
        "total_instances": 245,
        "total_current_monthly": 125000.00,
        "total_potential_savings": 28750.00,
        "by_account": {
            "123456789012": {
                "name": "Production",
                "instance_count": 120,
                "monthly_cost": 75000.00,
                "potential_savings": 15000.00,
                "savings_percent": 20.0,
                "oversized": 25,
                "right_sized": 85,
                "undersized": 10,
                "status": "success",
            },
            "234567890123": {
                "name": "Development",
                "instance_count": 80,
                "monthly_cost": 32000.00,
                "potential_savings": 9600.00,
                "savings_percent": 30.0,
                "oversized": 35,
                "right_sized": 40,
                "undersized": 5,
                "status": "success",
            },
            "345678901234": {
                "name": "Staging",
                "instance_count": 45,
                "monthly_cost": 18000.00,
                "potential_savings": 4150.00,
                "savings_percent": 23.1,
                "oversized": 12,
                "right_sized": 28,
                "undersized": 5,
                "status": "success",
            },
            "456789012345": {
                "name": "Sandbox",
                "instance_count": 0,
                "monthly_cost": 0,
                "potential_savings": 0,
                "savings_percent": 0,
                "status": "failed",
                "error": "Access denied: Role assumption failed",
            },
        },
        "analysis_duration_seconds": 45.3,
    }


# Load or simulate data
data = load_multi_account_data()

if data is None:
    st.info("No multi-account data loaded. Showing sample data for demonstration.")
    data = simulate_multi_account_data()

# Summary metrics
st.header("Organization Overview")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Accounts", data["total_accounts"])

with col2:
    st.metric(
        "Successful",
        data["successful_accounts"],
        delta=None
    )

with col3:
    st.metric("Total Instances", data["total_instances"])

with col4:
    st.metric(
        "Monthly Spend",
        f"${data['total_current_monthly']:,.0f}"
    )

with col5:
    savings = data.get("total_potential_savings", 0)
    st.metric(
        "Potential Savings",
        f"${savings:,.0f}",
        delta=f"{(savings / data['total_current_monthly'] * 100) if data['total_current_monthly'] > 0 else 0:.1f}%"
    )

if data.get("analysis_duration_seconds"):
    st.caption(f"Analysis completed in {data['analysis_duration_seconds']:.1f} seconds")

st.divider()

# Account breakdown
st.header("Account Breakdown")

by_account = data.get("by_account", {})

if by_account:
    # Filter to successful accounts
    successful_accounts = {
        k: v for k, v in by_account.items()
        if v.get("status") == "success"
    }
    failed_accounts = {
        k: v for k, v in by_account.items()
        if v.get("status") != "success"
    }

    if successful_accounts:
        # Create DataFrame for table
        account_df = pd.DataFrame([
            {
                "Account ID": account_id,
                "Name": info["name"],
                "Instances": info["instance_count"],
                "Monthly Cost": info["monthly_cost"],
                "Potential Savings": info.get("potential_savings", 0),
                "Savings %": info.get("savings_percent", 0),
                "Oversized": info.get("oversized", 0),
                "Right-sized": info.get("right_sized", 0),
                "Undersized": info.get("undersized", 0),
            }
            for account_id, info in successful_accounts.items()
        ])

        st.dataframe(
            account_df,
            use_container_width=True,
            column_config={
                "Monthly Cost": st.column_config.NumberColumn("Monthly Cost", format="$%.0f"),
                "Potential Savings": st.column_config.NumberColumn("Potential Savings", format="$%.0f"),
                "Savings %": st.column_config.NumberColumn("Savings %", format="%.1f%%"),
            }
        )

        # Cost distribution chart
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Cost by Account")

            fig = px.pie(
                account_df,
                values="Monthly Cost",
                names="Name",
                hole=0.4,
            )
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Savings Opportunity by Account")

            fig = px.bar(
                account_df.sort_values("Potential Savings", ascending=True),
                x="Potential Savings",
                y="Name",
                orientation="h",
                color="Savings %",
                color_continuous_scale="Greens",
            )
            fig.update_layout(
                height=350,
                xaxis_title="Monthly Savings ($)",
                yaxis_title="",
            )
            st.plotly_chart(fig, use_container_width=True)

        # Classification breakdown
        st.subheader("Instance Classification by Account")

        classification_data = []
        for account_id, info in successful_accounts.items():
            classification_data.extend([
                {"Account": info["name"], "Classification": "Oversized", "Count": info.get("oversized", 0)},
                {"Account": info["name"], "Classification": "Right-sized", "Count": info.get("right_sized", 0)},
                {"Account": info["name"], "Classification": "Undersized", "Count": info.get("undersized", 0)},
            ])

        class_df = pd.DataFrame(classification_data)

        fig = px.bar(
            class_df,
            x="Account",
            y="Count",
            color="Classification",
            barmode="stack",
            color_discrete_map={
                "Oversized": "#28a745",
                "Right-sized": "#6c757d",
                "Undersized": "#dc3545",
            }
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    # Show failed accounts
    if failed_accounts:
        st.subheader("Failed Accounts")
        st.warning(f"{len(failed_accounts)} account(s) could not be analyzed.")

        for account_id, info in failed_accounts.items():
            with st.expander(f"{info.get('name', account_id)} ({account_id})"):
                st.error(info.get("error", "Unknown error"))
                st.markdown("""
                **Possible causes:**
                - Role does not exist in target account
                - Insufficient permissions on the role
                - Trust policy not configured correctly

                **To fix:**
                1. Ensure the `CostOptimizerRole` exists in the target account
                2. Verify the trust policy allows assumption from the management account
                3. Check the role has the required permissions (EC2, Cost Explorer)
                """)

else:
    st.info("No account data available.")

st.divider()

# Configuration section
st.header("Configuration")

with st.expander("Multi-Account Setup Guide", expanded=False):
    st.markdown("""
    ### Prerequisites

    1. **AWS Organizations** - Your accounts must be part of an AWS Organization
    2. **Cross-Account Role** - Each member account needs a role that can be assumed

    ### Step 1: Create the IAM Role in Member Accounts

    Create a role named `CostOptimizerRole` with this trust policy:

    ```json
    {
      "Version": "2012-10-17",
      "Statement": [
        {
          "Effect": "Allow",
          "Principal": {
            "AWS": "arn:aws:iam::MANAGEMENT_ACCOUNT_ID:root"
          },
          "Action": "sts:AssumeRole"
        }
      ]
    }
    ```

    Attach this permissions policy:

    ```json
    {
      "Version": "2012-10-17",
      "Statement": [
        {
          "Effect": "Allow",
          "Action": [
            "ec2:DescribeInstances",
            "ec2:DescribeInstanceTypes",
            "ce:GetCostAndUsage",
            "pricing:GetProducts"
          ],
          "Resource": "*"
        }
      ]
    }
    ```

    ### Step 2: Configure Multi-Account Mode

    In `config/config.yaml`:

    ```yaml
    organizations:
      enabled: true
      role_name: "CostOptimizerRole"
      # Optional: explicit account list
      accounts:
        - account_id: "123456789012"
          name: "Production"
        - account_id: "234567890123"
          name: "Development"
    ```

    ### Step 3: Run Multi-Account Analysis

    ```bash
    python run.py --multi-account --output multi_account_report.xlsx
    ```
    """)

with st.expander("Validate Account Access", expanded=False):
    st.markdown("""
    To validate access to all accounts before running a full analysis:

    ```bash
    python run.py --validate-multi-account
    ```

    This will attempt to assume the role in each account and report success/failure.
    """)

# Export
st.header("Export")

if by_account:
    # Create export data
    export_data = []
    for account_id, info in by_account.items():
        export_data.append({
            "account_id": account_id,
            "account_name": info.get("name", ""),
            "status": info.get("status", ""),
            "instance_count": info.get("instance_count", 0),
            "monthly_cost": info.get("monthly_cost", 0),
            "potential_savings": info.get("potential_savings", 0),
            "oversized": info.get("oversized", 0),
            "right_sized": info.get("right_sized", 0),
            "undersized": info.get("undersized", 0),
            "error": info.get("error", ""),
        })

    csv = pd.DataFrame(export_data).to_csv(index=False)
    st.download_button(
        label="Download Account Summary CSV",
        data=csv,
        file_name=f"multi_account_summary_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

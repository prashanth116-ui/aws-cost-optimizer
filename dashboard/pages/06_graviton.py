"""Graviton Migration Recommendations page."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from styles import inject_styles, page_header, section_header, chart_header, metrics_row

st.set_page_config(page_title="Graviton Recommendations", page_icon="🚀", layout="wide")
inject_styles()

page_header("🚀 Graviton Migration", "Identify instances that can migrate to ARM-based Graviton for additional savings")

# Graviton equivalents mapping
GRAVITON_EQUIVALENTS = {
    "m5.large": {"graviton": "m6g.large", "savings_pct": 20},
    "m5.xlarge": {"graviton": "m6g.xlarge", "savings_pct": 20},
    "m5.2xlarge": {"graviton": "m6g.2xlarge", "savings_pct": 20},
    "m5.4xlarge": {"graviton": "m6g.4xlarge", "savings_pct": 20},
    "c5.large": {"graviton": "c6g.large", "savings_pct": 20},
    "c5.xlarge": {"graviton": "c6g.xlarge", "savings_pct": 20},
    "c5.2xlarge": {"graviton": "c6g.2xlarge", "savings_pct": 20},
    "c5.4xlarge": {"graviton": "c6g.4xlarge", "savings_pct": 20},
    "r5.large": {"graviton": "r6g.large", "savings_pct": 20},
    "r5.xlarge": {"graviton": "r6g.xlarge", "savings_pct": 20},
    "r5.2xlarge": {"graviton": "r6g.2xlarge", "savings_pct": 20},
    "r5.4xlarge": {"graviton": "r6g.4xlarge", "savings_pct": 20},
    "t3.micro": {"graviton": "t4g.micro", "savings_pct": 20},
    "t3.small": {"graviton": "t4g.small", "savings_pct": 20},
    "t3.medium": {"graviton": "t4g.medium", "savings_pct": 20},
    "t3.large": {"graviton": "t4g.large", "savings_pct": 20},
    "t3.xlarge": {"graviton": "t4g.xlarge", "savings_pct": 20},
}

COMPATIBLE_WORKLOADS = [
    "Web servers", "Application servers", "Microservices", "Containerized apps",
    "Open-source databases", "In-memory caches", "Gaming servers", "Media encoding",
]

INCOMPATIBLE_WORKLOADS = [
    "Windows applications", "x86-specific software", "Legacy 32-bit apps", "Some commercial databases",
]


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

# Analyze Graviton eligibility
section_header("Graviton Eligibility Analysis")


def analyze_graviton_eligibility(row):
    """Determine if an instance can migrate to Graviton."""
    instance_type = row.get("instance_type", "")

    if instance_type in GRAVITON_EQUIVALENTS:
        equiv = GRAVITON_EQUIVALENTS[instance_type]
        current_cost = row.get("current_monthly", 0)
        graviton_savings = current_cost * (equiv["savings_pct"] / 100)
        return {
            "eligible": True,
            "graviton_type": equiv["graviton"],
            "savings_pct": equiv["savings_pct"],
            "monthly_savings_graviton": graviton_savings,
            "yearly_savings_graviton": graviton_savings * 12,
        }

    return {
        "eligible": False,
        "graviton_type": None,
        "savings_pct": 0,
        "monthly_savings_graviton": 0,
        "yearly_savings_graviton": 0,
    }


# Add Graviton analysis to dataframe
graviton_analysis = df.apply(analyze_graviton_eligibility, axis=1, result_type="expand")
df_graviton = pd.concat([df, graviton_analysis], axis=1)

eligible_df = df_graviton[df_graviton["eligible"] == True]
ineligible_df = df_graviton[df_graviton["eligible"] == False]

# Summary metrics
total_graviton_savings = eligible_df["monthly_savings_graviton"].sum()

st.markdown(metrics_row([
    ("✅", len(eligible_df), "Graviton Eligible", "green"),
    ("❌", len(ineligible_df), "Not Eligible"),
    ("💵", f"${total_graviton_savings:,.0f}", "Monthly Savings", "green"),
    ("📅", f"${total_graviton_savings * 12:,.0f}", "Yearly Savings", "green"),
]), unsafe_allow_html=True)

st.divider()

# Eligible instances
col1, col2 = st.columns([2, 1])

with col1:
    section_header("Graviton Migration Candidates")

    if len(eligible_df) > 0:
        display_df = eligible_df[[
            "hostname", "instance_type", "graviton_type",
            "current_monthly", "monthly_savings_graviton", "savings_pct"
        ]].copy()

        display_df = display_df.sort_values("monthly_savings_graviton", ascending=False)

        st.dataframe(
            display_df,
            use_container_width=True,
            height=400,
            column_config={
                "hostname": "Server",
                "instance_type": "Current Type",
                "graviton_type": "Graviton Type",
                "current_monthly": st.column_config.NumberColumn("Current Cost", format="$%.2f"),
                "monthly_savings_graviton": st.column_config.NumberColumn("Monthly Savings", format="$%.2f"),
                "savings_pct": st.column_config.NumberColumn("Savings %", format="%d%%"),
            }
        )
    else:
        st.info("No instances eligible for Graviton migration in current data.")

with col2:
    chart_header("Savings by Instance Family")

    if len(eligible_df) > 0:
        eligible_df["family"] = eligible_df["instance_type"].str.split(".").str[0]

        by_family = eligible_df.groupby("family").agg({
            "monthly_savings_graviton": "sum",
            "hostname": "count"
        }).rename(columns={"hostname": "count"})

        fig = go.Figure(data=[go.Pie(
            labels=by_family.index,
            values=by_family["monthly_savings_graviton"],
            hole=0.5,
            marker_colors=['#FF9900', '#10b981', '#3b82f6', '#f59e0b', '#8b5cf6'],
            textinfo='label+percent',
            textfont_size=11
        )])
        fig.update_layout(
            height=350,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#94a3b8'),
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)

st.divider()

# Compatibility checklist
section_header("Migration Compatibility Checklist")

col1, col2 = st.columns(2)

with col1:
    chart_header("Compatible Workloads")
    for workload in COMPATIBLE_WORKLOADS:
        st.markdown(f"✅ {workload}")

with col2:
    chart_header("Requires Validation")
    for workload in INCOMPATIBLE_WORKLOADS:
        st.markdown(f"⚠️ {workload}")

st.divider()

# Migration plan
section_header("Migration Plan Generator")

if len(eligible_df) > 0:
    st.markdown("**Select servers to include in migration plan:**")

    selected_for_migration = st.multiselect(
        "Select servers:",
        options=eligible_df["hostname"].tolist() if "hostname" in eligible_df.columns else [],
        default=eligible_df["hostname"].tolist()[:5] if "hostname" in eligible_df.columns else []
    )

    if selected_for_migration:
        migration_df = eligible_df[eligible_df["hostname"].isin(selected_for_migration)]

        chart_header("Migration Summary")

        total_migration_savings = migration_df["monthly_savings_graviton"].sum()

        st.markdown(metrics_row([
            ("🖥️", len(migration_df), "Servers to Migrate"),
            ("💵", f"${total_migration_savings:,.2f}", "Monthly Savings", "green"),
            ("📅", f"${total_migration_savings * 12:,.2f}", "Yearly Savings", "green"),
        ]), unsafe_allow_html=True)

        # Export migration plan
        st.markdown("### Export Migration Plan")

        migration_plan = migration_df[[
            "hostname", "instance_type", "graviton_type", "monthly_savings_graviton"
        ]].copy()
        migration_plan["migration_status"] = "Planned"
        migration_plan["target_date"] = ""
        migration_plan["notes"] = ""

        csv = migration_plan.to_csv(index=False)
        st.download_button(
            label="📥 Download Migration Plan (CSV)",
            data=csv,
            file_name="graviton_migration_plan.csv",
            mime="text/csv"
        )

st.divider()

# Additional resources
section_header("Resources")

st.markdown("""
**AWS Graviton Documentation:**
- [AWS Graviton Processor](https://aws.amazon.com/ec2/graviton/)
- [Graviton Getting Started Guide](https://github.com/aws/aws-graviton-getting-started)
- [Graviton Technical Guide](https://docs.aws.amazon.com/whitepapers/latest/aws-graviton-performance-testing/aws-graviton-performance-testing.html)

**Key Benefits:**
- Up to 40% better price-performance vs x86
- Built by AWS using 64-bit Arm Neoverse cores
- Supported by most Linux distributions
- Compatible with containers and Kubernetes
""")

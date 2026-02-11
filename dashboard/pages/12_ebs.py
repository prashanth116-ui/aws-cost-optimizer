"""EBS Volumes Analysis page."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from styles import inject_styles, page_header, section_header, chart_header, metrics_row

st.set_page_config(page_title="EBS Analysis", page_icon="💾", layout="wide")
inject_styles()

page_header("💾 EBS Volume Analysis", "Identify unattached volumes, optimize storage types, and reduce EBS costs")

EBS_PRICING = {
    "gp2": {"price_per_gb": 0.10, "baseline_iops": 3, "max_iops": 16000},
    "gp3": {"price_per_gb": 0.08, "baseline_iops": 3000, "max_iops": 16000},
    "io1": {"price_per_gb": 0.125, "baseline_iops": 0, "iops_price": 0.065},
    "io2": {"price_per_gb": 0.125, "baseline_iops": 0, "iops_price": 0.065},
    "st1": {"price_per_gb": 0.045, "baseline_iops": 0, "max_iops": 500},
    "sc1": {"price_per_gb": 0.015, "baseline_iops": 0, "max_iops": 250},
    "standard": {"price_per_gb": 0.05, "baseline_iops": 0, "max_iops": 200},
}


def generate_sample_ebs_data():
    """Generate sample EBS volume data."""
    volumes = [
        {"name": "prod-web-root", "type": "gp3", "size_gb": 100, "attached": True, "env": "Production"},
        {"name": "prod-web-data", "type": "gp3", "size_gb": 500, "attached": True, "env": "Production"},
        {"name": "prod-db-data", "type": "io2", "size_gb": 1000, "attached": True, "env": "Production"},
        {"name": "prod-db-logs", "type": "gp3", "size_gb": 200, "attached": True, "env": "Production"},
        {"name": "analytics-storage", "type": "st1", "size_gb": 5000, "attached": True, "env": "Production"},
        {"name": "backup-archive", "type": "sc1", "size_gb": 10000, "attached": True, "env": "Production"},
        {"name": "stage-web-root", "type": "gp2", "size_gb": 50, "attached": True, "env": "Staging"},
        {"name": "stage-db-data", "type": "gp2", "size_gb": 200, "attached": True, "env": "Staging"},
        {"name": "dev-instance-1", "type": "gp2", "size_gb": 30, "attached": True, "env": "Development"},
        {"name": "dev-instance-2", "type": "gp2", "size_gb": 30, "attached": True, "env": "Development"},
        {"name": "old-migration-vol", "type": "gp2", "size_gb": 500, "attached": False, "env": "Unknown"},
        {"name": "snapshot-restore-test", "type": "gp2", "size_gb": 100, "attached": False, "env": "Test"},
        {"name": "decom-server-data", "type": "gp2", "size_gb": 250, "attached": False, "env": "Unknown"},
        {"name": "temp-analysis", "type": "gp2", "size_gb": 1000, "attached": False, "env": "Development"},
        {"name": "legacy-app-root", "type": "standard", "size_gb": 20, "attached": True, "env": "Production"},
    ]

    data = []
    for vol in volumes:
        pricing = EBS_PRICING.get(vol["type"], EBS_PRICING["gp2"])
        monthly_cost = vol["size_gb"] * pricing["price_per_gb"]
        usage_pct = np.random.uniform(10, 85) if vol["attached"] else 0
        iops_avg = np.random.uniform(100, 3000) if vol["attached"] else 0

        data.append({
            "volume_name": vol["name"], "volume_type": vol["type"], "size_gb": vol["size_gb"],
            "attached": vol["attached"], "environment": vol["env"], "usage_pct": usage_pct,
            "iops_avg": iops_avg, "monthly_cost": monthly_cost,
            "days_since_activity": np.random.randint(0, 90) if vol["attached"] else np.random.randint(30, 365),
        })
    return pd.DataFrame(data)


if "ebs_data" not in st.session_state:
    st.session_state["ebs_data"] = generate_sample_ebs_data()

df = st.session_state["ebs_data"]

section_header("Overview")

unattached_cost = df[df["attached"] == False]["monthly_cost"].sum()

st.markdown(metrics_row([
    ("💾", len(df), "Total Volumes"),
    ("💵", f"${df['monthly_cost'].sum():,.0f}", "Monthly Spend", "orange"),
    ("⚠️", len(df[df["attached"] == False]), "Unattached", "red"),
    ("📦", f"{df['size_gb'].sum():,.0f} GB", "Total Storage"),
    ("🗑️", f"${unattached_cost:,.0f}/mo", "Wasted Cost", "red"),
]), unsafe_allow_html=True)

st.divider()

tab1, tab2, tab3, tab4 = st.tabs(["📋 Inventory", "⚠️ Unattached", "💡 Recommendations", "📈 Cost Analysis"])

with tab1:
    section_header("Volume Inventory")

    col1, col2, col3 = st.columns(3)
    with col1:
        type_filter = st.multiselect("Volume Type", list(df["volume_type"].unique()), default=list(df["volume_type"].unique()))
    with col2:
        env_filter = st.multiselect("Environment", list(df["environment"].unique()), default=list(df["environment"].unique()))
    with col3:
        attached_filter = st.selectbox("Status", ["All", "Attached", "Unattached"])

    filtered = df[(df["volume_type"].isin(type_filter)) & (df["environment"].isin(env_filter))]
    if attached_filter == "Attached":
        filtered = filtered[filtered["attached"] == True]
    elif attached_filter == "Unattached":
        filtered = filtered[filtered["attached"] == False]

    st.dataframe(filtered, column_config={
        "usage_pct": st.column_config.NumberColumn("Usage %", format="%.1f"),
        "iops_avg": st.column_config.NumberColumn("Avg IOPS", format="%.0f"),
        "monthly_cost": st.column_config.NumberColumn("Monthly Cost", format="$%.2f"),
        "attached": st.column_config.CheckboxColumn("Attached"),
    }, use_container_width=True, height=400)

with tab2:
    section_header("Unattached Volumes")

    unattached_df = df[df["attached"] == False].copy()
    if len(unattached_df) > 0:
        st.markdown(f"""
        <div class="info-box error">
            <strong>{len(unattached_df)} unattached volumes</strong> costing <strong>${unattached_df['monthly_cost'].sum():,.0f}/month</strong>
        </div>
        """, unsafe_allow_html=True)

        st.dataframe(unattached_df[["volume_name", "volume_type", "size_gb", "monthly_cost", "days_since_activity"]], column_config={
            "monthly_cost": st.column_config.NumberColumn("Monthly Cost", format="$%.2f"),
            "days_since_activity": st.column_config.NumberColumn("Days Idle"),
        }, use_container_width=True)

        st.markdown("""
        **Recommended Actions:**
        1. Verify volumes are not needed
        2. Create snapshots if data may be needed later
        3. Delete unneeded volumes to stop charges
        """)
    else:
        st.success("No unattached volumes found!")

with tab3:
    section_header("Optimization Recommendations")

    recommendations = []
    for _, row in df.iterrows():
        if row["volume_type"] == "gp2" and row["attached"]:
            gp3_cost = row["size_gb"] * EBS_PRICING["gp3"]["price_per_gb"]
            savings = row["monthly_cost"] - gp3_cost
            if savings > 0:
                recommendations.append({"volume": row["volume_name"], "issue": "gp2 → gp3 Migration", "recommendation": "Migrate to gp3 for 20% savings + better IOPS", "savings": savings, "risk": "Low"})
        if row["attached"] and row["usage_pct"] < 30:
            recommendations.append({"volume": row["volume_name"], "issue": "Low Utilization", "recommendation": f"Only {row['usage_pct']:.0f}% used - consider resizing", "savings": row["monthly_cost"] * 0.3, "risk": "Medium"})
        if row["volume_type"] == "standard":
            recommendations.append({"volume": row["volume_name"], "issue": "Legacy Type", "recommendation": "Migrate from magnetic to gp3", "savings": row["monthly_cost"] * 0.2, "risk": "Low"})

    if recommendations:
        recs_df = pd.DataFrame(recommendations)
        st.markdown(f"""
        <div class="info-box success">
            <strong>Potential Savings: ${recs_df['savings'].sum():,.0f}/month</strong>
        </div>
        """, unsafe_allow_html=True)
        st.dataframe(recs_df, column_config={"savings": st.column_config.NumberColumn("Monthly Savings", format="$%.2f")}, use_container_width=True)
    else:
        st.success("All volumes appear optimized!")

with tab4:
    section_header("Cost Analysis")

    col1, col2 = st.columns(2)
    with col1:
        by_type = df.groupby("volume_type")["monthly_cost"].sum().sort_values(ascending=False)
        fig = go.Figure(data=[go.Pie(labels=by_type.index, values=by_type.values, hole=0.5, marker_colors=['#FF9900', '#10b981', '#3b82f6', '#f59e0b', '#8b5cf6', '#64748b'])])
        fig.update_layout(height=350, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#94a3b8'))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        by_env = df.groupby("environment")["monthly_cost"].sum().sort_values(ascending=False)
        fig = px.bar(x=by_env.index, y=by_env.values, color_discrete_sequence=['#FF9900'])
        fig.update_layout(height=350, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#94a3b8'), xaxis=dict(gridcolor='rgba(255,255,255,0.05)'), yaxis=dict(gridcolor='rgba(255,255,255,0.05)', title="Monthly Cost ($)"))
        st.plotly_chart(fig, use_container_width=True)

    chart_header("Volume Size vs Cost")
    fig = px.scatter(df, x="size_gb", y="monthly_cost", color="volume_type", size="size_gb", hover_name="volume_name")
    fig.update_layout(height=400, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#94a3b8'), xaxis=dict(gridcolor='rgba(255,255,255,0.05)', title="Size (GB)"), yaxis=dict(gridcolor='rgba(255,255,255,0.05)', title="Monthly Cost ($)"))
    st.plotly_chart(fig, use_container_width=True)

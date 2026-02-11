"""RDS Database Analysis page."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from styles import inject_styles, page_header, section_header, chart_header, metrics_row

st.set_page_config(page_title="RDS Analysis", page_icon="🗄️", layout="wide")
inject_styles()

page_header("🗄️ RDS Database Analysis", "Optimize database instances, identify idle DBs, and recommend Reserved Instance coverage")

# RDS Instance Pricing (approximate hourly rates)
RDS_PRICING = {
    "db.t3.micro": {"vcpu": 2, "memory_gb": 1, "hourly": 0.017},
    "db.t3.small": {"vcpu": 2, "memory_gb": 2, "hourly": 0.034},
    "db.t3.medium": {"vcpu": 2, "memory_gb": 4, "hourly": 0.068},
    "db.t3.large": {"vcpu": 2, "memory_gb": 8, "hourly": 0.136},
    "db.m5.large": {"vcpu": 2, "memory_gb": 8, "hourly": 0.171},
    "db.m5.xlarge": {"vcpu": 4, "memory_gb": 16, "hourly": 0.342},
    "db.m5.2xlarge": {"vcpu": 8, "memory_gb": 32, "hourly": 0.684},
    "db.m5.4xlarge": {"vcpu": 16, "memory_gb": 64, "hourly": 1.368},
    "db.r5.large": {"vcpu": 2, "memory_gb": 16, "hourly": 0.24},
    "db.r5.xlarge": {"vcpu": 4, "memory_gb": 32, "hourly": 0.48},
    "db.r5.2xlarge": {"vcpu": 8, "memory_gb": 64, "hourly": 0.96},
    "db.r5.4xlarge": {"vcpu": 16, "memory_gb": 128, "hourly": 1.92},
}

RDS_GRAVITON = {
    "db.m5.large": "db.m6g.large",
    "db.m5.xlarge": "db.m6g.xlarge",
    "db.m5.2xlarge": "db.m6g.2xlarge",
    "db.r5.large": "db.r6g.large",
    "db.r5.xlarge": "db.r6g.xlarge",
    "db.r5.2xlarge": "db.r6g.2xlarge",
}


def generate_sample_rds_data():
    """Generate sample RDS data for demonstration."""
    databases = [
        {"name": "prod-mysql-primary", "engine": "MySQL", "instance_type": "db.r5.2xlarge", "multi_az": True, "storage_gb": 500, "env": "Production"},
        {"name": "prod-mysql-replica", "engine": "MySQL", "instance_type": "db.r5.xlarge", "multi_az": False, "storage_gb": 500, "env": "Production"},
        {"name": "prod-postgres", "engine": "PostgreSQL", "instance_type": "db.m5.xlarge", "multi_az": True, "storage_gb": 200, "env": "Production"},
        {"name": "analytics-db", "engine": "PostgreSQL", "instance_type": "db.r5.4xlarge", "multi_az": False, "storage_gb": 1000, "env": "Production"},
        {"name": "stage-mysql", "engine": "MySQL", "instance_type": "db.m5.large", "multi_az": False, "storage_gb": 100, "env": "Staging"},
        {"name": "stage-postgres", "engine": "PostgreSQL", "instance_type": "db.t3.medium", "multi_az": False, "storage_gb": 50, "env": "Staging"},
        {"name": "dev-mysql-1", "engine": "MySQL", "instance_type": "db.t3.large", "multi_az": False, "storage_gb": 50, "env": "Development"},
        {"name": "dev-mysql-2", "engine": "MySQL", "instance_type": "db.t3.medium", "multi_az": False, "storage_gb": 30, "env": "Development"},
        {"name": "test-postgres", "engine": "PostgreSQL", "instance_type": "db.t3.small", "multi_az": False, "storage_gb": 20, "env": "Test"},
        {"name": "legacy-oracle", "engine": "Oracle", "instance_type": "db.m5.2xlarge", "multi_az": True, "storage_gb": 300, "env": "Production"},
    ]

    data = []
    for db in databases:
        specs = RDS_PRICING.get(db["instance_type"], {"vcpu": 2, "memory_gb": 8, "hourly": 0.2})
        monthly_cost = specs["hourly"] * 730 * (2 if db["multi_az"] else 1)
        storage_cost = db["storage_gb"] * 0.115

        if db["env"] == "Development":
            cpu_avg = np.random.uniform(5, 20)
            connections_avg = np.random.uniform(1, 10)
        elif db["env"] == "Staging":
            cpu_avg = np.random.uniform(10, 35)
            connections_avg = np.random.uniform(5, 30)
        else:
            cpu_avg = np.random.uniform(20, 70)
            connections_avg = np.random.uniform(20, 200)

        data.append({
            "db_name": db["name"],
            "engine": db["engine"],
            "instance_type": db["instance_type"],
            "vcpu": specs["vcpu"],
            "memory_gb": specs["memory_gb"],
            "multi_az": db["multi_az"],
            "storage_gb": db["storage_gb"],
            "environment": db["env"],
            "cpu_avg": cpu_avg,
            "cpu_p95": cpu_avg + np.random.uniform(10, 25),
            "connections_avg": connections_avg,
            "read_iops_avg": np.random.uniform(100, 5000),
            "write_iops_avg": np.random.uniform(50, 2000),
            "monthly_compute": monthly_cost,
            "monthly_storage": storage_cost,
            "monthly_total": monthly_cost + storage_cost,
        })

    return pd.DataFrame(data)


if "rds_data" not in st.session_state:
    st.session_state["rds_data"] = generate_sample_rds_data()

df = st.session_state["rds_data"]

# Summary metrics
section_header("Overview")

st.markdown(metrics_row([
    ("🗄️", len(df), "Total Databases"),
    ("💵", f"${df['monthly_total'].sum():,.0f}", "Monthly Spend", "orange"),
    ("🔄", len(df[df["multi_az"] == True]), "Multi-AZ Enabled"),
    ("💾", f"{df['storage_gb'].sum():,.0f} GB", "Total Storage"),
    ("📊", f"{df['cpu_avg'].mean():.1f}%", "Avg CPU"),
]), unsafe_allow_html=True)

st.divider()

# Analysis tabs
tab1, tab2, tab3, tab4 = st.tabs(["📋 Inventory", "💡 Recommendations", "💰 Cost Analysis", "🚀 Graviton"])

with tab1:
    section_header("Database Inventory")

    col1, col2, col3 = st.columns(3)
    with col1:
        engine_filter = st.multiselect("Engine", list(df["engine"].unique()), default=list(df["engine"].unique()))
    with col2:
        env_filter = st.multiselect("Environment", list(df["environment"].unique()), default=list(df["environment"].unique()))
    with col3:
        min_cost = st.slider("Min Monthly Cost ($)", 0, int(df["monthly_total"].max()), 0)

    filtered = df[
        (df["engine"].isin(engine_filter)) &
        (df["environment"].isin(env_filter)) &
        (df["monthly_total"] >= min_cost)
    ]

    st.dataframe(
        filtered[["db_name", "engine", "instance_type", "multi_az", "cpu_avg", "connections_avg", "monthly_total", "environment"]],
        column_config={
            "cpu_avg": st.column_config.NumberColumn("CPU Avg %", format="%.1f"),
            "connections_avg": st.column_config.NumberColumn("Connections", format="%.0f"),
            "monthly_total": st.column_config.NumberColumn("Monthly Cost", format="$%.2f"),
            "multi_az": st.column_config.CheckboxColumn("Multi-AZ"),
        },
        use_container_width=True,
        height=400
    )

with tab2:
    section_header("Optimization Recommendations")

    recommendations = []
    for _, row in df.iterrows():
        if row["cpu_avg"] < 5 and row["connections_avg"] < 5:
            recommendations.append({
                "database": row["db_name"], "issue": "Potentially Idle",
                "recommendation": "Review usage - consider shutting down",
                "savings": row["monthly_total"] * 0.9, "risk": "Medium"
            })
        elif row["cpu_avg"] < 20 and row["cpu_p95"] < 40:
            recommendations.append({
                "database": row["db_name"], "issue": "Oversized",
                "recommendation": f"Downsize from {row['instance_type']}",
                "savings": row["monthly_compute"] * 0.4, "risk": "Low"
            })
        if row["multi_az"] and row["environment"] in ["Development", "Test", "Staging"]:
            recommendations.append({
                "database": row["db_name"], "issue": "Multi-AZ in non-prod",
                "recommendation": "Disable Multi-AZ for non-production",
                "savings": row["monthly_compute"] * 0.5, "risk": "Low"
            })

    if recommendations:
        recs_df = pd.DataFrame(recommendations)
        total_savings = recs_df["savings"].sum()

        st.markdown(f"""
        <div class="info-box success">
            <strong>Potential Savings: ${total_savings:,.0f}/month</strong>
        </div>
        """, unsafe_allow_html=True)

        st.dataframe(recs_df, column_config={"savings": st.column_config.NumberColumn("Monthly Savings", format="$%.2f")}, use_container_width=True)
    else:
        st.success("All databases appear optimized!")

with tab3:
    section_header("Cost Analysis")

    col1, col2 = st.columns(2)
    with col1:
        by_env = df.groupby("environment")["monthly_total"].sum().sort_values(ascending=False)
        fig = go.Figure(data=[go.Pie(labels=by_env.index, values=by_env.values, hole=0.5, marker_colors=['#FF9900', '#10b981', '#3b82f6', '#f59e0b'])])
        fig.update_layout(height=350, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#94a3b8'), showlegend=True)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        by_engine = df.groupby("engine")["monthly_total"].sum().sort_values(ascending=False)
        fig = px.bar(x=by_engine.index, y=by_engine.values, color_discrete_sequence=['#FF9900'])
        fig.update_layout(height=350, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#94a3b8'), xaxis=dict(gridcolor='rgba(255,255,255,0.05)'), yaxis=dict(gridcolor='rgba(255,255,255,0.05)', title="Monthly Cost ($)"))
        st.plotly_chart(fig, use_container_width=True)

    chart_header("Compute vs Storage Cost")
    fig = go.Figure(data=[
        go.Bar(name='Compute', x=df["db_name"], y=df["monthly_compute"], marker_color='#FF9900'),
        go.Bar(name='Storage', x=df["db_name"], y=df["monthly_storage"], marker_color='#10b981')
    ])
    fig.update_layout(barmode='stack', height=400, xaxis_tickangle=45, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#94a3b8'), xaxis=dict(gridcolor='rgba(255,255,255,0.05)'), yaxis=dict(gridcolor='rgba(255,255,255,0.05)'))
    st.plotly_chart(fig, use_container_width=True)

with tab4:
    section_header("Graviton Migration Opportunities")

    graviton_candidates = []
    for _, row in df.iterrows():
        if row["instance_type"] in RDS_GRAVITON:
            graviton_candidates.append({
                "database": row["db_name"], "current_type": row["instance_type"],
                "graviton_type": RDS_GRAVITON[row["instance_type"]],
                "current_cost": row["monthly_compute"],
                "estimated_savings": row["monthly_compute"] * 0.20, "engine": row["engine"]
            })

    if graviton_candidates:
        grav_df = pd.DataFrame(graviton_candidates)
        total_graviton_savings = grav_df["estimated_savings"].sum()

        st.markdown(f"""
        <div class="info-box success">
            <strong>Potential Graviton Savings: ${total_graviton_savings:,.0f}/month</strong>
        </div>
        """, unsafe_allow_html=True)

        st.dataframe(grav_df, column_config={
            "current_cost": st.column_config.NumberColumn("Current Cost", format="$%.2f"),
            "estimated_savings": st.column_config.NumberColumn("Est. Savings", format="$%.2f"),
        }, use_container_width=True)

        st.markdown("""
        **Graviton Benefits for RDS:**
        - Up to 20% cost savings
        - Up to 35% better price-performance
        - Supported by MySQL, PostgreSQL, MariaDB
        """)
    else:
        st.info("No Graviton migration candidates found.")

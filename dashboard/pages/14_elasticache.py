"""ElastiCache Analysis page."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from styles import inject_styles, page_header, section_header, chart_header, metrics_row

st.set_page_config(page_title="ElastiCache Analysis", page_icon="🗃️", layout="wide")
inject_styles()

page_header("🗃️ ElastiCache Analysis", "Optimize cache clusters, identify idle caches, and reduce in-memory data costs")

ELASTICACHE_PRICING = {
    "cache.t3.micro": {"vcpu": 2, "memory_gb": 0.5, "hourly": 0.017},
    "cache.t3.small": {"vcpu": 2, "memory_gb": 1.37, "hourly": 0.034},
    "cache.t3.medium": {"vcpu": 2, "memory_gb": 3.09, "hourly": 0.068},
    "cache.m5.large": {"vcpu": 2, "memory_gb": 6.38, "hourly": 0.124},
    "cache.m5.xlarge": {"vcpu": 4, "memory_gb": 12.93, "hourly": 0.248},
    "cache.m5.2xlarge": {"vcpu": 8, "memory_gb": 26.04, "hourly": 0.496},
    "cache.r5.large": {"vcpu": 2, "memory_gb": 13.07, "hourly": 0.166},
    "cache.r5.xlarge": {"vcpu": 4, "memory_gb": 26.32, "hourly": 0.332},
    "cache.r5.2xlarge": {"vcpu": 8, "memory_gb": 52.82, "hourly": 0.664},
    "cache.r6g.large": {"vcpu": 2, "memory_gb": 13.07, "hourly": 0.133},
    "cache.r6g.xlarge": {"vcpu": 4, "memory_gb": 26.32, "hourly": 0.266},
}

GRAVITON_MAPPING = {
    "cache.m5.large": "cache.m6g.large", "cache.m5.xlarge": "cache.m6g.xlarge",
    "cache.r5.large": "cache.r6g.large", "cache.r5.xlarge": "cache.r6g.xlarge",
    "cache.r5.2xlarge": "cache.r6g.2xlarge",
}


def generate_sample_elasticache_data():
    """Generate sample ElastiCache data."""
    clusters = [
        {"name": "prod-redis-primary", "engine": "Redis", "node_type": "cache.r5.xlarge", "nodes": 3, "env": "Production"},
        {"name": "prod-redis-sessions", "engine": "Redis", "node_type": "cache.r5.large", "nodes": 2, "env": "Production"},
        {"name": "prod-memcached", "engine": "Memcached", "node_type": "cache.m5.xlarge", "nodes": 3, "env": "Production"},
        {"name": "stage-redis", "engine": "Redis", "node_type": "cache.t3.medium", "nodes": 1, "env": "Staging"},
        {"name": "dev-redis", "engine": "Redis", "node_type": "cache.t3.small", "nodes": 1, "env": "Development"},
        {"name": "analytics-cache", "engine": "Redis", "node_type": "cache.r5.2xlarge", "nodes": 2, "env": "Production"},
        {"name": "legacy-cache", "engine": "Memcached", "node_type": "cache.m5.large", "nodes": 2, "env": "Production"},
    ]

    data = []
    for cluster in clusters:
        specs = ELASTICACHE_PRICING.get(cluster["node_type"], {"vcpu": 2, "memory_gb": 8, "hourly": 0.2})
        monthly_cost = specs["hourly"] * 730 * cluster["nodes"]

        if cluster["env"] == "Development":
            cpu_avg, memory_used_pct, connections = np.random.uniform(5, 20), np.random.uniform(10, 40), np.random.randint(5, 50)
        elif cluster["env"] == "Staging":
            cpu_avg, memory_used_pct, connections = np.random.uniform(10, 35), np.random.uniform(20, 50), np.random.randint(20, 200)
        else:
            cpu_avg, memory_used_pct, connections = np.random.uniform(15, 60), np.random.uniform(30, 85), np.random.randint(100, 2000)

        data.append({
            "cluster_name": cluster["name"], "engine": cluster["engine"], "node_type": cluster["node_type"],
            "nodes": cluster["nodes"], "vcpu": specs["vcpu"], "memory_gb": specs["memory_gb"],
            "environment": cluster["env"], "cpu_avg": cpu_avg, "memory_used_pct": memory_used_pct,
            "connections": connections, "hit_rate_pct": np.random.uniform(85, 99.5), "monthly_cost": monthly_cost,
        })
    return pd.DataFrame(data)


if "elasticache_data" not in st.session_state:
    st.session_state["elasticache_data"] = generate_sample_elasticache_data()

df = st.session_state["elasticache_data"]

section_header("Overview")

st.markdown(metrics_row([
    ("🗃️", len(df), "Total Clusters"),
    ("💵", f"${df['monthly_cost'].sum():,.0f}", "Monthly Spend", "orange"),
    ("🖥️", df["nodes"].sum(), "Total Nodes"),
    ("🔴", len(df[df["engine"] == "Redis"]), "Redis Clusters"),
    ("📊", f"{df['hit_rate_pct'].mean():.1f}%", "Avg Hit Rate", "green"),
]), unsafe_allow_html=True)

st.divider()

tab1, tab2, tab3, tab4 = st.tabs(["📋 Inventory", "💡 Recommendations", "📈 Cost Analysis", "🚀 Graviton"])

with tab1:
    section_header("Cluster Inventory")

    col1, col2, col3 = st.columns(3)
    with col1:
        engine_filter = st.multiselect("Engine", list(df["engine"].unique()), default=list(df["engine"].unique()))
    with col2:
        env_filter = st.multiselect("Environment", list(df["environment"].unique()), default=list(df["environment"].unique()))
    with col3:
        min_cost = st.slider("Min Monthly Cost ($)", 0, int(df["monthly_cost"].max()), 0)

    filtered = df[(df["engine"].isin(engine_filter)) & (df["environment"].isin(env_filter)) & (df["monthly_cost"] >= min_cost)]

    st.dataframe(filtered, column_config={
        "cpu_avg": st.column_config.NumberColumn("CPU Avg %", format="%.1f"),
        "memory_used_pct": st.column_config.NumberColumn("Memory %", format="%.1f"),
        "hit_rate_pct": st.column_config.NumberColumn("Hit Rate %", format="%.1f"),
        "monthly_cost": st.column_config.NumberColumn("Monthly Cost", format="$%.2f"),
    }, use_container_width=True, height=400)

with tab2:
    section_header("Optimization Recommendations")

    recommendations = []
    for _, row in df.iterrows():
        if row["memory_used_pct"] < 30 and row["cpu_avg"] < 20:
            recommendations.append({"cluster": row["cluster_name"], "issue": "Low Utilization", "recommendation": f"Downsize from {row['node_type']}", "savings": row["monthly_cost"] * 0.4, "risk": "Low"})
        if row["nodes"] > 2 and row["memory_used_pct"] < 40:
            recommendations.append({"cluster": row["cluster_name"], "issue": "Too Many Nodes", "recommendation": f"Reduce from {row['nodes']} nodes", "savings": row["monthly_cost"] / row["nodes"], "risk": "Medium"})
        if row["hit_rate_pct"] < 90:
            recommendations.append({"cluster": row["cluster_name"], "issue": "Low Hit Rate", "recommendation": f"Review caching strategy ({row['hit_rate_pct']:.1f}%)", "savings": 0, "risk": "Low"})
        if row["environment"] in ["Development", "Staging"] and "r5" in row["node_type"]:
            recommendations.append({"cluster": row["cluster_name"], "issue": "Oversized for Non-Prod", "recommendation": "Use t3 instances", "savings": row["monthly_cost"] * 0.6, "risk": "Low"})

    if recommendations:
        recs_df = pd.DataFrame(recommendations)
        st.markdown(f"""
        <div class="info-box success">
            <strong>Potential Savings: ${recs_df['savings'].sum():,.0f}/month</strong>
        </div>
        """, unsafe_allow_html=True)
        st.dataframe(recs_df, column_config={"savings": st.column_config.NumberColumn("Monthly Savings", format="$%.2f")}, use_container_width=True)
    else:
        st.success("All clusters appear optimized!")

with tab3:
    section_header("Cost Analysis")

    col1, col2 = st.columns(2)
    with col1:
        by_engine = df.groupby("engine")["monthly_cost"].sum()
        fig = go.Figure(data=[go.Pie(labels=by_engine.index, values=by_engine.values, hole=0.5, marker_colors=['#FF9900', '#10b981'])])
        fig.update_layout(height=350, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#94a3b8'))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        by_env = df.groupby("environment")["monthly_cost"].sum().sort_values(ascending=False)
        fig = px.bar(x=by_env.index, y=by_env.values, color_discrete_sequence=['#FF9900'])
        fig.update_layout(height=350, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#94a3b8'), xaxis=dict(gridcolor='rgba(255,255,255,0.05)'), yaxis=dict(gridcolor='rgba(255,255,255,0.05)', title="Monthly Cost ($)"))
        st.plotly_chart(fig, use_container_width=True)

    chart_header("Cluster Performance")
    fig = go.Figure(data=[
        go.Bar(name='CPU %', x=df["cluster_name"], y=df["cpu_avg"], marker_color='#FF9900'),
        go.Bar(name='Memory %', x=df["cluster_name"], y=df["memory_used_pct"], marker_color='#10b981')
    ])
    fig.update_layout(barmode='group', height=400, xaxis_tickangle=45, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#94a3b8'), xaxis=dict(gridcolor='rgba(255,255,255,0.05)'), yaxis=dict(gridcolor='rgba(255,255,255,0.05)'))
    st.plotly_chart(fig, use_container_width=True)

with tab4:
    section_header("Graviton Migration Opportunities")

    graviton_candidates = [{"cluster": row["cluster_name"], "current_type": row["node_type"], "graviton_type": GRAVITON_MAPPING[row["node_type"]], "nodes": row["nodes"], "current_cost": row["monthly_cost"], "estimated_savings": row["monthly_cost"] * 0.20, "engine": row["engine"]} for _, row in df.iterrows() if row["node_type"] in GRAVITON_MAPPING]

    if graviton_candidates:
        grav_df = pd.DataFrame(graviton_candidates)
        st.markdown(f"""
        <div class="info-box success">
            <strong>Potential Graviton Savings: ${grav_df['estimated_savings'].sum():,.0f}/month</strong>
        </div>
        """, unsafe_allow_html=True)
        st.dataframe(grav_df, column_config={"current_cost": st.column_config.NumberColumn("Current Cost", format="$%.2f"), "estimated_savings": st.column_config.NumberColumn("Est. Savings", format="$%.2f")}, use_container_width=True)
        st.markdown("**Graviton Benefits:** Up to 20% cost savings, 45% better price-performance, supported by Redis and Memcached")
    else:
        st.info("No Graviton migration candidates found.")

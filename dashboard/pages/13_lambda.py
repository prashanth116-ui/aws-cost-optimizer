"""Lambda Functions Analysis page."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from styles import inject_styles, page_header, section_header, chart_header, metrics_row

st.set_page_config(page_title="Lambda Analysis", page_icon="⚡", layout="wide")
inject_styles()

page_header("⚡ Lambda Functions Analysis", "Optimize function memory, identify unused functions, and reduce compute costs")

LAMBDA_PRICING = {
    "request_price": 0.0000002,
    "duration_price_per_gb_second": 0.0000166667,
    "arm_discount": 0.20,
}


def generate_sample_lambda_data():
    """Generate sample Lambda data."""
    functions = [
        {"name": "api-handler", "runtime": "nodejs18.x", "memory_mb": 1024, "arch": "x86_64", "env": "Production"},
        {"name": "image-processor", "runtime": "python3.11", "memory_mb": 3008, "arch": "x86_64", "env": "Production"},
        {"name": "data-transformer", "runtime": "python3.11", "memory_mb": 2048, "arch": "x86_64", "env": "Production"},
        {"name": "notification-sender", "runtime": "nodejs18.x", "memory_mb": 256, "arch": "arm64", "env": "Production"},
        {"name": "cron-cleanup", "runtime": "python3.9", "memory_mb": 512, "arch": "x86_64", "env": "Production"},
        {"name": "auth-validator", "runtime": "nodejs18.x", "memory_mb": 512, "arch": "x86_64", "env": "Production"},
        {"name": "report-generator", "runtime": "python3.11", "memory_mb": 4096, "arch": "x86_64", "env": "Production"},
        {"name": "webhook-receiver", "runtime": "go1.x", "memory_mb": 128, "arch": "arm64", "env": "Production"},
        {"name": "stage-api-handler", "runtime": "nodejs18.x", "memory_mb": 1024, "arch": "x86_64", "env": "Staging"},
        {"name": "dev-test-function", "runtime": "python3.11", "memory_mb": 256, "arch": "x86_64", "env": "Development"},
        {"name": "old-legacy-handler", "runtime": "nodejs14.x", "memory_mb": 512, "arch": "x86_64", "env": "Production"},
        {"name": "unused-experiment", "runtime": "python3.9", "memory_mb": 1024, "arch": "x86_64", "env": "Development"},
    ]

    data = []
    for func in functions:
        if "unused" in func["name"] or "legacy" in func["name"]:
            invocations_day = np.random.randint(0, 10)
            avg_duration_ms = np.random.uniform(50, 500)
        elif func["env"] == "Production":
            invocations_day = np.random.randint(1000, 100000)
            avg_duration_ms = np.random.uniform(50, 2000)
        else:
            invocations_day = np.random.randint(10, 1000)
            avg_duration_ms = np.random.uniform(100, 1000)

        monthly_invocations = invocations_day * 30
        gb_seconds = (func["memory_mb"] / 1024) * (avg_duration_ms / 1000) * monthly_invocations
        request_cost = monthly_invocations * LAMBDA_PRICING["request_price"]
        duration_cost = gb_seconds * LAMBDA_PRICING["duration_price_per_gb_second"]
        if func["arch"] == "arm64":
            duration_cost = duration_cost * (1 - LAMBDA_PRICING["arm_discount"])
        monthly_cost = request_cost + duration_cost
        memory_used_pct = np.random.uniform(20, 95) if invocations_day > 100 else np.random.uniform(10, 50)

        data.append({
            "function_name": func["name"], "runtime": func["runtime"], "memory_mb": func["memory_mb"],
            "architecture": func["arch"], "environment": func["env"], "invocations_day": invocations_day,
            "avg_duration_ms": avg_duration_ms, "memory_used_pct": memory_used_pct,
            "monthly_cost": monthly_cost, "last_invoked_days": np.random.randint(0, 90),
        })
    return pd.DataFrame(data)


if "lambda_data" not in st.session_state:
    st.session_state["lambda_data"] = generate_sample_lambda_data()

df = st.session_state["lambda_data"]

section_header("Overview")

st.markdown(metrics_row([
    ("⚡", len(df), "Total Functions"),
    ("💵", f"${df['monthly_cost'].sum():,.2f}", "Monthly Spend", "orange"),
    ("🦾", len(df[df["architecture"] == "arm64"]), "ARM Functions", "green"),
    ("📊", f"{df['invocations_day'].sum() * 30 / 1e6:.1f}M", "Monthly Invocations"),
    ("💤", len(df[df["invocations_day"] < 10]), "Low-Use Functions", "red"),
]), unsafe_allow_html=True)

st.divider()

tab1, tab2, tab3, tab4 = st.tabs(["📋 Inventory", "💡 Recommendations", "📈 Cost Analysis", "🚀 ARM Migration"])

with tab1:
    section_header("Function Inventory")

    col1, col2, col3 = st.columns(3)
    with col1:
        runtime_filter = st.multiselect("Runtime", list(df["runtime"].unique()), default=list(df["runtime"].unique()))
    with col2:
        env_filter = st.multiselect("Environment", list(df["environment"].unique()), default=list(df["environment"].unique()))
    with col3:
        arch_filter = st.multiselect("Architecture", list(df["architecture"].unique()), default=list(df["architecture"].unique()))

    filtered = df[(df["runtime"].isin(runtime_filter)) & (df["environment"].isin(env_filter)) & (df["architecture"].isin(arch_filter))]

    st.dataframe(filtered, column_config={
        "invocations_day": st.column_config.NumberColumn("Daily Invocations", format="%d"),
        "avg_duration_ms": st.column_config.NumberColumn("Avg Duration (ms)", format="%.1f"),
        "memory_used_pct": st.column_config.NumberColumn("Memory Used %", format="%.1f"),
        "monthly_cost": st.column_config.NumberColumn("Monthly Cost", format="$%.4f"),
    }, use_container_width=True, height=400)

with tab2:
    section_header("Optimization Recommendations")

    recommendations = []
    for _, row in df.iterrows():
        if row["invocations_day"] < 10 and row["last_invoked_days"] > 30:
            recommendations.append({"function": row["function_name"], "issue": "Unused/Rarely Used", "recommendation": "Consider deleting or archiving", "savings": row["monthly_cost"], "risk": "Medium"})
        if row["memory_used_pct"] < 40 and row["invocations_day"] > 100:
            optimal_memory = max(128, int(row["memory_mb"] * (row["memory_used_pct"] / 100) * 1.5))
            savings = row["monthly_cost"] * ((row["memory_mb"] - optimal_memory) / row["memory_mb"]) * 0.5
            if savings > 0.01:
                recommendations.append({"function": row["function_name"], "issue": "Over-Provisioned Memory", "recommendation": f"Reduce from {row['memory_mb']}MB to ~{optimal_memory}MB", "savings": savings, "risk": "Low"})
        if row["runtime"] in ["nodejs14.x", "python3.7", "python3.8"]:
            recommendations.append({"function": row["function_name"], "issue": "Deprecated Runtime", "recommendation": f"Upgrade {row['runtime']} to latest version", "savings": 0, "risk": "Medium"})

    if recommendations:
        recs_df = pd.DataFrame(recommendations)
        st.markdown(f"""
        <div class="info-box success">
            <strong>Potential Savings: ${recs_df['savings'].sum():,.2f}/month</strong>
        </div>
        """, unsafe_allow_html=True)
        st.dataframe(recs_df, column_config={"savings": st.column_config.NumberColumn("Monthly Savings", format="$%.4f")}, use_container_width=True)
    else:
        st.success("All functions appear optimized!")

with tab3:
    section_header("Cost Analysis")

    col1, col2 = st.columns(2)
    with col1:
        by_runtime = df.groupby("runtime")["monthly_cost"].sum().sort_values(ascending=False)
        fig = go.Figure(data=[go.Pie(labels=by_runtime.index, values=by_runtime.values, hole=0.5, marker_colors=['#FF9900', '#10b981', '#3b82f6', '#f59e0b', '#8b5cf6'])])
        fig.update_layout(height=350, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#94a3b8'))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        by_env = df.groupby("environment")["monthly_cost"].sum().sort_values(ascending=False)
        fig = px.bar(x=by_env.index, y=by_env.values, color_discrete_sequence=['#FF9900'])
        fig.update_layout(height=350, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#94a3b8'), xaxis=dict(gridcolor='rgba(255,255,255,0.05)'), yaxis=dict(gridcolor='rgba(255,255,255,0.05)', title="Monthly Cost ($)"))
        st.plotly_chart(fig, use_container_width=True)

    chart_header("Invocations vs Cost")
    fig = px.scatter(df, x="invocations_day", y="monthly_cost", color="runtime", size="memory_mb", hover_name="function_name", log_x=True)
    fig.update_layout(height=400, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#94a3b8'), xaxis=dict(gridcolor='rgba(255,255,255,0.05)', title="Daily Invocations (log)"), yaxis=dict(gridcolor='rgba(255,255,255,0.05)', title="Monthly Cost ($)"))
    st.plotly_chart(fig, use_container_width=True)

with tab4:
    section_header("ARM (Graviton2) Migration Opportunities")

    arm_candidates = df[df["architecture"] == "x86_64"].copy()
    if len(arm_candidates) > 0:
        arm_candidates["arm_savings"] = arm_candidates["monthly_cost"] * LAMBDA_PRICING["arm_discount"]
        total_arm_savings = arm_candidates["arm_savings"].sum()

        st.markdown(f"""
        <div class="info-box success">
            <strong>Potential ARM Migration Savings: ${total_arm_savings:,.2f}/month</strong>
        </div>
        """, unsafe_allow_html=True)

        arm_compatible = ["nodejs18.x", "python3.11", "python3.9", "go1.x"]
        compatible = arm_candidates[arm_candidates["runtime"].isin(arm_compatible)]

        chart_header("Compatible Functions (Ready to Migrate)")
        if len(compatible) > 0:
            st.dataframe(compatible[["function_name", "runtime", "memory_mb", "monthly_cost", "arm_savings"]], column_config={
                "monthly_cost": st.column_config.NumberColumn("Current Cost", format="$%.4f"),
                "arm_savings": st.column_config.NumberColumn("Est. Savings", format="$%.4f"),
            }, use_container_width=True)
        else:
            st.info("No compatible functions found.")

        st.markdown("""
        **ARM/Graviton2 Benefits:**
        - Up to 20% cost savings
        - Up to 34% better price-performance
        - Supported by Node.js, Python, Go, Java, Ruby, .NET
        """)
    else:
        st.success("All functions are already on ARM architecture!")

"""S3 Buckets Analysis page."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from styles import inject_styles, page_header, section_header, chart_header, metrics_row

st.set_page_config(page_title="S3 Analysis", page_icon="🪣", layout="wide")
inject_styles()

page_header("🪣 S3 Storage Analysis", "Optimize storage classes, identify unused buckets, and implement lifecycle policies")

S3_PRICING = {
    "STANDARD": {"storage": 0.023, "retrieval": 0.0, "min_days": 0},
    "INTELLIGENT_TIERING": {"storage": 0.023, "retrieval": 0.0, "min_days": 0},
    "STANDARD_IA": {"storage": 0.0125, "retrieval": 0.01, "min_days": 30},
    "ONEZONE_IA": {"storage": 0.01, "retrieval": 0.01, "min_days": 30},
    "GLACIER_IR": {"storage": 0.004, "retrieval": 0.03, "min_days": 90},
    "GLACIER_FLEXIBLE": {"storage": 0.0036, "retrieval": 0.03, "min_days": 90},
    "GLACIER_DEEP": {"storage": 0.00099, "retrieval": 0.02, "min_days": 180},
}


def generate_sample_s3_data():
    """Generate sample S3 data."""
    buckets = [
        {"name": "prod-app-assets", "class": "STANDARD", "size_gb": 500, "env": "Production", "purpose": "Application"},
        {"name": "prod-user-uploads", "class": "STANDARD", "size_gb": 2000, "env": "Production", "purpose": "User Data"},
        {"name": "prod-logs", "class": "STANDARD", "size_gb": 5000, "env": "Production", "purpose": "Logs"},
        {"name": "data-lake-raw", "class": "STANDARD", "size_gb": 50000, "env": "Production", "purpose": "Analytics"},
        {"name": "data-lake-processed", "class": "STANDARD_IA", "size_gb": 20000, "env": "Production", "purpose": "Analytics"},
        {"name": "backups-weekly", "class": "GLACIER_FLEXIBLE", "size_gb": 100000, "env": "Production", "purpose": "Backups"},
        {"name": "backups-monthly", "class": "GLACIER_DEEP", "size_gb": 500000, "env": "Production", "purpose": "Backups"},
        {"name": "staging-assets", "class": "STANDARD", "size_gb": 100, "env": "Staging", "purpose": "Application"},
        {"name": "dev-test-data", "class": "STANDARD", "size_gb": 50, "env": "Development", "purpose": "Test Data"},
        {"name": "old-migration-data", "class": "STANDARD", "size_gb": 10000, "env": "Unknown", "purpose": "Migration"},
        {"name": "temp-analytics", "class": "STANDARD", "size_gb": 1000, "env": "Development", "purpose": "Analytics"},
        {"name": "compliance-archive", "class": "GLACIER_DEEP", "size_gb": 200000, "env": "Production", "purpose": "Compliance"},
    ]

    data = []
    for bucket in buckets:
        pricing = S3_PRICING.get(bucket["class"], S3_PRICING["STANDARD"])
        monthly_cost = bucket["size_gb"] * pricing["storage"]

        if bucket["class"] in ["GLACIER_FLEXIBLE", "GLACIER_DEEP"]:
            access_frequency, last_accessed_days = "Rare", np.random.randint(30, 365)
        elif bucket["class"] in ["STANDARD_IA", "ONEZONE_IA"]:
            access_frequency, last_accessed_days = "Infrequent", np.random.randint(7, 60)
        else:
            access_frequency = "Infrequent" if "logs" in bucket["name"] or "old" in bucket["name"] else "Frequent"
            last_accessed_days = np.random.randint(14, 90) if access_frequency == "Infrequent" else np.random.randint(0, 7)

        data.append({
            "bucket_name": bucket["name"], "storage_class": bucket["class"], "size_gb": bucket["size_gb"],
            "size_tb": bucket["size_gb"] / 1024, "objects_count": int(bucket["size_gb"] * np.random.uniform(100, 10000)),
            "environment": bucket["env"], "purpose": bucket["purpose"], "access_frequency": access_frequency,
            "last_accessed_days": last_accessed_days, "has_lifecycle_policy": np.random.choice([True, False], p=[0.3, 0.7]),
            "monthly_cost": monthly_cost,
        })
    return pd.DataFrame(data)


if "s3_data" not in st.session_state:
    st.session_state["s3_data"] = generate_sample_s3_data()

df = st.session_state["s3_data"]

section_header("Overview")

st.markdown(metrics_row([
    ("🪣", len(df), "Total Buckets"),
    ("💵", f"${df['monthly_cost'].sum():,.0f}", "Monthly Spend", "orange"),
    ("💾", f"{df['size_tb'].sum():,.1f} TB", "Total Storage"),
    ("📦", f"{len(df[df['storage_class'] == 'STANDARD']) / len(df) * 100:.0f}%", "In Standard"),
    ("⚠️", len(df[df["has_lifecycle_policy"] == False]), "No Lifecycle", "red"),
]), unsafe_allow_html=True)

st.divider()

tab1, tab2, tab3, tab4 = st.tabs(["📋 Inventory", "💡 Storage Class Optimization", "📈 Cost Analysis", "🔄 Lifecycle Recommendations"])

with tab1:
    section_header("Bucket Inventory")

    col1, col2, col3 = st.columns(3)
    with col1:
        class_filter = st.multiselect("Storage Class", list(df["storage_class"].unique()), default=list(df["storage_class"].unique()))
    with col2:
        env_filter = st.multiselect("Environment", list(df["environment"].unique()), default=list(df["environment"].unique()))
    with col3:
        purpose_filter = st.multiselect("Purpose", list(df["purpose"].unique()), default=list(df["purpose"].unique()))

    filtered = df[(df["storage_class"].isin(class_filter)) & (df["environment"].isin(env_filter)) & (df["purpose"].isin(purpose_filter))]

    st.dataframe(filtered[["bucket_name", "storage_class", "size_tb", "objects_count", "environment", "access_frequency", "has_lifecycle_policy", "monthly_cost"]], column_config={
        "size_tb": st.column_config.NumberColumn("Size (TB)", format="%.2f"),
        "objects_count": st.column_config.NumberColumn("Objects", format="%d"),
        "monthly_cost": st.column_config.NumberColumn("Monthly Cost", format="$%.2f"),
        "has_lifecycle_policy": st.column_config.CheckboxColumn("Lifecycle"),
    }, use_container_width=True, height=400)

with tab2:
    section_header("Storage Class Optimization")

    recommendations = []
    for _, row in df.iterrows():
        if row["storage_class"] == "STANDARD":
            if row["access_frequency"] == "Infrequent" or row["last_accessed_days"] > 30:
                savings = row["monthly_cost"] - row["size_gb"] * S3_PRICING["STANDARD_IA"]["storage"]
                recommendations.append({"bucket": row["bucket_name"], "current_class": row["storage_class"], "recommended_class": "STANDARD_IA", "reason": f"Infrequent access ({row['last_accessed_days']} days)", "monthly_savings": savings, "risk": "Low"})
            if row["size_gb"] > 1000:
                recommendations.append({"bucket": row["bucket_name"], "current_class": row["storage_class"], "recommended_class": "INTELLIGENT_TIERING", "reason": "Large bucket - automatic optimization", "monthly_savings": row["monthly_cost"] * 0.15, "risk": "Low"})

    if recommendations:
        recs_df = pd.DataFrame(recommendations)
        st.markdown(f"""
        <div class="info-box success">
            <strong>Potential Savings: ${recs_df['monthly_savings'].sum():,.0f}/month</strong>
        </div>
        """, unsafe_allow_html=True)
        st.dataframe(recs_df, column_config={"monthly_savings": st.column_config.NumberColumn("Monthly Savings", format="$%.2f")}, use_container_width=True)
        st.markdown("**Storage Classes (most to least expensive):** STANDARD → INTELLIGENT_TIERING → STANDARD_IA → GLACIER_IR → GLACIER_FLEXIBLE → GLACIER_DEEP")
    else:
        st.success("All buckets using optimal storage classes!")

with tab3:
    section_header("Cost Analysis")

    col1, col2 = st.columns(2)
    with col1:
        by_class = df.groupby("storage_class")["monthly_cost"].sum().sort_values(ascending=False)
        fig = go.Figure(data=[go.Pie(labels=by_class.index, values=by_class.values, hole=0.5, marker_colors=['#FF9900', '#10b981', '#3b82f6', '#f59e0b', '#8b5cf6', '#64748b', '#ef4444'])])
        fig.update_layout(height=350, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#94a3b8'))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        by_purpose = df.groupby("purpose")["monthly_cost"].sum().sort_values(ascending=False)
        fig = px.bar(x=by_purpose.index, y=by_purpose.values, color_discrete_sequence=['#FF9900'])
        fig.update_layout(height=350, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#94a3b8'), xaxis=dict(gridcolor='rgba(255,255,255,0.05)'), yaxis=dict(gridcolor='rgba(255,255,255,0.05)', title="Monthly Cost ($)"))
        st.plotly_chart(fig, use_container_width=True)

    chart_header("Top Buckets by Cost")
    top_buckets = df.nlargest(10, "monthly_cost")
    fig = px.bar(top_buckets, x="bucket_name", y="monthly_cost", color="storage_class", color_discrete_sequence=['#FF9900', '#10b981', '#3b82f6', '#f59e0b'])
    fig.update_layout(height=400, xaxis_tickangle=45, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#94a3b8'), xaxis=dict(gridcolor='rgba(255,255,255,0.05)'), yaxis=dict(gridcolor='rgba(255,255,255,0.05)', title="Monthly Cost ($)"))
    st.plotly_chart(fig, use_container_width=True)

with tab4:
    section_header("Lifecycle Policy Recommendations")

    no_lifecycle = df[df["has_lifecycle_policy"] == False].copy()
    if len(no_lifecycle) > 0:
        st.markdown(f"""
        <div class="info-box warning">
            <strong>{len(no_lifecycle)} buckets</strong> have no lifecycle policy configured
        </div>
        """, unsafe_allow_html=True)

        lifecycle_recs = []
        for _, row in no_lifecycle.iterrows():
            if row["purpose"] == "Logs":
                lifecycle_recs.append({"bucket": row["bucket_name"], "recommendation": "IA after 30d, Glacier after 90d, delete after 365d", "estimated_savings": row["monthly_cost"] * 0.6})
            elif row["purpose"] == "Backups":
                lifecycle_recs.append({"bucket": row["bucket_name"], "recommendation": "Glacier after 7d, Deep Archive after 90d", "estimated_savings": row["monthly_cost"] * 0.7})
            else:
                lifecycle_recs.append({"bucket": row["bucket_name"], "recommendation": "Review access patterns and implement lifecycle rules", "estimated_savings": row["monthly_cost"] * 0.2})

        lifecycle_df = pd.DataFrame(lifecycle_recs)
        st.markdown(f"""
        <div class="info-box success">
            <strong>Potential Lifecycle Savings: ${lifecycle_df['estimated_savings'].sum():,.0f}/month</strong>
        </div>
        """, unsafe_allow_html=True)
        st.dataframe(lifecycle_df, column_config={"estimated_savings": st.column_config.NumberColumn("Est. Savings", format="$%.2f")}, use_container_width=True)
    else:
        st.success("All buckets have lifecycle policies!")

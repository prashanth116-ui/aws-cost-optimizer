"""Cost Anomaly Detection page."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from styles import inject_styles, page_header, section_header, chart_header, metrics_row

st.set_page_config(page_title="Cost Anomalies", page_icon="⚠️", layout="wide")
inject_styles()

page_header("⚠️ Cost Anomaly Detection", "Detect unusual spending patterns across AWS services")


def simulate_anomaly_data():
    """Generate sample anomaly data for demonstration."""
    from datetime import timezone

    now = datetime.now(timezone.utc)

    baselines = {
        "Amazon EC2": {"mean": 1250.50, "std_dev": 125.00, "p95": 1475.00, "min_cost": 1050.00, "max_cost": 1550.00},
        "Amazon RDS": {"mean": 650.25, "std_dev": 45.00, "p95": 740.00, "min_cost": 580.00, "max_cost": 760.00},
        "AWS Lambda": {"mean": 85.00, "std_dev": 12.50, "p95": 110.00, "min_cost": 60.00, "max_cost": 125.00},
    }

    anomalies = [
        {"service": "Amazon EC2", "date": (now - timedelta(days=1)).strftime("%Y-%m-%d"), "actual": 1875.50, "expected": 1250.50, "deviation": 50.0, "severity": "critical", "type": "spike"},
        {"service": "Amazon RDS", "date": (now - timedelta(days=2)).strftime("%Y-%m-%d"), "actual": 785.00, "expected": 650.25, "deviation": 20.7, "severity": "warning", "type": "spike"},
        {"service": "AWS Lambda", "date": (now - timedelta(days=3)).strftime("%Y-%m-%d"), "actual": 45.00, "expected": 85.00, "deviation": -47.1, "severity": "warning", "type": "drop"},
    ]

    return {"anomalies": anomalies, "baselines": baselines, "total": 3, "critical": 1, "warning": 2, "excess": 759.75}


data = simulate_anomaly_data()

# Summary metrics
section_header("Anomaly Summary")

st.markdown(metrics_row([
    ("🔍", data["total"], "Total Anomalies"),
    ("🚨", data["critical"], "Critical", "red"),
    ("⚠️", data["warning"], "Warnings", "orange"),
    ("💸", f"${data['excess']:,.0f}", "Excess Cost", "red"),
]), unsafe_allow_html=True)

st.divider()

# Detected Anomalies
section_header("Detected Anomalies")

df = pd.DataFrame(data["anomalies"])

st.dataframe(
    df,
    use_container_width=True,
    height=250,
    column_config={
        "service": st.column_config.TextColumn("Service"),
        "date": st.column_config.TextColumn("Date"),
        "actual": st.column_config.NumberColumn("Actual Cost", format="$%.2f"),
        "expected": st.column_config.NumberColumn("Expected", format="$%.2f"),
        "deviation": st.column_config.NumberColumn("Deviation %", format="%.1f%%"),
        "severity": st.column_config.TextColumn("Severity"),
        "type": st.column_config.TextColumn("Type"),
    }
)

st.divider()

# Deviation Chart
section_header("Cost Deviation by Service")

fig = go.Figure()

for anomaly in data["anomalies"]:
    color = "#ef4444" if anomaly["severity"] == "critical" else "#f59e0b"
    deviation = anomaly["actual"] - anomaly["expected"]

    fig.add_trace(go.Bar(
        x=[anomaly["service"]],
        y=[deviation],
        name=anomaly["date"],
        marker_color=color,
        text=f"${deviation:+,.0f}",
        textposition="outside",
    ))

fig.update_layout(
    height=350,
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(color='#94a3b8'),
    xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
    yaxis=dict(gridcolor='rgba(255,255,255,0.05)', title="Deviation ($)"),
    showlegend=True
)

st.plotly_chart(fig, use_container_width=True)

st.divider()

# Service Baselines
section_header("Service Baselines")

baseline_df = pd.DataFrame([
    {"Service": k, "Mean": v["mean"], "Std Dev": v["std_dev"], "P95": v["p95"], "Min": v["min_cost"], "Max": v["max_cost"]}
    for k, v in data["baselines"].items()
])

st.dataframe(
    baseline_df,
    use_container_width=True,
    column_config={
        "Mean": st.column_config.NumberColumn("Mean", format="$%.2f"),
        "Std Dev": st.column_config.NumberColumn("Std Dev", format="$%.2f"),
        "P95": st.column_config.NumberColumn("P95", format="$%.2f"),
        "Min": st.column_config.NumberColumn("Min", format="$%.2f"),
        "Max": st.column_config.NumberColumn("Max", format="$%.2f"),
    }
)

st.divider()

# Configuration
section_header("Detection Settings")

with st.expander("⚙️ Threshold Configuration"):
    st.markdown("""
    | Level | Std Deviations | Percentage |
    |-------|----------------|------------|
    | Warning | 2.0 | 30% |
    | Critical | 3.0 | 50% |

    Modify thresholds in `config/config.yaml`
    """)

# Export
if st.button("📥 Export Anomalies CSV"):
    csv = df.to_csv(index=False)
    st.download_button(
        label="Download",
        data=csv,
        file_name=f"anomalies_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

"""Cost Anomaly Detection page."""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="Cost Anomalies", page_icon="!", layout="wide")

st.title("Cost Anomaly Detection")
st.markdown("Detect unusual spending patterns across AWS services.")


def load_anomaly_data():
    """Load anomaly data from session state."""
    if "anomaly_summary" in st.session_state:
        return st.session_state["anomaly_summary"]
    return None


def simulate_anomaly_data():
    """Generate sample anomaly data for demonstration."""
    from datetime import timezone
    import numpy as np

    now = datetime.now(timezone.utc)

    # Sample baselines
    baselines = {
        "Amazon Elastic Compute Cloud - Compute": {
            "service": "Amazon Elastic Compute Cloud - Compute",
            "mean": 1250.50,
            "std_dev": 125.00,
            "median": 1225.00,
            "p50": 1225.00,
            "p75": 1350.00,
            "p90": 1425.00,
            "p95": 1475.00,
            "min_cost": 1050.00,
            "max_cost": 1550.00,
            "data_points": 30,
        },
        "Amazon Relational Database Service": {
            "service": "Amazon Relational Database Service",
            "mean": 650.25,
            "std_dev": 45.00,
            "median": 645.00,
            "p50": 645.00,
            "p75": 685.00,
            "p90": 720.00,
            "p95": 740.00,
            "min_cost": 580.00,
            "max_cost": 760.00,
            "data_points": 30,
        },
        "AWS Lambda": {
            "service": "AWS Lambda",
            "mean": 85.00,
            "std_dev": 12.50,
            "median": 82.00,
            "p50": 82.00,
            "p75": 95.00,
            "p90": 105.00,
            "p95": 110.00,
            "min_cost": 60.00,
            "max_cost": 125.00,
            "data_points": 30,
        },
    }

    # Sample anomalies
    anomalies = [
        {
            "service": "Amazon Elastic Compute Cloud - Compute",
            "anomaly_date": (now - timedelta(days=1)).isoformat(),
            "actual_cost": 1875.50,
            "expected_cost": 1250.50,
            "deviation_amount": 625.00,
            "deviation_percent": 50.0,
            "std_dev_from_mean": 5.0,
            "severity": "critical",
            "anomaly_type": "spike",
        },
        {
            "service": "Amazon Relational Database Service",
            "anomaly_date": (now - timedelta(days=2)).isoformat(),
            "actual_cost": 785.00,
            "expected_cost": 650.25,
            "deviation_amount": 134.75,
            "deviation_percent": 20.7,
            "std_dev_from_mean": 3.0,
            "severity": "warning",
            "anomaly_type": "spike",
        },
        {
            "service": "AWS Lambda",
            "anomaly_date": (now - timedelta(days=3)).isoformat(),
            "actual_cost": 45.00,
            "expected_cost": 85.00,
            "deviation_amount": -40.00,
            "deviation_percent": -47.1,
            "std_dev_from_mean": -3.2,
            "severity": "warning",
            "anomaly_type": "drop",
        },
    ]

    return {
        "total_anomalies": 3,
        "critical_count": 1,
        "warning_count": 2,
        "spike_count": 2,
        "drop_count": 1,
        "total_excess_cost": 759.75,
        "services_affected": ["Amazon Elastic Compute Cloud - Compute", "Amazon Relational Database Service", "AWS Lambda"],
        "anomalies": anomalies,
        "baselines": baselines,
        "detection_period_start": (now - timedelta(days=7)).isoformat(),
        "detection_period_end": now.isoformat(),
    }


# Load or simulate data
data = load_anomaly_data()

if data is None:
    st.info("No anomaly data loaded. Showing sample data for demonstration.")
    data = simulate_anomaly_data()

# Summary metrics
st.header("Anomaly Summary")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total Anomalies",
        data["total_anomalies"],
        delta=None,
        delta_color="inverse"
    )

with col2:
    st.metric(
        "Critical",
        data["critical_count"],
        delta=None,
        delta_color="inverse"
    )

with col3:
    st.metric(
        "Warnings",
        data["warning_count"],
        delta=None,
        delta_color="normal"
    )

with col4:
    excess = data.get("total_excess_cost", 0)
    st.metric(
        "Excess Cost",
        f"${excess:,.2f}",
        delta=None
    )

# Detection period
st.caption(
    f"Detection period: {data.get('detection_period_start', 'N/A')[:10]} to "
    f"{data.get('detection_period_end', 'N/A')[:10]}"
)

st.divider()

# Sidebar filters
st.sidebar.header("Filters")

severity_filter = st.sidebar.multiselect(
    "Severity",
    options=["critical", "warning"],
    default=["critical", "warning"]
)

type_filter = st.sidebar.multiselect(
    "Anomaly Type",
    options=["spike", "drop"],
    default=["spike", "drop"]
)

# Filter anomalies
anomalies = data.get("anomalies", [])
filtered_anomalies = [
    a for a in anomalies
    if a["severity"] in severity_filter and a["anomaly_type"] in type_filter
]

# Anomalies table
st.header("Detected Anomalies")

if filtered_anomalies:
    # Convert to DataFrame
    df = pd.DataFrame(filtered_anomalies)

    # Format columns
    df["anomaly_date"] = pd.to_datetime(df["anomaly_date"]).dt.strftime("%Y-%m-%d")

    # Display table
    st.dataframe(
        df[[
            "service", "anomaly_date", "severity", "anomaly_type",
            "actual_cost", "expected_cost", "deviation_percent"
        ]],
        use_container_width=True,
        height=300,
        column_config={
            "service": st.column_config.TextColumn("Service", width="medium"),
            "anomaly_date": st.column_config.TextColumn("Date", width="small"),
            "severity": st.column_config.TextColumn("Severity", width="small"),
            "anomaly_type": st.column_config.TextColumn("Type", width="small"),
            "actual_cost": st.column_config.NumberColumn("Actual Cost", format="$%.2f"),
            "expected_cost": st.column_config.NumberColumn("Expected", format="$%.2f"),
            "deviation_percent": st.column_config.NumberColumn("Deviation %", format="%.1f%%"),
        }
    )

    # Deviation chart
    st.subheader("Cost Deviation by Service")

    fig = go.Figure()

    for anomaly in filtered_anomalies:
        color = "red" if anomaly["severity"] == "critical" else "orange"
        fig.add_trace(go.Bar(
            x=[anomaly["service"].split(" - ")[0][:20]],
            y=[anomaly["deviation_amount"]],
            name=f"{anomaly['anomaly_date'][:10]}",
            marker_color=color,
            text=f"${anomaly['deviation_amount']:.0f}",
            textposition="outside",
        ))

    fig.update_layout(
        title="Cost Deviation Amount",
        xaxis_title="Service",
        yaxis_title="Deviation ($)",
        showlegend=True,
        height=400,
    )

    st.plotly_chart(fig, use_container_width=True)

else:
    st.success("No anomalies detected matching the selected filters.")

st.divider()

# Service Baselines
st.header("Service Baselines")

baselines = data.get("baselines", {})

if baselines:
    baseline_df = pd.DataFrame([
        {
            "Service": service[:40],
            "Mean": b["mean"],
            "Std Dev": b["std_dev"],
            "P50": b["p50"],
            "P95": b["p95"],
            "Min": b["min_cost"],
            "Max": b["max_cost"],
            "Data Points": b["data_points"],
        }
        for service, b in baselines.items()
    ])

    st.dataframe(
        baseline_df,
        use_container_width=True,
        column_config={
            "Mean": st.column_config.NumberColumn("Mean", format="$%.2f"),
            "Std Dev": st.column_config.NumberColumn("Std Dev", format="$%.2f"),
            "P50": st.column_config.NumberColumn("P50", format="$%.2f"),
            "P95": st.column_config.NumberColumn("P95", format="$%.2f"),
            "Min": st.column_config.NumberColumn("Min", format="$%.2f"),
            "Max": st.column_config.NumberColumn("Max", format="$%.2f"),
        }
    )

    # Baseline visualization
    st.subheader("Baseline Ranges")

    fig = go.Figure()

    for service, b in baselines.items():
        short_name = service.split(" - ")[0][:25]

        # Add range (min to max)
        fig.add_trace(go.Scatter(
            x=[short_name, short_name],
            y=[b["min_cost"], b["max_cost"]],
            mode="lines",
            line=dict(color="lightgray", width=10),
            showlegend=False,
            hoverinfo="skip",
        ))

        # Add mean point
        fig.add_trace(go.Scatter(
            x=[short_name],
            y=[b["mean"]],
            mode="markers",
            marker=dict(color="blue", size=12, symbol="diamond"),
            name=f"{short_name} Mean",
            hovertemplate=f"Mean: ${b['mean']:.2f}<extra></extra>",
        ))

        # Add P95 point
        fig.add_trace(go.Scatter(
            x=[short_name],
            y=[b["p95"]],
            mode="markers",
            marker=dict(color="orange", size=10, symbol="triangle-up"),
            name=f"{short_name} P95",
            hovertemplate=f"P95: ${b['p95']:.2f}<extra></extra>",
        ))

    fig.update_layout(
        title="Cost Baselines by Service",
        xaxis_title="Service",
        yaxis_title="Daily Cost ($)",
        showlegend=False,
        height=400,
    )

    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("No baseline data available.")

st.divider()

# Configuration section
st.header("Detection Configuration")

with st.expander("Threshold Settings", expanded=False):
    st.markdown("""
    **Current Thresholds:**

    | Level | Std Deviations | Percentage |
    |-------|----------------|------------|
    | Warning | 2.0 | 30% |
    | Critical | 3.0 | 50% |

    To modify thresholds, update `config/config.yaml`:

    ```yaml
    anomaly_detection:
      enabled: true
      baseline_days: 30
      thresholds:
        warning:
          std_dev: 2.0
          percentage: 30
        critical:
          std_dev: 3.0
          percentage: 50
    ```
    """)

# Export section
st.header("Export")

if filtered_anomalies:
    csv = pd.DataFrame(filtered_anomalies).to_csv(index=False)
    st.download_button(
        label="Download Anomalies CSV",
        data=csv,
        file_name=f"cost_anomalies_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

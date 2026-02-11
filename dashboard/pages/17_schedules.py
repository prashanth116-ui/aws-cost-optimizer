"""Schedule Management page."""
import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Schedules", page_icon="", layout="wide")

st.title("Report Schedules")
st.markdown("Manage automated report generation and notifications.")


def load_schedules():
    """Load schedules from session state or config."""
    if "schedules" in st.session_state:
        return st.session_state["schedules"]

    # Sample schedules for demonstration
    return [
        {
            "id": "weekly-report",
            "name": "Weekly Cost Report",
            "cron": "0 8 * * MON",
            "enabled": True,
            "report_type": "full",
            "recipients": ["team@example.com"],
            "slack_channel": "#cost-alerts",
            "next_run": "2026-02-17T08:00:00Z",
        },
        {
            "id": "daily-anomalies",
            "name": "Daily Anomaly Check",
            "cron": "0 9 * * *",
            "enabled": True,
            "report_type": "anomalies",
            "recipients": [],
            "slack_channel": "#cost-alerts",
            "next_run": "2026-02-11T09:00:00Z",
        },
        {
            "id": "monthly-summary",
            "name": "Monthly Executive Summary",
            "cron": "0 8 1 * *",
            "enabled": False,
            "report_type": "summary",
            "recipients": ["executives@example.com"],
            "slack_channel": None,
            "next_run": None,
        },
    ]


def load_executions():
    """Load recent executions from session state."""
    if "schedule_executions" in st.session_state:
        return st.session_state["schedule_executions"]

    # Sample executions for demonstration
    return [
        {
            "schedule_id": "weekly-report",
            "start_time": "2026-02-10T08:00:00Z",
            "end_time": "2026-02-10T08:02:15Z",
            "status": "success",
            "report_path": "reports/weekly-report_20260210_080000.xlsx",
            "notifications_sent": 2,
        },
        {
            "schedule_id": "daily-anomalies",
            "start_time": "2026-02-10T09:00:00Z",
            "end_time": "2026-02-10T09:01:30Z",
            "status": "success",
            "report_path": "reports/daily-anomalies_20260210_090000.json",
            "notifications_sent": 1,
        },
        {
            "schedule_id": "weekly-report",
            "start_time": "2026-02-03T08:00:00Z",
            "end_time": "2026-02-03T08:03:00Z",
            "status": "failed",
            "error": "AWS connection timeout",
            "notifications_sent": 0,
        },
    ]


schedules = load_schedules()
executions = load_executions()

# Summary metrics
st.header("Overview")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Schedules", len(schedules))

with col2:
    enabled = len([s for s in schedules if s.get("enabled")])
    st.metric("Active", enabled)

with col3:
    recent_success = len([e for e in executions if e.get("status") == "success"])
    st.metric("Recent Successes", recent_success)

with col4:
    recent_failed = len([e for e in executions if e.get("status") == "failed"])
    st.metric("Recent Failures", recent_failed, delta_color="inverse")

st.divider()

# Schedules table
st.header("Configured Schedules")

if schedules:
    df = pd.DataFrame(schedules)

    # Format for display
    df["status"] = df["enabled"].map({True: "Active", False: "Disabled"})
    df["notification_targets"] = df.apply(
        lambda r: ", ".join(filter(None, [
            f"{len(r.get('recipients', []))} email(s)" if r.get("recipients") else None,
            r.get("slack_channel")
        ])) or "None",
        axis=1
    )

    st.dataframe(
        df[["name", "cron", "status", "report_type", "notification_targets", "next_run"]],
        use_container_width=True,
        column_config={
            "name": st.column_config.TextColumn("Schedule Name", width="medium"),
            "cron": st.column_config.TextColumn("Cron Expression", width="small"),
            "status": st.column_config.TextColumn("Status", width="small"),
            "report_type": st.column_config.TextColumn("Report Type", width="small"),
            "notification_targets": st.column_config.TextColumn("Notifications", width="medium"),
            "next_run": st.column_config.TextColumn("Next Run", width="medium"),
        }
    )

else:
    st.info("No schedules configured. Add schedules in `config/config.yaml`.")

st.divider()

# Recent executions
st.header("Recent Executions")

if executions:
    exec_df = pd.DataFrame(executions)

    # Status indicator
    def status_emoji(status):
        return "" if status == "success" else ""

    exec_df["status_display"] = exec_df["status"].apply(
        lambda s: f"{'Success' if s == 'success' else 'Failed'}"
    )

    st.dataframe(
        exec_df[["schedule_id", "start_time", "status_display", "report_path", "notifications_sent"]],
        use_container_width=True,
        column_config={
            "schedule_id": st.column_config.TextColumn("Schedule", width="medium"),
            "start_time": st.column_config.TextColumn("Executed At", width="medium"),
            "status_display": st.column_config.TextColumn("Status", width="small"),
            "report_path": st.column_config.TextColumn("Report", width="large"),
            "notifications_sent": st.column_config.NumberColumn("Notifications", width="small"),
        }
    )

else:
    st.info("No recent executions.")

st.divider()

# Manual execution
st.header("Run Schedule Now")

schedule_options = {s["name"]: s["id"] for s in schedules if s.get("enabled")}

if schedule_options:
    col1, col2 = st.columns([3, 1])

    with col1:
        selected_name = st.selectbox(
            "Select Schedule",
            options=list(schedule_options.keys())
        )

    with col2:
        st.write("")  # Spacing
        st.write("")
        if st.button("Run Now", type="primary"):
            selected_id = schedule_options[selected_name]
            st.info(f"Executing schedule: {selected_name} (ID: {selected_id})")
            st.markdown("""
            To run a schedule manually, use the CLI:
            ```bash
            python run.py --run-schedule {schedule_id}
            ```
            """.format(schedule_id=selected_id))

else:
    st.warning("No active schedules available to run.")

st.divider()

# Configuration help
st.header("Configuration")

with st.expander("How to Configure Schedules", expanded=False):
    st.markdown("""
    ### Adding Schedules

    Add schedules to `config/config.yaml`:

    ```yaml
    schedules:
      - id: "weekly-report"
        name: "Weekly Cost Report"
        cron: "0 8 * * MON"  # Every Monday at 8 AM
        report_type: "full"
        recipients:
          - "team@example.com"
          - "manager@example.com"
        slack_channel: "#cost-alerts"

      - id: "daily-anomalies"
        name: "Daily Anomaly Check"
        cron: "0 9 * * *"  # Every day at 9 AM
        report_type: "anomalies"
        slack_channel: "#cost-alerts"
    ```

    ### Cron Expression Reference

    | Expression | Description |
    |------------|-------------|
    | `0 8 * * MON` | Every Monday at 8:00 AM |
    | `0 9 * * *` | Every day at 9:00 AM |
    | `0 8 1 * *` | First day of month at 8:00 AM |
    | `0 */4 * * *` | Every 4 hours |

    ### Report Types

    - `full` - Complete cost optimization report with all servers
    - `summary` - Executive summary with key metrics
    - `anomalies` - Cost anomaly detection results only

    ### Running the Scheduler Daemon

    ```bash
    python run.py --daemon
    ```

    This starts the scheduler in the background to execute schedules automatically.
    """)

with st.expander("Notification Configuration", expanded=False):
    st.markdown("""
    ### Email Configuration

    Add SMTP settings to `config/config.yaml`:

    ```yaml
    notifications:
      email:
        smtp_host: "smtp.example.com"
        smtp_port: 587
        use_tls: true
        from_address: "cost-optimizer@example.com"
    ```

    Add credentials to `config/credentials.yaml`:

    ```yaml
    notifications:
      email:
        username: "your-smtp-username"
        password: "your-smtp-password"
    ```

    ### Slack Configuration

    1. Create a Slack Incoming Webhook at https://api.slack.com/messaging/webhooks
    2. Add the webhook URL to `config/config.yaml`:

    ```yaml
    notifications:
      slack:
        default_webhook: "https://hooks.slack.com/services/..."
    ```

    ### Testing Notifications

    ```bash
    # Test email
    python run.py --test-email recipient@example.com

    # Test Slack
    python run.py --test-slack
    ```
    """)

# Export schedules
st.header("Export")

if schedules:
    import json
    schedules_json = json.dumps(schedules, indent=2)
    st.download_button(
        label="Download Schedules JSON",
        data=schedules_json,
        file_name="schedules.json",
        mime="application/json"
    )

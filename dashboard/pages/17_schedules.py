"""Schedule Management page."""
import streamlit as st
import pandas as pd
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from styles import inject_styles, page_header, section_header, chart_header, metrics_row

st.set_page_config(page_title="Schedules", page_icon="📅", layout="wide")
inject_styles()

page_header("📅 Report Schedules", "Manage automated report generation and notifications")


def load_schedules():
    """Load schedules from session state or config."""
    if "schedules" in st.session_state:
        return st.session_state["schedules"]
    return [
        {"id": "weekly-report", "name": "Weekly Cost Report", "cron": "0 8 * * MON", "enabled": True, "report_type": "full", "recipients": ["team@example.com"], "slack_channel": "#cost-alerts", "next_run": "2026-02-17T08:00:00Z"},
        {"id": "daily-anomalies", "name": "Daily Anomaly Check", "cron": "0 9 * * *", "enabled": True, "report_type": "anomalies", "recipients": [], "slack_channel": "#cost-alerts", "next_run": "2026-02-11T09:00:00Z"},
        {"id": "monthly-summary", "name": "Monthly Executive Summary", "cron": "0 8 1 * *", "enabled": False, "report_type": "summary", "recipients": ["executives@example.com"], "slack_channel": None, "next_run": None},
    ]


def load_executions():
    """Load recent executions from session state."""
    if "schedule_executions" in st.session_state:
        return st.session_state["schedule_executions"]
    return [
        {"schedule_id": "weekly-report", "start_time": "2026-02-10T08:00:00Z", "end_time": "2026-02-10T08:02:15Z", "status": "success", "report_path": "reports/weekly-report_20260210.xlsx", "notifications_sent": 2},
        {"schedule_id": "daily-anomalies", "start_time": "2026-02-10T09:00:00Z", "end_time": "2026-02-10T09:01:30Z", "status": "success", "report_path": "reports/daily-anomalies_20260210.json", "notifications_sent": 1},
        {"schedule_id": "weekly-report", "start_time": "2026-02-03T08:00:00Z", "end_time": "2026-02-03T08:03:00Z", "status": "failed", "error": "AWS connection timeout", "notifications_sent": 0},
    ]


schedules = load_schedules()
executions = load_executions()

section_header("Overview")

enabled = len([s for s in schedules if s.get("enabled")])
recent_success = len([e for e in executions if e.get("status") == "success"])
recent_failed = len([e for e in executions if e.get("status") == "failed"])

st.markdown(metrics_row([
    ("📋", len(schedules), "Total Schedules"),
    ("✅", enabled, "Active", "green"),
    ("📊", recent_success, "Recent Successes", "green"),
    ("❌", recent_failed, "Recent Failures", "red"),
]), unsafe_allow_html=True)

st.divider()

section_header("Configured Schedules")

if schedules:
    df = pd.DataFrame(schedules)
    df["status"] = df["enabled"].map({True: "Active", False: "Disabled"})
    df["notification_targets"] = df.apply(
        lambda r: ", ".join(filter(None, [
            f"{len(r.get('recipients', []))} email(s)" if r.get("recipients") else None,
            r.get("slack_channel")
        ])) or "None", axis=1)

    st.dataframe(df[["name", "cron", "status", "report_type", "notification_targets", "next_run"]], use_container_width=True, column_config={
        "name": st.column_config.TextColumn("Schedule Name"),
        "cron": st.column_config.TextColumn("Cron Expression"),
        "status": st.column_config.TextColumn("Status"),
        "report_type": st.column_config.TextColumn("Report Type"),
        "notification_targets": st.column_config.TextColumn("Notifications"),
        "next_run": st.column_config.TextColumn("Next Run"),
    })
else:
    st.info("No schedules configured. Add schedules in `config/config.yaml`.")

st.divider()

section_header("Recent Executions")

if executions:
    exec_df = pd.DataFrame(executions)
    exec_df["status_display"] = exec_df["status"].apply(lambda s: "✅ Success" if s == "success" else "❌ Failed")

    st.dataframe(exec_df[["schedule_id", "start_time", "status_display", "report_path", "notifications_sent"]], use_container_width=True, column_config={
        "schedule_id": st.column_config.TextColumn("Schedule"),
        "start_time": st.column_config.TextColumn("Executed At"),
        "status_display": st.column_config.TextColumn("Status"),
        "report_path": st.column_config.TextColumn("Report"),
        "notifications_sent": st.column_config.NumberColumn("Notifications"),
    })
else:
    st.info("No recent executions.")

st.divider()

section_header("Run Schedule Now")

schedule_options = {s["name"]: s["id"] for s in schedules if s.get("enabled")}

if schedule_options:
    col1, col2 = st.columns([3, 1])
    with col1:
        selected_name = st.selectbox("Select Schedule", options=list(schedule_options.keys()))
    with col2:
        st.write("")
        st.write("")
        if st.button("Run Now", type="primary"):
            selected_id = schedule_options[selected_name]
            st.info(f"Executing schedule: {selected_name} (ID: {selected_id})")
            st.code(f"python run.py --run-schedule {selected_id}", language="bash")
else:
    st.markdown("""
    <div class="info-box warning">
        No active schedules available to run.
    </div>
    """, unsafe_allow_html=True)

st.divider()

section_header("Configuration")

with st.expander("How to Configure Schedules"):
    st.markdown("""
    ### Adding Schedules
    Add schedules to `config/config.yaml`:
    ```yaml
    schedules:
      - id: "weekly-report"
        name: "Weekly Cost Report"
        cron: "0 8 * * MON"  # Every Monday at 8 AM
        report_type: "full"
        recipients: ["team@example.com"]
        slack_channel: "#cost-alerts"
    ```

    ### Cron Reference
    | Expression | Description |
    |------------|-------------|
    | `0 8 * * MON` | Every Monday at 8:00 AM |
    | `0 9 * * *` | Every day at 9:00 AM |
    | `0 8 1 * *` | First day of month at 8:00 AM |

    ### Running the Scheduler Daemon
    ```bash
    python run.py --daemon
    ```
    """)

with st.expander("Notification Configuration"):
    st.markdown("""
    ### Email Configuration
    Add SMTP settings to `config/config.yaml`:
    ```yaml
    notifications:
      email:
        smtp_host: "smtp.example.com"
        smtp_port: 587
        use_tls: true
    ```

    ### Slack Configuration
    ```yaml
    notifications:
      slack:
        default_webhook: "https://hooks.slack.com/services/..."
    ```

    ### Testing
    ```bash
    python run.py --test-email recipient@example.com
    python run.py --test-slack
    ```
    """)

if schedules:
    import json
    st.download_button(label="📥 Download Schedules JSON", data=json.dumps(schedules, indent=2), file_name="schedules.json", mime="application/json")

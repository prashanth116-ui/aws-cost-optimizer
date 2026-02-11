"""Slack notification sender for reports."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class SlackNotifier:
    """Send notifications to Slack via webhooks.

    Uses Slack Block Kit for rich message formatting.
    """

    def __init__(self, webhook_url: Optional[str] = None):
        """Initialize the Slack notifier.

        Args:
            webhook_url: Default Slack webhook URL
        """
        self.default_webhook = webhook_url

    def send_message(
        self,
        text: str,
        webhook_url: Optional[str] = None,
        blocks: Optional[List[Dict]] = None
    ) -> bool:
        """Send a simple message to Slack.

        Args:
            text: Message text (used as fallback)
            webhook_url: Override webhook URL
            blocks: Optional Block Kit blocks

        Returns:
            True if message was sent successfully
        """
        url = webhook_url or self.default_webhook
        if not url:
            logger.error("No Slack webhook URL configured")
            return False

        try:
            payload = {"text": text}
            if blocks:
                payload["blocks"] = blocks

            response = requests.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            if response.status_code == 200:
                logger.info("Slack message sent successfully")
                return True
            else:
                logger.error(f"Slack API error: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"Failed to send Slack message: {e}")
            return False

    def send_report_notification(
        self,
        channel: Optional[str] = None,
        schedule_name: str = "Cost Report",
        report_path: Optional[str] = None,
        summary: Optional[Dict[str, Any]] = None,
        webhook_url: Optional[str] = None
    ) -> bool:
        """Send a report completion notification.

        Args:
            channel: Slack channel (for display only, webhook determines destination)
            schedule_name: Name of the schedule/report
            report_path: Path to generated report
            summary: Optional report summary data
            webhook_url: Override webhook URL

        Returns:
            True if notification was sent successfully
        """
        blocks = self._build_report_blocks(
            schedule_name=schedule_name,
            report_path=report_path,
            summary=summary
        )

        text = f"AWS Cost Optimization Report: {schedule_name}"
        return self.send_message(text, webhook_url=webhook_url, blocks=blocks)

    def send_anomaly_alert(
        self,
        anomalies: List[Dict[str, Any]],
        severity: str = "warning",
        webhook_url: Optional[str] = None
    ) -> bool:
        """Send an anomaly detection alert.

        Args:
            anomalies: List of detected anomalies
            severity: Alert severity (warning, critical)
            webhook_url: Override webhook URL

        Returns:
            True if alert was sent successfully
        """
        blocks = self._build_anomaly_blocks(anomalies, severity)
        text = f"AWS Cost Anomaly Alert: {len(anomalies)} anomalies detected"
        return self.send_message(text, webhook_url=webhook_url, blocks=blocks)

    def send_alert(
        self,
        title: str,
        message: str,
        severity: str = "warning",
        webhook_url: Optional[str] = None
    ) -> bool:
        """Send a generic alert.

        Args:
            title: Alert title
            message: Alert message
            severity: Alert severity
            webhook_url: Override webhook URL

        Returns:
            True if alert was sent successfully
        """
        emoji = ":warning:" if severity == "warning" else ":rotating_light:"

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} {title}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": message
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Severity: *{severity.upper()}* | {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}"
                    }
                ]
            }
        ]

        return self.send_message(title, webhook_url=webhook_url, blocks=blocks)

    def _build_report_blocks(
        self,
        schedule_name: str,
        report_path: Optional[str] = None,
        summary: Optional[Dict[str, Any]] = None
    ) -> List[Dict]:
        """Build Block Kit blocks for report notification.

        Args:
            schedule_name: Name of the report
            report_path: Path to report file
            summary: Report summary data

        Returns:
            List of Block Kit blocks
        """
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": ":chart_with_upwards_trend: AWS Cost Optimization Report",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{schedule_name}* has completed successfully."
                }
            }
        ]

        if summary:
            savings = summary.get("total_monthly_savings", 0)
            savings_pct = summary.get("savings_percentage", 0)
            servers = summary.get("total_servers", 0)

            blocks.append({
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Servers Analyzed:*\n{servers}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Potential Savings:*\n:moneybag: ${savings:,.2f}/month ({savings_pct:.1f}%)"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Oversized:*\n{summary.get('oversized_count', 0)}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Undersized:*\n{summary.get('undersized_count', 0)}"
                    }
                ]
            })

        if report_path:
            report_name = Path(report_path).name
            blocks.append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f":page_facing_up: Report: `{report_name}`"
                    }
                ]
            })

        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}"
                }
            ]
        })

        return blocks

    def _build_anomaly_blocks(
        self,
        anomalies: List[Dict[str, Any]],
        severity: str
    ) -> List[Dict]:
        """Build Block Kit blocks for anomaly alert.

        Args:
            anomalies: List of detected anomalies
            severity: Alert severity

        Returns:
            List of Block Kit blocks
        """
        emoji = ":warning:" if severity == "warning" else ":rotating_light:"

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} Cost Anomaly Alert",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{len(anomalies)} cost anomalies* detected in your AWS account."
                }
            }
        ]

        # Add top anomalies (max 5)
        for anomaly in anomalies[:5]:
            service = anomaly.get("service", "Unknown")
            actual = anomaly.get("actual_cost", 0)
            expected = anomaly.get("expected_cost", 0)
            deviation = anomaly.get("deviation_percent", 0)
            a_type = anomaly.get("anomaly_type", "spike")

            direction = ":arrow_up:" if a_type == "spike" else ":arrow_down:"

            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*{service}*\n"
                        f"{direction} Actual: ${actual:,.2f} | Expected: ${expected:,.2f}\n"
                        f"Deviation: {deviation:+.1f}%"
                    )
                }
            })

        if len(anomalies) > 5:
            blocks.append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"_...and {len(anomalies) - 5} more anomalies_"
                    }
                ]
            })

        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Detected at {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}"
                }
            ]
        })

        return blocks

    def test_connection(self, webhook_url: Optional[str] = None) -> bool:
        """Test Slack webhook connection.

        Args:
            webhook_url: Override webhook URL

        Returns:
            True if connection is successful
        """
        return self.send_message(
            text="AWS Cost Optimizer: Connection test successful!",
            webhook_url=webhook_url,
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": ":white_check_mark: *AWS Cost Optimizer*\nSlack integration test successful!"
                    }
                }
            ]
        )

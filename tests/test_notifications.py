"""Tests for the notifications module."""

import pytest
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path

from src.notifications.email_sender import EmailSender, EmailConfig, create_report_email_body
from src.notifications.slack_notifier import SlackNotifier


class TestEmailConfig:
    """Tests for EmailConfig dataclass."""

    def test_from_dict(self):
        """Test creating config from dictionary."""
        data = {
            "smtp_host": "smtp.example.com",
            "smtp_port": 465,
            "username": "user",
            "password": "pass",
            "use_tls": False,
            "from_address": "from@example.com",
        }

        config = EmailConfig.from_dict(data)

        assert config.smtp_host == "smtp.example.com"
        assert config.smtp_port == 465
        assert config.username == "user"
        assert config.password == "pass"
        assert config.use_tls is False
        assert config.from_address == "from@example.com"

    def test_from_dict_defaults(self):
        """Test defaults when creating from minimal dict."""
        data = {"smtp_host": "smtp.example.com"}

        config = EmailConfig.from_dict(data)

        assert config.smtp_host == "smtp.example.com"
        assert config.smtp_port == 587  # Default
        assert config.use_tls is True  # Default
        assert config.username is None
        assert config.password is None


class TestEmailSender:
    """Tests for EmailSender."""

    def test_init(self):
        """Test initialization."""
        config = EmailConfig(
            smtp_host="smtp.example.com",
            smtp_port=587,
            username="user",
            password="pass",
        )

        sender = EmailSender(config)

        assert sender.config == config

    def test_send_report_no_recipients(self):
        """Test sending report with no recipients."""
        config = EmailConfig(smtp_host="smtp.example.com")
        sender = EmailSender(config)

        result = sender.send_report(
            recipients=[],
            subject="Test",
            report_path="/path/to/report.xlsx",
        )

        assert result is False

    def test_send_report_file_not_found(self):
        """Test sending report when file doesn't exist."""
        config = EmailConfig(smtp_host="smtp.example.com")
        sender = EmailSender(config)

        result = sender.send_report(
            recipients=["test@example.com"],
            subject="Test",
            report_path="/nonexistent/report.xlsx",
        )

        assert result is False

    @patch("src.notifications.email_sender.smtplib.SMTP")
    def test_send_report_success(self, mock_smtp):
        """Test successful report sending."""
        config = EmailConfig(
            smtp_host="smtp.example.com",
            smtp_port=587,
            username="user",
            password="pass",
        )
        sender = EmailSender(config)

        # Mock file existence
        with patch.object(Path, "exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=b"test data")):
                result = sender.send_report(
                    recipients=["test@example.com"],
                    subject="Test Report",
                    report_path="/path/to/report.xlsx",
                )

        assert result is True
        mock_smtp.assert_called_once_with("smtp.example.com", 587)

    @patch("src.notifications.email_sender.smtplib.SMTP")
    def test_send_report_smtp_error(self, mock_smtp):
        """Test handling SMTP error."""
        mock_smtp.side_effect = Exception("SMTP error")

        config = EmailConfig(smtp_host="smtp.example.com")
        sender = EmailSender(config)

        with patch.object(Path, "exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=b"test data")):
                result = sender.send_report(
                    recipients=["test@example.com"],
                    subject="Test",
                    report_path="/path/to/report.xlsx",
                )

        assert result is False

    @patch("src.notifications.email_sender.smtplib.SMTP")
    def test_send_alert(self, mock_smtp):
        """Test sending an alert."""
        config = EmailConfig(
            smtp_host="smtp.example.com",
            username="user",
            password="pass",
        )
        sender = EmailSender(config)

        result = sender.send_alert(
            recipients=["test@example.com"],
            subject="Alert",
            message="Test alert message",
            severity="warning",
        )

        assert result is True

    @patch("src.notifications.email_sender.smtplib.SMTP")
    def test_test_connection_success(self, mock_smtp):
        """Test successful connection test."""
        config = EmailConfig(
            smtp_host="smtp.example.com",
            username="user",
            password="pass",
        )
        sender = EmailSender(config)

        result = sender.test_connection()

        assert result is True

    @patch("src.notifications.email_sender.smtplib.SMTP")
    def test_test_connection_failure(self, mock_smtp):
        """Test failed connection test."""
        mock_smtp.side_effect = Exception("Connection refused")

        config = EmailConfig(smtp_host="smtp.example.com")
        sender = EmailSender(config)

        result = sender.test_connection()

        assert result is False


class TestCreateReportEmailBody:
    """Tests for email body generation."""

    def test_create_body(self):
        """Test creating email body from summary."""
        summary = {
            "total_servers": 100,
            "total_current_monthly": 50000.00,
            "total_monthly_savings": 10000.00,
            "total_yearly_savings": 120000.00,
            "savings_percentage": 20.0,
            "oversized_count": 40,
            "right_sized_count": 50,
            "undersized_count": 10,
            "contention_count": 5,
        }

        text, html = create_report_email_body(summary, "/path/to/report.xlsx")

        assert "100" in text
        assert "$50,000.00" in text
        assert "$10,000.00" in text
        assert "20.0%" in text

        assert "100" in html
        assert "$50,000.00" in html
        assert "#28a745" in html  # Green color for savings


class TestSlackNotifier:
    """Tests for SlackNotifier."""

    def test_init_with_webhook(self):
        """Test initialization with webhook."""
        notifier = SlackNotifier("https://hooks.slack.com/test")

        assert notifier.default_webhook == "https://hooks.slack.com/test"

    def test_init_without_webhook(self):
        """Test initialization without webhook."""
        notifier = SlackNotifier()

        assert notifier.default_webhook is None

    def test_send_message_no_webhook(self):
        """Test sending message without webhook configured."""
        notifier = SlackNotifier()

        result = notifier.send_message("Test message")

        assert result is False

    @patch("src.notifications.slack_notifier.requests.post")
    def test_send_message_success(self, mock_post):
        """Test successful message sending."""
        mock_post.return_value.status_code = 200

        notifier = SlackNotifier("https://hooks.slack.com/test")

        result = notifier.send_message("Test message")

        assert result is True
        mock_post.assert_called_once()

    @patch("src.notifications.slack_notifier.requests.post")
    def test_send_message_api_error(self, mock_post):
        """Test handling API error."""
        mock_post.return_value.status_code = 400
        mock_post.return_value.text = "invalid_payload"

        notifier = SlackNotifier("https://hooks.slack.com/test")

        result = notifier.send_message("Test message")

        assert result is False

    @patch("src.notifications.slack_notifier.requests.post")
    def test_send_message_with_blocks(self, mock_post):
        """Test sending message with blocks."""
        mock_post.return_value.status_code = 200

        notifier = SlackNotifier("https://hooks.slack.com/test")

        blocks = [
            {"type": "section", "text": {"type": "mrkdwn", "text": "Test"}}
        ]

        result = notifier.send_message("Test", blocks=blocks)

        assert result is True
        call_args = mock_post.call_args
        assert "blocks" in call_args.kwargs["json"]

    @patch("src.notifications.slack_notifier.requests.post")
    def test_send_report_notification(self, mock_post):
        """Test sending report notification."""
        mock_post.return_value.status_code = 200

        notifier = SlackNotifier("https://hooks.slack.com/test")

        summary = {
            "total_servers": 100,
            "total_monthly_savings": 10000,
            "savings_percentage": 20.0,
            "oversized_count": 40,
            "undersized_count": 10,
        }

        result = notifier.send_report_notification(
            schedule_name="Weekly Report",
            report_path="/path/to/report.xlsx",
            summary=summary,
        )

        assert result is True

    @patch("src.notifications.slack_notifier.requests.post")
    def test_send_anomaly_alert(self, mock_post):
        """Test sending anomaly alert."""
        mock_post.return_value.status_code = 200

        notifier = SlackNotifier("https://hooks.slack.com/test")

        anomalies = [
            {
                "service": "EC2",
                "actual_cost": 200.0,
                "expected_cost": 100.0,
                "deviation_percent": 100.0,
                "anomaly_type": "spike",
            },
            {
                "service": "RDS",
                "actual_cost": 50.0,
                "expected_cost": 100.0,
                "deviation_percent": -50.0,
                "anomaly_type": "drop",
            },
        ]

        result = notifier.send_anomaly_alert(anomalies, severity="critical")

        assert result is True

    @patch("src.notifications.slack_notifier.requests.post")
    def test_send_alert(self, mock_post):
        """Test sending generic alert."""
        mock_post.return_value.status_code = 200

        notifier = SlackNotifier("https://hooks.slack.com/test")

        result = notifier.send_alert(
            title="Test Alert",
            message="This is a test alert",
            severity="warning",
        )

        assert result is True

    @patch("src.notifications.slack_notifier.requests.post")
    def test_test_connection(self, mock_post):
        """Test connection test."""
        mock_post.return_value.status_code = 200

        notifier = SlackNotifier("https://hooks.slack.com/test")

        result = notifier.test_connection()

        assert result is True

    @patch("src.notifications.slack_notifier.requests.post")
    def test_send_message_timeout(self, mock_post):
        """Test handling timeout."""
        import requests
        mock_post.side_effect = requests.Timeout()

        notifier = SlackNotifier("https://hooks.slack.com/test")

        result = notifier.send_message("Test")

        assert result is False


class TestSlackBlockBuilding:
    """Tests for Slack Block Kit building."""

    def test_build_report_blocks(self):
        """Test building report notification blocks."""
        notifier = SlackNotifier()

        summary = {
            "total_servers": 100,
            "total_monthly_savings": 10000,
            "savings_percentage": 20.0,
            "oversized_count": 40,
            "undersized_count": 10,
        }

        blocks = notifier._build_report_blocks(
            schedule_name="Test Report",
            report_path="/path/to/report.xlsx",
            summary=summary,
        )

        assert len(blocks) > 0
        # Should have header block
        assert blocks[0]["type"] == "header"
        # Should include summary fields
        fields_block = next((b for b in blocks if b.get("type") == "section" and "fields" in b), None)
        assert fields_block is not None

    def test_build_anomaly_blocks(self):
        """Test building anomaly alert blocks."""
        notifier = SlackNotifier()

        anomalies = [
            {
                "service": "EC2",
                "actual_cost": 200.0,
                "expected_cost": 100.0,
                "deviation_percent": 100.0,
                "anomaly_type": "spike",
            },
        ]

        blocks = notifier._build_anomaly_blocks(anomalies, severity="critical")

        assert len(blocks) > 0
        # Should have header with rotating light emoji
        assert ":rotating_light:" in blocks[0]["text"]["text"]

    def test_build_anomaly_blocks_warning(self):
        """Test building warning-level anomaly blocks."""
        notifier = SlackNotifier()

        anomalies = [
            {"service": "EC2", "actual_cost": 150, "expected_cost": 100,
             "deviation_percent": 50, "anomaly_type": "spike"},
        ]

        blocks = notifier._build_anomaly_blocks(anomalies, severity="warning")

        # Should have header with warning emoji
        assert ":warning:" in blocks[0]["text"]["text"]

    def test_build_anomaly_blocks_many(self):
        """Test building blocks with many anomalies (truncation)."""
        notifier = SlackNotifier()

        anomalies = [
            {"service": f"Service{i}", "actual_cost": 200, "expected_cost": 100,
             "deviation_percent": 100, "anomaly_type": "spike"}
            for i in range(10)
        ]

        blocks = notifier._build_anomaly_blocks(anomalies, severity="warning")

        # Should show 5 anomalies + "and X more" context
        context_blocks = [b for b in blocks if b.get("type") == "context"]
        # At least one context block should mention remaining anomalies
        has_more_text = any(
            "more anomalies" in str(b)
            for b in context_blocks
        )
        assert has_more_text

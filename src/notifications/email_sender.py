"""Email notification sender for reports."""

import logging
import smtplib
from dataclasses import dataclass
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class EmailConfig:
    """Email configuration."""

    smtp_host: str
    smtp_port: int = 587
    username: Optional[str] = None
    password: Optional[str] = None
    use_tls: bool = True
    from_address: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EmailConfig":
        """Create from dictionary."""
        return cls(
            smtp_host=data.get("smtp_host", ""),
            smtp_port=data.get("smtp_port", 587),
            username=data.get("username"),
            password=data.get("password"),
            use_tls=data.get("use_tls", True),
            from_address=data.get("from_address"),
        )


class EmailSender:
    """Send email notifications with report attachments.

    Supports SMTP with TLS for secure email delivery.
    """

    def __init__(self, config: EmailConfig):
        """Initialize the email sender.

        Args:
            config: Email configuration
        """
        self.config = config

    def send_report(
        self,
        recipients: List[str],
        subject: str,
        report_path: str,
        body_html: Optional[str] = None,
        body_text: Optional[str] = None,
    ) -> bool:
        """Send a report via email.

        Args:
            recipients: List of email addresses
            subject: Email subject
            report_path: Path to report file to attach
            body_html: Optional HTML body
            body_text: Optional plain text body

        Returns:
            True if email was sent successfully
        """
        if not recipients:
            logger.warning("No recipients specified, skipping email")
            return False

        report_file = Path(report_path)
        if not report_file.exists():
            logger.error(f"Report file not found: {report_path}")
            return False

        try:
            msg = self._create_message(
                recipients=recipients,
                subject=subject,
                report_path=report_file,
                body_html=body_html,
                body_text=body_text,
            )

            self._send_message(msg, recipients)
            logger.info(f"Email sent to {len(recipients)} recipients")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def send_alert(
        self,
        recipients: List[str],
        subject: str,
        message: str,
        severity: str = "warning"
    ) -> bool:
        """Send an alert email without attachment.

        Args:
            recipients: List of email addresses
            subject: Email subject
            message: Alert message
            severity: Alert severity (info, warning, critical)

        Returns:
            True if email was sent successfully
        """
        if not recipients:
            return False

        try:
            # Format alert message
            severity_colors = {
                "info": "#3498db",
                "warning": "#f39c12",
                "critical": "#e74c3c",
            }
            color = severity_colors.get(severity, "#3498db")

            html = f"""
            <html>
            <body>
            <div style="border-left: 4px solid {color}; padding-left: 15px;">
                <h2 style="color: {color};">AWS Cost Optimizer Alert</h2>
                <p><strong>Severity:</strong> {severity.upper()}</p>
                <p>{message}</p>
            </div>
            <hr>
            <p style="color: #888; font-size: 12px;">
                This is an automated alert from AWS Cost Optimizer.
            </p>
            </body>
            </html>
            """

            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.config.from_address or self.config.username or "cost-optimizer@localhost"
            msg["To"] = ", ".join(recipients)

            msg.attach(MIMEText(message, "plain"))
            msg.attach(MIMEText(html, "html"))

            self._send_message(msg, recipients)
            return True

        except Exception as e:
            logger.error(f"Failed to send alert email: {e}")
            return False

    def _create_message(
        self,
        recipients: List[str],
        subject: str,
        report_path: Path,
        body_html: Optional[str] = None,
        body_text: Optional[str] = None,
    ) -> MIMEMultipart:
        """Create the email message with attachment.

        Args:
            recipients: List of email addresses
            subject: Email subject
            report_path: Path to report file
            body_html: Optional HTML body
            body_text: Optional plain text body

        Returns:
            Constructed email message
        """
        msg = MIMEMultipart()
        msg["Subject"] = subject
        msg["From"] = self.config.from_address or self.config.username or "cost-optimizer@localhost"
        msg["To"] = ", ".join(recipients)

        # Default body if not provided
        if not body_text:
            body_text = f"""
AWS Cost Optimization Report

Please find the attached report with cost optimization recommendations.

Report: {report_path.name}

This is an automated report from AWS Cost Optimizer.
            """.strip()

        if not body_html:
            body_html = f"""
            <html>
            <body>
            <h2>AWS Cost Optimization Report</h2>
            <p>Please find the attached report with cost optimization recommendations.</p>
            <p><strong>Report:</strong> {report_path.name}</p>
            <hr>
            <p style="color: #888; font-size: 12px;">
                This is an automated report from AWS Cost Optimizer.
            </p>
            </body>
            </html>
            """

        # Attach body
        msg.attach(MIMEText(body_text, "plain"))
        msg.attach(MIMEText(body_html, "html"))

        # Attach report file
        with open(report_path, "rb") as f:
            attachment = MIMEApplication(f.read())
            attachment.add_header(
                "Content-Disposition",
                "attachment",
                filename=report_path.name
            )
            msg.attach(attachment)

        return msg

    def _send_message(self, msg: MIMEMultipart, recipients: List[str]) -> None:
        """Send the email message via SMTP.

        Args:
            msg: Email message to send
            recipients: List of recipient addresses
        """
        with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port) as server:
            if self.config.use_tls:
                server.starttls()

            if self.config.username and self.config.password:
                server.login(self.config.username, self.config.password)

            from_addr = self.config.from_address or self.config.username or "cost-optimizer@localhost"
            server.sendmail(from_addr, recipients, msg.as_string())

    def test_connection(self) -> bool:
        """Test SMTP connection.

        Returns:
            True if connection is successful
        """
        try:
            with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port) as server:
                if self.config.use_tls:
                    server.starttls()

                if self.config.username and self.config.password:
                    server.login(self.config.username, self.config.password)

                logger.info("SMTP connection successful")
                return True

        except Exception as e:
            logger.error(f"SMTP connection failed: {e}")
            return False


def create_report_email_body(
    summary: Dict[str, Any],
    report_path: str
) -> tuple[str, str]:
    """Create email body from report summary.

    Args:
        summary: Report summary dictionary
        report_path: Path to report file

    Returns:
        Tuple of (plain_text, html) body content
    """
    text = f"""
AWS Cost Optimization Report Summary

Servers Analyzed: {summary.get('total_servers', 0)}
Current Monthly Spend: ${summary.get('total_current_monthly', 0):,.2f}
Potential Monthly Savings: ${summary.get('total_monthly_savings', 0):,.2f}
Potential Yearly Savings: ${summary.get('total_yearly_savings', 0):,.2f}
Savings Percentage: {summary.get('savings_percentage', 0):.1f}%

Classification Breakdown:
- Oversized (can downsize): {summary.get('oversized_count', 0)}
- Right-sized: {summary.get('right_sized_count', 0)}
- Undersized (need upgrade): {summary.get('undersized_count', 0)}
- With Contention: {summary.get('contention_count', 0)}

Please see the attached report for full details.

Report: {Path(report_path).name}
    """.strip()

    html = f"""
    <html>
    <body>
    <h2>AWS Cost Optimization Report Summary</h2>

    <table border="0" cellpadding="8" style="border-collapse: collapse;">
        <tr style="background-color: #f5f5f5;">
            <td><strong>Servers Analyzed</strong></td>
            <td>{summary.get('total_servers', 0)}</td>
        </tr>
        <tr>
            <td><strong>Current Monthly Spend</strong></td>
            <td>${summary.get('total_current_monthly', 0):,.2f}</td>
        </tr>
        <tr style="background-color: #f5f5f5;">
            <td><strong>Potential Monthly Savings</strong></td>
            <td style="color: #28a745; font-weight: bold;">${summary.get('total_monthly_savings', 0):,.2f}</td>
        </tr>
        <tr>
            <td><strong>Potential Yearly Savings</strong></td>
            <td style="color: #28a745; font-weight: bold;">${summary.get('total_yearly_savings', 0):,.2f}</td>
        </tr>
        <tr style="background-color: #f5f5f5;">
            <td><strong>Savings Percentage</strong></td>
            <td>{summary.get('savings_percentage', 0):.1f}%</td>
        </tr>
    </table>

    <h3>Classification Breakdown</h3>
    <ul>
        <li><span style="color: #28a745;">Oversized (can downsize):</span> {summary.get('oversized_count', 0)}</li>
        <li>Right-sized: {summary.get('right_sized_count', 0)}</li>
        <li><span style="color: #dc3545;">Undersized (need upgrade):</span> {summary.get('undersized_count', 0)}</li>
        <li><span style="color: #ffc107;">With Contention:</span> {summary.get('contention_count', 0)}</li>
    </ul>

    <p>Please see the attached report for full details.</p>

    <hr>
    <p style="color: #888; font-size: 12px;">
        Report: {Path(report_path).name}<br>
        This is an automated report from AWS Cost Optimizer.
    </p>
    </body>
    </html>
    """

    return text, html

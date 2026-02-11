"""Notifications module for email and Slack alerts."""

from .email_sender import EmailSender, EmailConfig
from .slack_notifier import SlackNotifier

__all__ = ["EmailSender", "EmailConfig", "SlackNotifier"]

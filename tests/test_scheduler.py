"""Tests for the scheduler module."""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from src.scheduler.scheduler import ReportScheduler, ScheduleConfig, ScheduleExecution


class TestScheduleConfig:
    """Tests for ScheduleConfig dataclass."""

    def test_from_dict_full(self):
        """Test creating config from complete dictionary."""
        data = {
            "id": "test-schedule",
            "name": "Test Schedule",
            "cron": "0 8 * * MON",
            "report_type": "full",
            "recipients": ["test@example.com"],
            "slack_channel": "#alerts",
            "enabled": True,
            "input_file": "servers.csv",
            "tags": {"GSI": "MyProject"},
        }

        config = ScheduleConfig.from_dict(data)

        assert config.id == "test-schedule"
        assert config.name == "Test Schedule"
        assert config.cron == "0 8 * * MON"
        assert config.report_type == "full"
        assert config.recipients == ["test@example.com"]
        assert config.slack_channel == "#alerts"
        assert config.enabled is True
        assert config.input_file == "servers.csv"
        assert config.tags == {"GSI": "MyProject"}

    def test_from_dict_minimal(self):
        """Test creating config from minimal dictionary."""
        data = {
            "id": "minimal",
            "cron": "0 * * * *",
        }

        config = ScheduleConfig.from_dict(data)

        assert config.id == "minimal"
        assert config.name == "minimal"  # Falls back to id
        assert config.cron == "0 * * * *"
        assert config.report_type == "full"  # Default
        assert config.recipients == []
        assert config.slack_channel is None
        assert config.enabled is True  # Default

    def test_to_dict(self):
        """Test converting config to dictionary."""
        config = ScheduleConfig(
            id="test",
            name="Test",
            cron="0 8 * * *",
            recipients=["a@b.com"],
        )

        result = config.to_dict()

        assert result["id"] == "test"
        assert result["name"] == "Test"
        assert result["cron"] == "0 8 * * *"
        assert result["recipients"] == ["a@b.com"]


class TestReportScheduler:
    """Tests for ReportScheduler."""

    def test_init_default(self):
        """Test default initialization."""
        scheduler = ReportScheduler()

        assert scheduler.timezone == "UTC"
        assert scheduler.schedules == {}
        assert scheduler.scheduler is not None

    def test_init_custom_timezone(self):
        """Test initialization with custom timezone."""
        scheduler = ReportScheduler(timezone="America/New_York")

        assert scheduler.timezone == "America/New_York"

    def test_add_schedule_valid(self):
        """Test adding a valid schedule."""
        scheduler = ReportScheduler()

        config = ScheduleConfig(
            id="test",
            name="Test Schedule",
            cron="0 8 * * *",
        )

        result = scheduler.add_schedule(config)

        assert result is True
        assert "test" in scheduler.schedules

    def test_add_schedule_disabled(self):
        """Test adding a disabled schedule."""
        scheduler = ReportScheduler()

        config = ScheduleConfig(
            id="disabled",
            name="Disabled Schedule",
            cron="0 8 * * *",
            enabled=False,
        )

        result = scheduler.add_schedule(config)

        assert result is True
        # Disabled schedules are not added to active schedules
        assert "disabled" not in scheduler.schedules

    def test_add_schedule_invalid_cron(self):
        """Test adding a schedule with invalid cron."""
        scheduler = ReportScheduler()

        config = ScheduleConfig(
            id="invalid",
            name="Invalid Schedule",
            cron="not a cron expression",
        )

        result = scheduler.add_schedule(config)

        assert result is False
        assert "invalid" not in scheduler.schedules

    def test_add_schedule_missing_id(self):
        """Test adding a schedule without ID."""
        scheduler = ReportScheduler()

        config = ScheduleConfig(
            id="",
            name="No ID",
            cron="0 8 * * *",
        )

        result = scheduler.add_schedule(config)

        assert result is False

    def test_remove_schedule(self):
        """Test removing a schedule."""
        scheduler = ReportScheduler()

        config = ScheduleConfig(
            id="to-remove",
            name="To Remove",
            cron="0 8 * * *",
        )
        scheduler.add_schedule(config)

        result = scheduler.remove_schedule("to-remove")

        assert result is True
        assert "to-remove" not in scheduler.schedules

    def test_remove_schedule_not_found(self):
        """Test removing a non-existent schedule."""
        scheduler = ReportScheduler()

        result = scheduler.remove_schedule("not-found")

        assert result is False

    def test_get_schedule(self):
        """Test getting a schedule."""
        scheduler = ReportScheduler()

        config = ScheduleConfig(
            id="get-me",
            name="Get Me",
            cron="0 8 * * *",
        )
        scheduler.add_schedule(config)

        result = scheduler.get_schedule("get-me")

        assert result is not None
        assert result.id == "get-me"

    def test_get_schedule_not_found(self):
        """Test getting a non-existent schedule."""
        scheduler = ReportScheduler()

        result = scheduler.get_schedule("not-found")

        assert result is None

    def test_list_schedules(self):
        """Test listing all schedules."""
        scheduler = ReportScheduler()

        config1 = ScheduleConfig(id="s1", name="Schedule 1", cron="0 8 * * *")
        config2 = ScheduleConfig(id="s2", name="Schedule 2", cron="0 9 * * *")

        scheduler.add_schedule(config1)
        scheduler.add_schedule(config2)

        result = scheduler.list_schedules()

        assert len(result) == 2
        ids = [s["id"] for s in result]
        assert "s1" in ids
        assert "s2" in ids

    def test_set_report_generator(self):
        """Test setting a report generator."""
        scheduler = ReportScheduler()

        def my_generator(config):
            return "/path/to/report.xlsx"

        scheduler.set_report_generator(my_generator)

        assert scheduler.report_generator == my_generator

    def test_set_notification_handler(self):
        """Test setting a notification handler."""
        scheduler = ReportScheduler()

        def my_handler(config, path):
            return 1

        scheduler.set_notification_handler(my_handler)

        assert scheduler.notification_handler == my_handler

    def test_execute_schedule_with_generator(self):
        """Test executing a schedule with a generator."""
        scheduler = ReportScheduler()

        config = ScheduleConfig(
            id="exec-test",
            name="Execution Test",
            cron="0 8 * * *",
        )
        scheduler.add_schedule(config)

        # Mock generator
        mock_generator = MagicMock(return_value="/path/to/report.xlsx")
        scheduler.set_report_generator(mock_generator)

        # Mock notification handler
        mock_handler = MagicMock(return_value=2)
        scheduler.set_notification_handler(mock_handler)

        execution = scheduler.run_schedule_now("exec-test")

        assert execution is not None
        assert execution.status == "success"
        assert execution.report_path == "/path/to/report.xlsx"
        assert execution.notifications_sent == 2
        mock_generator.assert_called_once_with(config)
        mock_handler.assert_called_once()

    def test_execute_schedule_failure(self):
        """Test schedule execution failure."""
        scheduler = ReportScheduler()

        config = ScheduleConfig(
            id="fail-test",
            name="Failure Test",
            cron="0 8 * * *",
        )
        scheduler.add_schedule(config)

        # Mock generator that raises an exception
        mock_generator = MagicMock(side_effect=Exception("Test error"))
        scheduler.set_report_generator(mock_generator)

        execution = scheduler.run_schedule_now("fail-test")

        assert execution is not None
        assert execution.status == "failed"
        assert execution.error == "Test error"

    def test_execute_schedule_not_found(self):
        """Test executing a non-existent schedule."""
        scheduler = ReportScheduler()

        result = scheduler.run_schedule_now("not-found")

        assert result is None

    def test_load_schedules_from_config(self):
        """Test loading schedules from config list."""
        scheduler = ReportScheduler()

        config_list = [
            {"id": "s1", "name": "Schedule 1", "cron": "0 8 * * *"},
            {"id": "s2", "name": "Schedule 2", "cron": "0 9 * * *"},
            {"id": "s3", "name": "Disabled", "cron": "0 10 * * *", "enabled": False},
        ]

        loaded = scheduler.load_schedules_from_config(config_list)

        assert loaded == 2  # Only enabled schedules
        assert "s1" in scheduler.schedules
        assert "s2" in scheduler.schedules
        assert "s3" not in scheduler.schedules

    def test_get_recent_executions(self):
        """Test getting recent executions."""
        scheduler = ReportScheduler()

        # Add some executions
        scheduler.executions = [
            ScheduleExecution(
                schedule_id="s1",
                start_time=datetime(2026, 2, 10, 8, 0, 0, tzinfo=timezone.utc),
                end_time=datetime(2026, 2, 10, 8, 2, 0, tzinfo=timezone.utc),
                status="success",
            ),
            ScheduleExecution(
                schedule_id="s2",
                start_time=datetime(2026, 2, 9, 8, 0, 0, tzinfo=timezone.utc),
                end_time=datetime(2026, 2, 9, 8, 2, 0, tzinfo=timezone.utc),
                status="failed",
                error="Test error",
            ),
        ]

        result = scheduler.get_recent_executions(limit=5)

        assert len(result) == 2
        # Should be sorted by start_time descending
        assert result[0]["schedule_id"] == "s1"
        assert result[1]["schedule_id"] == "s2"

    def test_start_stop(self):
        """Test starting and stopping the scheduler."""
        scheduler = ReportScheduler()

        scheduler.start()
        assert scheduler.scheduler.running is True

        scheduler.stop()
        assert scheduler.scheduler.running is False


class TestScheduleExecution:
    """Tests for ScheduleExecution dataclass."""

    def test_default_values(self):
        """Test default values."""
        execution = ScheduleExecution(
            schedule_id="test",
            start_time=datetime.now(timezone.utc),
        )

        assert execution.status == "running"
        assert execution.end_time is None
        assert execution.error is None
        assert execution.report_path is None
        assert execution.notifications_sent == 0

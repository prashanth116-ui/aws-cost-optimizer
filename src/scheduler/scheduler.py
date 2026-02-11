"""Report scheduler using APScheduler."""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, JobExecutionEvent

logger = logging.getLogger(__name__)


@dataclass
class ScheduleConfig:
    """Configuration for a scheduled report."""

    id: str
    name: str
    cron: str
    report_type: str = "full"  # full, summary, anomalies
    recipients: List[str] = field(default_factory=list)
    slack_channel: Optional[str] = None
    enabled: bool = True
    input_file: Optional[str] = None
    tags: Optional[Dict[str, str]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScheduleConfig":
        """Create from dictionary."""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", data.get("id", "")),
            cron=data.get("cron", ""),
            report_type=data.get("report_type", "full"),
            recipients=data.get("recipients", []),
            slack_channel=data.get("slack_channel"),
            enabled=data.get("enabled", True),
            input_file=data.get("input_file"),
            tags=data.get("tags"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "cron": self.cron,
            "report_type": self.report_type,
            "recipients": self.recipients,
            "slack_channel": self.slack_channel,
            "enabled": self.enabled,
            "input_file": self.input_file,
            "tags": self.tags,
        }


@dataclass
class ScheduleExecution:
    """Record of a schedule execution."""

    schedule_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "running"  # running, success, failed
    error: Optional[str] = None
    report_path: Optional[str] = None
    notifications_sent: int = 0


class ReportScheduler:
    """Scheduler for automated report generation.

    Wraps APScheduler to provide scheduling for cost optimization reports.
    """

    def __init__(
        self,
        timezone: str = "UTC",
        job_store: Optional[str] = None
    ):
        """Initialize the scheduler.

        Args:
            timezone: Timezone for schedule execution
            job_store: Optional path to SQLite job store for persistence
        """
        self.timezone = timezone
        self.schedules: Dict[str, ScheduleConfig] = {}
        self.executions: List[ScheduleExecution] = []
        self.report_generator: Optional[Callable] = None
        self.notification_handler: Optional[Callable] = None

        # Configure job stores
        job_stores = {}
        if job_store:
            from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
            job_stores["default"] = SQLAlchemyJobStore(url=f"sqlite:///{job_store}")

        self.scheduler = BackgroundScheduler(
            jobstores=job_stores,
            timezone=timezone,
        )

        # Add event listeners
        self.scheduler.add_listener(self._on_job_executed, EVENT_JOB_EXECUTED)
        self.scheduler.add_listener(self._on_job_error, EVENT_JOB_ERROR)

    def set_report_generator(self, generator: Callable) -> None:
        """Set the report generation function.

        Args:
            generator: Function that takes ScheduleConfig and returns report path
        """
        self.report_generator = generator

    def set_notification_handler(self, handler: Callable) -> None:
        """Set the notification handler function.

        Args:
            handler: Function that takes (ScheduleConfig, report_path) and sends notifications
        """
        self.notification_handler = handler

    def add_schedule(self, config: ScheduleConfig) -> bool:
        """Add a new schedule.

        Args:
            config: Schedule configuration

        Returns:
            True if schedule was added successfully
        """
        if not config.id or not config.cron:
            logger.error(f"Invalid schedule config: missing id or cron")
            return False

        if not config.enabled:
            logger.info(f"Schedule {config.id} is disabled, skipping")
            return True

        try:
            trigger = CronTrigger.from_crontab(config.cron, timezone=self.timezone)

            self.scheduler.add_job(
                self._execute_schedule,
                trigger=trigger,
                id=config.id,
                name=config.name,
                args=[config],
                replace_existing=True,
            )

            self.schedules[config.id] = config
            logger.info(f"Added schedule: {config.id} ({config.cron})")
            return True

        except Exception as e:
            logger.error(f"Failed to add schedule {config.id}: {e}")
            return False

    def remove_schedule(self, schedule_id: str) -> bool:
        """Remove a schedule.

        Args:
            schedule_id: ID of schedule to remove

        Returns:
            True if schedule was removed
        """
        try:
            if schedule_id in self.schedules:
                self.scheduler.remove_job(schedule_id)
                del self.schedules[schedule_id]
                logger.info(f"Removed schedule: {schedule_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to remove schedule {schedule_id}: {e}")
            return False

    def get_schedule(self, schedule_id: str) -> Optional[ScheduleConfig]:
        """Get a schedule configuration.

        Args:
            schedule_id: ID of schedule

        Returns:
            ScheduleConfig or None
        """
        return self.schedules.get(schedule_id)

    def list_schedules(self) -> List[Dict[str, Any]]:
        """List all schedules with their next run times.

        Returns:
            List of schedule info dictionaries
        """
        result = []

        for schedule_id, config in self.schedules.items():
            job = self.scheduler.get_job(schedule_id)
            next_run = None
            if job:
                # Handle different APScheduler versions
                try:
                    next_run = getattr(job, 'next_run_time', None)
                except Exception:
                    pass

            result.append({
                "id": schedule_id,
                "name": config.name,
                "cron": config.cron,
                "enabled": config.enabled,
                "next_run": next_run.isoformat() if next_run else None,
                "report_type": config.report_type,
                "recipients": config.recipients,
            })

        return result

    def run_schedule_now(self, schedule_id: str) -> Optional[ScheduleExecution]:
        """Execute a schedule immediately.

        Args:
            schedule_id: ID of schedule to run

        Returns:
            ScheduleExecution record or None
        """
        config = self.schedules.get(schedule_id)
        if not config:
            logger.error(f"Schedule not found: {schedule_id}")
            return None

        return self._execute_schedule(config)

    def _execute_schedule(self, config: ScheduleConfig) -> ScheduleExecution:
        """Execute a scheduled report.

        Args:
            config: Schedule configuration

        Returns:
            ScheduleExecution record
        """
        execution = ScheduleExecution(
            schedule_id=config.id,
            start_time=datetime.now(timezone.utc),
        )

        logger.info(f"Executing schedule: {config.id}")

        try:
            # Generate report
            if self.report_generator:
                report_path = self.report_generator(config)
                execution.report_path = report_path
            else:
                logger.warning(f"No report generator configured for {config.id}")

            # Send notifications
            if self.notification_handler and execution.report_path:
                notifications_sent = self.notification_handler(config, execution.report_path)
                execution.notifications_sent = notifications_sent
            elif config.recipients or config.slack_channel:
                logger.warning(f"No notification handler configured for {config.id}")

            execution.status = "success"
            execution.end_time = datetime.now(timezone.utc)

            logger.info(
                f"Schedule {config.id} completed successfully. "
                f"Report: {execution.report_path}, Notifications: {execution.notifications_sent}"
            )

        except Exception as e:
            execution.status = "failed"
            execution.error = str(e)
            execution.end_time = datetime.now(timezone.utc)
            logger.error(f"Schedule {config.id} failed: {e}")

        self.executions.append(execution)
        return execution

    def _on_job_executed(self, event: JobExecutionEvent) -> None:
        """Handle successful job execution."""
        logger.debug(f"Job executed: {event.job_id}")

    def _on_job_error(self, event: JobExecutionEvent) -> None:
        """Handle job execution error."""
        logger.error(f"Job failed: {event.job_id}, error: {event.exception}")

    def start(self) -> None:
        """Start the scheduler."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started")

    def stop(self) -> None:
        """Stop the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            logger.info("Scheduler stopped")

    def get_recent_executions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent schedule executions.

        Args:
            limit: Maximum number of executions to return

        Returns:
            List of execution records
        """
        recent = sorted(
            self.executions,
            key=lambda x: x.start_time,
            reverse=True
        )[:limit]

        return [
            {
                "schedule_id": e.schedule_id,
                "start_time": e.start_time.isoformat(),
                "end_time": e.end_time.isoformat() if e.end_time else None,
                "status": e.status,
                "error": e.error,
                "report_path": e.report_path,
                "notifications_sent": e.notifications_sent,
            }
            for e in recent
        ]

    def load_schedules_from_config(self, schedules: List[Dict[str, Any]]) -> int:
        """Load schedules from configuration.

        Args:
            schedules: List of schedule dictionaries from config

        Returns:
            Number of enabled schedules loaded
        """
        loaded = 0
        for schedule_dict in schedules:
            config = ScheduleConfig.from_dict(schedule_dict)
            if config.enabled and self.add_schedule(config):
                loaded += 1

        logger.info(f"Loaded {loaded} schedules from config")
        return loaded

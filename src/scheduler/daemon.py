"""Scheduler daemon for running in background."""

import logging
import signal
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .scheduler import ReportScheduler, ScheduleConfig

logger = logging.getLogger(__name__)


class SchedulerDaemon:
    """Daemon process for running scheduled reports.

    Manages the report scheduler lifecycle and handles OS signals
    for graceful shutdown.
    """

    def __init__(
        self,
        config: Dict[str, Any],
        credentials: Dict[str, Any],
        output_dir: str = "reports"
    ):
        """Initialize the daemon.

        Args:
            config: Application configuration
            credentials: Credentials for AWS and notifications
            output_dir: Directory for generated reports
        """
        self.config = config
        self.credentials = credentials
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.running = False
        self.scheduler: Optional[ReportScheduler] = None

        # Set up signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum: int, frame: Any) -> None:
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False

    def _create_report_generator(self):
        """Create the report generator function."""
        from ..clients.aws_client import AWSClient
        from ..analysis.metrics_analyzer import MetricsAnalyzer
        from ..analysis.contention_detector import ContentionDetector
        from ..analysis.rightsizing import RightsizingEngine
        from ..analysis.anomaly_detector import CostAnomalyDetector
        from ..cost.current_spend import CurrentSpendCalculator
        from ..cost.projections import SavingsProjector
        from ..cost.historical_costs import HistoricalCostRetriever
        from ..output.report_data import ReportDataBuilder
        from ..output.excel_generator import ExcelGenerator
        from ..input.csv_parser import CSVParser

        aws_creds = self.credentials.get("aws", {})
        aws_client = AWSClient(
            access_key_id=aws_creds.get("access_key_id"),
            secret_access_key=aws_creds.get("secret_access_key"),
            profile_name=aws_creds.get("profile_name"),
        )

        def generate_report(schedule: ScheduleConfig) -> str:
            """Generate a report for the given schedule."""
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.output_dir / f"{schedule.id}_{timestamp}.xlsx"

            logger.info(f"Generating {schedule.report_type} report for {schedule.id}")

            if schedule.report_type == "anomalies":
                # Generate anomaly detection report
                detector = CostAnomalyDetector(
                    baseline_days=self.config.get("anomaly_detection", {}).get("baseline_days", 30)
                )
                retriever = HistoricalCostRetriever(aws_client)

                cost_data = retriever.get_costs_for_anomaly_detection(
                    baseline_days=30,
                    detection_days=7,
                )

                summary = detector.analyze_all_services(cost_data)
                report = detector.get_anomaly_report(summary)

                # Save as JSON for now (could extend to Excel)
                import json
                json_file = output_file.with_suffix(".json")
                with open(json_file, "w") as f:
                    json.dump(report, f, indent=2, default=str)

                return str(json_file)

            else:
                # Generate full or summary report
                # Get instances
                if schedule.input_file:
                    parser = CSVParser(schedule.input_file)
                    instances = parser.parse()
                elif schedule.tags:
                    instances = aws_client.get_instances(tags=schedule.tags)
                else:
                    instances = aws_client.get_instances()

                if not instances:
                    logger.warning(f"No instances found for {schedule.id}")
                    return ""

                # Analyze instances
                metrics_analyzer = MetricsAnalyzer(self.config.get("analysis", {}))
                contention_detector = ContentionDetector()
                rightsizing_engine = RightsizingEngine()
                spend_calculator = CurrentSpendCalculator(aws_client)
                savings_projector = SavingsProjector(spend_calculator)

                report_builder = ReportDataBuilder()

                for instance in instances:
                    instance_id = instance.get("instance_id")
                    if not instance_id:
                        continue

                    instance_type = instance.get("instance_type")
                    instance_specs = aws_client.get_instance_type_info(instance_type) if instance_type else {}

                    # Minimal metrics for scheduled reports (could enhance with CloudWatch)
                    server_metrics = metrics_analyzer.analyze_server(
                        server_id=instance_id,
                        metrics_data={},
                        hostname=instance.get("name")
                    )

                    contention = contention_detector.analyze_server(
                        server_id=instance_id,
                        metrics_data={},
                    )

                    recommendation = rightsizing_engine.recommend(
                        server_id=instance_id,
                        current_instance_type=instance_type or "",
                        cpu_p95=None,
                        memory_p95=None,
                        has_contention=contention.has_contention,
                        hostname=instance.get("name"),
                        instance_specs=instance_specs
                    )

                    projection = savings_projector.project_savings(recommendation)

                    server_report = report_builder.build_server_report(
                        instance=instance,
                        metrics=server_metrics,
                        contention=contention,
                        recommendation=recommendation,
                        projection=projection
                    )
                    report_builder.add_server(server_report)

                # Generate Excel
                generator = ExcelGenerator(output_file)
                generator.generate(report_builder)

                return str(output_file)

        return generate_report

    def _create_notification_handler(self):
        """Create the notification handler function."""
        from ..notifications.email_sender import EmailSender, EmailConfig
        from ..notifications.slack_notifier import SlackNotifier

        email_config = self.config.get("notifications", {}).get("email", {})
        email_creds = self.credentials.get("notifications", {}).get("email", {})

        email_sender = None
        if email_config.get("smtp_host"):
            email_sender = EmailSender(EmailConfig(
                smtp_host=email_config.get("smtp_host"),
                smtp_port=email_config.get("smtp_port", 587),
                username=email_creds.get("username"),
                password=email_creds.get("password"),
                use_tls=email_config.get("use_tls", True),
                from_address=email_config.get("from_address"),
            ))

        slack_webhook = self.config.get("notifications", {}).get("slack", {}).get("default_webhook")
        slack_notifier = SlackNotifier(slack_webhook) if slack_webhook else None

        def send_notifications(schedule: ScheduleConfig, report_path: str) -> int:
            """Send notifications for a completed report."""
            sent = 0

            # Send email notifications
            if email_sender and schedule.recipients:
                try:
                    email_sender.send_report(
                        recipients=schedule.recipients,
                        subject=f"AWS Cost Optimization Report: {schedule.name}",
                        report_path=report_path,
                    )
                    sent += len(schedule.recipients)
                    logger.info(f"Sent email to {len(schedule.recipients)} recipients")
                except Exception as e:
                    logger.error(f"Failed to send email: {e}")

            # Send Slack notification
            if slack_notifier and schedule.slack_channel:
                try:
                    slack_notifier.send_report_notification(
                        channel=schedule.slack_channel,
                        schedule_name=schedule.name,
                        report_path=report_path,
                    )
                    sent += 1
                    logger.info(f"Sent Slack notification to {schedule.slack_channel}")
                except Exception as e:
                    logger.error(f"Failed to send Slack notification: {e}")

            return sent

        return send_notifications

    def start(self) -> None:
        """Start the scheduler daemon."""
        logger.info("Starting scheduler daemon...")

        # Initialize scheduler
        scheduler_config = self.config.get("scheduler", {})
        self.scheduler = ReportScheduler(
            timezone=scheduler_config.get("timezone", "UTC"),
        )

        # Set up handlers
        self.scheduler.set_report_generator(self._create_report_generator())
        self.scheduler.set_notification_handler(self._create_notification_handler())

        # Load schedules from config
        schedules = self.config.get("schedules", [])
        loaded = self.scheduler.load_schedules_from_config(schedules)

        if loaded == 0:
            logger.warning("No schedules loaded. Add schedules to config/config.yaml")

        # Start scheduler
        self.scheduler.start()
        self.running = True

        logger.info(f"Scheduler daemon started with {loaded} schedules")

        # Main loop
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    def stop(self) -> None:
        """Stop the scheduler daemon."""
        logger.info("Stopping scheduler daemon...")

        if self.scheduler:
            self.scheduler.stop()

        self.running = False
        logger.info("Scheduler daemon stopped")

    def run_schedule(self, schedule_id: str) -> bool:
        """Run a specific schedule immediately.

        Args:
            schedule_id: ID of schedule to run

        Returns:
            True if schedule executed successfully
        """
        if not self.scheduler:
            # Initialize scheduler for one-off run
            self.scheduler = ReportScheduler(
                timezone=self.config.get("scheduler", {}).get("timezone", "UTC"),
            )
            self.scheduler.set_report_generator(self._create_report_generator())
            self.scheduler.set_notification_handler(self._create_notification_handler())

            # Load schedule
            schedules = self.config.get("schedules", [])
            schedule_dict = next((s for s in schedules if s.get("id") == schedule_id), None)

            if not schedule_dict:
                logger.error(f"Schedule not found: {schedule_id}")
                return False

            config = ScheduleConfig.from_dict(schedule_dict)
            self.scheduler.add_schedule(config)

        execution = self.scheduler.run_schedule_now(schedule_id)
        return execution is not None and execution.status == "success"

    def list_schedules(self) -> List[Dict[str, Any]]:
        """List all configured schedules.

        Returns:
            List of schedule info
        """
        schedules = self.config.get("schedules", [])
        return [
            {
                "id": s.get("id"),
                "name": s.get("name", s.get("id")),
                "cron": s.get("cron"),
                "enabled": s.get("enabled", True),
                "report_type": s.get("report_type", "full"),
                "recipients": s.get("recipients", []),
                "slack_channel": s.get("slack_channel"),
            }
            for s in schedules
        ]

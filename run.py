#!/usr/bin/env python3
"""CLI entry point for AWS Cost Optimizer."""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from src.utils.helpers import load_config, load_credentials, setup_logging
from src.clients.aws_client import AWSClient
from src.clients.dynatrace_client import DynatraceClient
from src.clients.cloudwatch_client import CloudWatchClient
from src.input.csv_parser import CSVParser
from src.input.tag_query import TagQuery
from src.analysis.metrics_analyzer import MetricsAnalyzer
from src.analysis.contention_detector import ContentionDetector
from src.analysis.rightsizing import RightsizingEngine
from src.cost.current_spend import CurrentSpendCalculator
from src.cost.projections import SavingsProjector
from src.output.report_data import ReportDataBuilder
from src.output.excel_generator import ExcelGenerator


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="AWS Cost Optimization Tool - Analyze EC2 usage and generate rightsizing recommendations"
    )

    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument(
        "--input", "-i",
        type=str,
        help="Path to CSV/Excel file with server list"
    )
    input_group.add_argument(
        "--tag", "-t",
        action="append",
        nargs=2,
        metavar=("KEY", "VALUE"),
        help="Query AWS by tag (can be specified multiple times)"
    )

    parser.add_argument(
        "--output", "-o",
        type=str,
        default=f"cost_optimization_report_{datetime.now().strftime('%Y%m%d')}.xlsx",
        help="Output Excel file path (default: cost_optimization_report_YYYYMMDD.xlsx)"
    )

    parser.add_argument(
        "--months", "-m",
        type=int,
        default=3,
        help="Number of months of historical data to analyze (default: 3)"
    )

    parser.add_argument(
        "--dashboard",
        action="store_true",
        help="Launch the Streamlit dashboard instead of generating a report"
    )

    parser.add_argument(
        "--region",
        type=str,
        default="us-east-1",
        help="AWS region (default: us-east-1)"
    )

    parser.add_argument(
        "--config",
        type=str,
        help="Path to custom config file"
    )

    parser.add_argument(
        "--credentials",
        type=str,
        help="Path to credentials file"
    )

    parser.add_argument(
        "--use-cloudwatch",
        action="store_true",
        help="Use CloudWatch for metrics instead of Dynatrace"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Test connections without generating report"
    )

    # Anomaly detection arguments
    parser.add_argument(
        "--detect-anomalies",
        action="store_true",
        help="Run cost anomaly detection"
    )

    parser.add_argument(
        "--baseline-days",
        type=int,
        default=30,
        help="Days of history for anomaly baseline (default: 30)"
    )

    parser.add_argument(
        "--detection-days",
        type=int,
        default=7,
        help="Recent days to check for anomalies (default: 7)"
    )

    # Scheduler arguments
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run the scheduler daemon for automated reports"
    )

    parser.add_argument(
        "--run-schedule",
        type=str,
        metavar="SCHEDULE_ID",
        help="Execute a specific schedule immediately"
    )

    parser.add_argument(
        "--list-schedules",
        action="store_true",
        help="List all configured schedules"
    )

    # Notification test arguments
    parser.add_argument(
        "--test-email",
        type=str,
        metavar="EMAIL",
        help="Send a test email to the specified address"
    )

    parser.add_argument(
        "--test-slack",
        action="store_true",
        help="Send a test Slack notification"
    )

    # Multi-account arguments
    parser.add_argument(
        "--multi-account",
        action="store_true",
        help="Enable multi-account analysis across AWS Organizations"
    )

    parser.add_argument(
        "--validate-multi-account",
        action="store_true",
        help="Validate access to all configured accounts"
    )

    return parser.parse_args()


def get_instances(
    args,
    aws_client: AWSClient,
    csv_parser: Optional[CSVParser] = None
) -> List[Dict]:
    """Get list of instances to analyze.

    Args:
        args: Command line arguments
        aws_client: AWS client instance
        csv_parser: Optional CSV parser for file input

    Returns:
        List of instance dictionaries
    """
    if args.input:
        # Parse from CSV/Excel file
        parser = CSVParser(args.input)
        servers = parser.parse()

        # Enrich with AWS data
        instance_ids = [s.get("instance_id") for s in servers if s.get("instance_id")]
        if instance_ids:
            aws_instances = aws_client.get_instances(instance_ids=instance_ids)
            aws_map = {i["instance_id"]: i for i in aws_instances}

            for server in servers:
                if server.get("instance_id") in aws_map:
                    server.update(aws_map[server["instance_id"]])

        return servers

    elif args.tag:
        # Query AWS by tags - pass credentials for multi-region support
        tags = {key: value for key, value in args.tag}
        # Get credentials from args or try to load them
        try:
            from src.utils.helpers import load_credentials
            creds = load_credentials(args.credentials if hasattr(args, 'credentials') else None)
            aws_creds = creds.get("aws", {})
        except Exception:
            aws_creds = {}

        tag_query = TagQuery(
            aws_client,
            access_key_id=aws_creds.get("access_key_id"),
            secret_access_key=aws_creds.get("secret_access_key"),
            profile_name=aws_creds.get("profile_name")
        )
        return tag_query.query(tags=tags)

    else:
        # Get all running instances
        return aws_client.get_instances()


def get_metrics(
    instances: List[Dict],
    args,
    dynatrace_client: Optional[DynatraceClient] = None,
    cloudwatch_client: Optional[CloudWatchClient] = None
) -> Dict[str, Dict]:
    """Get metrics for all instances.

    Args:
        instances: List of instance dictionaries
        args: Command line arguments
        dynatrace_client: Dynatrace client
        cloudwatch_client: CloudWatch client

    Returns:
        Dictionary mapping instance_id to metrics data
    """
    metrics_data = {}

    for instance in instances:
        instance_id = instance.get("instance_id")
        if not instance_id:
            continue

        if args.use_cloudwatch and cloudwatch_client:
            # Use CloudWatch
            metrics = cloudwatch_client.get_instance_metrics(
                instance_id=instance_id,
                months=args.months
            )
        elif dynatrace_client:
            # Use Dynatrace - find host using multiple strategies
            host = dynatrace_client.find_host(
                instance_id=instance_id,
                hostname=instance.get("name"),
                private_ip=instance.get("private_ip"),
                public_ip=instance.get("public_ip")
            )
            if host:
                metrics = dynatrace_client.get_host_metrics(
                    host_id=host["entityId"],
                    months=args.months
                )
            else:
                # Log warning for missing host mapping
                logging.warning(
                    f"Could not find Dynatrace host for instance {instance_id}. "
                    f"Falling back to empty metrics."
                )
                metrics = {}
        else:
            # Fallback to CloudWatch if available
            if cloudwatch_client:
                metrics = cloudwatch_client.get_instance_metrics(
                    instance_id=instance_id,
                    months=args.months
                )
            else:
                metrics = {}

        metrics_data[instance_id] = metrics

    return metrics_data


def run_anomaly_detection(args, config, credentials):
    """Run cost anomaly detection.

    Args:
        args: Command line arguments
        config: Application configuration
        credentials: AWS credentials
    """
    from src.analysis.anomaly_detector import CostAnomalyDetector
    from src.cost.historical_costs import HistoricalCostRetriever

    logger = logging.getLogger(__name__)
    logger.info("Running cost anomaly detection...")

    # Get anomaly config
    anomaly_config = config.get("anomaly_detection", {})
    baseline_days = args.baseline_days or anomaly_config.get("baseline_days", 30)
    detection_days = args.detection_days or anomaly_config.get("detection_days", 7)
    thresholds = anomaly_config.get("thresholds")

    # Initialize AWS client
    aws_creds = credentials.get("aws", {})
    aws_client = AWSClient(
        access_key_id=aws_creds.get("access_key_id"),
        secret_access_key=aws_creds.get("secret_access_key"),
        region=args.region,
        profile_name=aws_creds.get("profile_name")
    )

    # Initialize detector and retriever
    detector = CostAnomalyDetector(
        thresholds=thresholds,
        baseline_days=baseline_days,
    )
    retriever = HistoricalCostRetriever(aws_client)

    # Get cost data
    logger.info(f"Retrieving cost data (baseline: {baseline_days}d, detection: {detection_days}d)")
    cost_data = retriever.get_costs_for_anomaly_detection(
        baseline_days=baseline_days,
        detection_days=detection_days,
    )

    # Detect anomalies
    summary = detector.analyze_all_services(cost_data)
    report = detector.get_anomaly_report(summary)

    # Print results
    print("\n" + "=" * 60)
    print("COST ANOMALY DETECTION RESULTS")
    print("=" * 60)
    print(f"Detection Period: {report['detection_period']['start'][:10]} to {report['detection_period']['end'][:10]}")
    print(f"Total Anomalies:  {report['total_anomalies']}")
    print(f"  Critical:       {report['critical_anomalies']}")
    print(f"  Warning:        {report['warning_anomalies']}")
    print(f"Excess Cost:      ${report['total_excess_cost']:,.2f}")
    print(f"Services Affected: {report['services_affected']}")
    print("-" * 60)

    if report['top_anomalies']:
        print("\nTop Anomalies:")
        for anomaly in report['top_anomalies'][:5]:
            print(f"  [{anomaly['severity'].upper()}] {anomaly['service'][:40]}")
            print(f"    Date: {anomaly['date'][:10]}, Type: {anomaly['type']}")
            print(f"    Actual: ${anomaly['actual_cost']:,.2f}, Expected: ${anomaly['expected_cost']:,.2f}")
            print(f"    Deviation: {anomaly['deviation_percent']:+.1f}%")
            print()
    else:
        print("\nNo anomalies detected.")

    print("=" * 60)

    # Save to JSON if output specified
    if args.output and args.output.endswith('.json'):
        import json
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\nReport saved to: {args.output}")


def run_scheduler_daemon(args, config, credentials):
    """Run the scheduler daemon.

    Args:
        args: Command line arguments
        config: Application configuration
        credentials: Credentials
    """
    from src.scheduler.daemon import SchedulerDaemon

    logger = logging.getLogger(__name__)
    logger.info("Starting scheduler daemon...")

    daemon = SchedulerDaemon(
        config=config,
        credentials=credentials,
        output_dir="reports",
    )

    daemon.start()


def run_specific_schedule(args, config, credentials):
    """Run a specific schedule immediately.

    Args:
        args: Command line arguments
        config: Application configuration
        credentials: Credentials
    """
    from src.scheduler.daemon import SchedulerDaemon

    logger = logging.getLogger(__name__)
    logger.info(f"Running schedule: {args.run_schedule}")

    daemon = SchedulerDaemon(
        config=config,
        credentials=credentials,
        output_dir="reports",
    )

    success = daemon.run_schedule(args.run_schedule)

    if success:
        print(f"Schedule '{args.run_schedule}' completed successfully.")
    else:
        print(f"Schedule '{args.run_schedule}' failed.")
        sys.exit(1)


def list_schedules(config):
    """List all configured schedules.

    Args:
        config: Application configuration
    """
    schedules = config.get("schedules", [])

    if not schedules:
        print("No schedules configured.")
        print("Add schedules to config/config.yaml")
        return

    print("\nConfigured Schedules:")
    print("-" * 60)

    for schedule in schedules:
        enabled = "ENABLED" if schedule.get("enabled", True) else "DISABLED"
        print(f"  ID: {schedule.get('id')}")
        print(f"    Name: {schedule.get('name', schedule.get('id'))}")
        print(f"    Cron: {schedule.get('cron')}")
        print(f"    Type: {schedule.get('report_type', 'full')}")
        print(f"    Status: {enabled}")
        if schedule.get('recipients'):
            print(f"    Recipients: {', '.join(schedule['recipients'])}")
        if schedule.get('slack_channel'):
            print(f"    Slack: {schedule['slack_channel']}")
        print()


def test_email_notification(args, config, credentials):
    """Send a test email notification.

    Args:
        args: Command line arguments
        config: Application configuration
        credentials: Credentials
    """
    from src.notifications.email_sender import EmailSender, EmailConfig

    email_config = config.get("notifications", {}).get("email", {})
    email_creds = credentials.get("notifications", {}).get("email", {})

    if not email_config.get("smtp_host"):
        print("Email not configured. Add SMTP settings to config/config.yaml")
        sys.exit(1)

    sender = EmailSender(EmailConfig(
        smtp_host=email_config.get("smtp_host"),
        smtp_port=email_config.get("smtp_port", 587),
        username=email_creds.get("username"),
        password=email_creds.get("password"),
        use_tls=email_config.get("use_tls", True),
        from_address=email_config.get("from_address"),
    ))

    success = sender.send_alert(
        recipients=[args.test_email],
        subject="AWS Cost Optimizer - Test Email",
        message="This is a test email from AWS Cost Optimizer. If you received this, email notifications are working correctly.",
        severity="info",
    )

    if success:
        print(f"Test email sent successfully to {args.test_email}")
    else:
        print("Failed to send test email. Check your SMTP configuration.")
        sys.exit(1)


def test_slack_notification(config):
    """Send a test Slack notification.

    Args:
        config: Application configuration
    """
    from src.notifications.slack_notifier import SlackNotifier

    webhook = config.get("notifications", {}).get("slack", {}).get("default_webhook")

    if not webhook:
        print("Slack not configured. Add webhook URL to config/config.yaml")
        sys.exit(1)

    notifier = SlackNotifier(webhook)
    success = notifier.test_connection()

    if success:
        print("Test Slack notification sent successfully!")
    else:
        print("Failed to send Slack notification. Check your webhook URL.")
        sys.exit(1)


def run_multi_account_analysis(args, config, credentials):
    """Run multi-account analysis.

    Args:
        args: Command line arguments
        config: Application configuration
        credentials: Credentials
    """
    from src.clients.organizations_client import OrganizationsClient
    from src.clients.multi_account_client import MultiAccountClient
    from src.output.multi_account_report import MultiAccountReportBuilder, MultiAccountExcelGenerator

    logger = logging.getLogger(__name__)
    logger.info("Running multi-account analysis...")

    org_config = config.get("organizations", {})
    aws_creds = credentials.get("aws", {})

    # Initialize organizations client
    org_client = OrganizationsClient(
        access_key_id=aws_creds.get("access_key_id"),
        secret_access_key=aws_creds.get("secret_access_key"),
        profile_name=aws_creds.get("profile_name"),
        default_role_name=org_config.get("role_name", "CostOptimizerRole"),
        session_duration=org_config.get("session_duration", 3600),
    )

    # Discover accounts
    explicit_accounts = org_config.get("accounts")
    accounts = org_client.discover_accounts(explicit_accounts)

    if not accounts:
        print("No accounts found. Configure accounts in config/config.yaml or enable AWS Organizations.")
        sys.exit(1)

    print(f"Found {len(accounts)} accounts to analyze")

    # Initialize multi-account client
    multi_client = MultiAccountClient(
        organizations_client=org_client,
        max_workers=5,
        region=args.region,
    )

    # Run analysis
    summary = multi_client.analyze_all_accounts(accounts)

    # Print summary
    print("\n" + "=" * 60)
    print("MULTI-ACCOUNT ANALYSIS SUMMARY")
    print("=" * 60)
    print(f"Total Accounts:     {summary.total_accounts}")
    print(f"Successful:         {summary.successful_accounts}")
    print(f"Failed:             {summary.failed_accounts}")
    print(f"Total Instances:    {summary.total_instances}")
    print(f"Total Monthly Cost: ${summary.total_current_monthly:,.2f}")
    print("-" * 60)

    for account_id, data in summary.by_account.items():
        status = "OK" if data.get("status") == "success" else "FAILED"
        print(f"  {data.get('name', account_id)[:20]:<20} [{status}]")
        if data.get("status") == "success":
            print(f"    Instances: {data.get('instance_count', 0)}, Cost: ${data.get('monthly_cost', 0):,.2f}")
        else:
            print(f"    Error: {data.get('error', 'Unknown')[:40]}")

    print("=" * 60)

    # Generate report if output specified
    if args.output:
        report_builder = MultiAccountReportBuilder()

        # Add account data to builder
        for result in summary.accounts:
            if result.success:
                # Build server reports for each instance
                server_reports = []
                # Note: Full analysis would be done here
                report_builder.add_account_data(result, server_reports)

        generator = MultiAccountExcelGenerator(args.output)
        generator.generate(report_builder)
        print(f"\nReport saved to: {args.output}")


def validate_multi_account_access(args, config, credentials):
    """Validate access to all configured accounts.

    Args:
        args: Command line arguments
        config: Application configuration
        credentials: Credentials
    """
    from src.clients.organizations_client import OrganizationsClient
    from src.clients.multi_account_client import MultiAccountClient

    logger = logging.getLogger(__name__)
    logger.info("Validating multi-account access...")

    org_config = config.get("organizations", {})
    aws_creds = credentials.get("aws", {})

    org_client = OrganizationsClient(
        access_key_id=aws_creds.get("access_key_id"),
        secret_access_key=aws_creds.get("secret_access_key"),
        profile_name=aws_creds.get("profile_name"),
        default_role_name=org_config.get("role_name", "CostOptimizerRole"),
    )

    # Discover accounts
    accounts = org_client.discover_accounts(org_config.get("accounts"))

    if not accounts:
        print("No accounts found.")
        return

    multi_client = MultiAccountClient(org_client)
    access_status = multi_client.validate_access(accounts)

    print("\nAccount Access Validation:")
    print("-" * 60)

    accessible = 0
    for account in accounts:
        status = access_status.get(account.account_id, False)
        icon = "OK" if status else "FAILED"
        print(f"  {account.name[:30]:<30} ({account.account_id}): {icon}")
        if status:
            accessible += 1

    print("-" * 60)
    print(f"Accessible: {accessible}/{len(accounts)} accounts")


def run_analysis(args):
    """Run the cost optimization analysis.

    Args:
        args: Command line arguments
    """
    logger = setup_logging("DEBUG" if args.verbose else "INFO")
    logger.info("Starting AWS Cost Optimization analysis")

    # Load configuration
    try:
        config = load_config(args.config)
        credentials = load_credentials(args.credentials)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    # Initialize clients
    aws_creds = credentials.get("aws", {})
    aws_client = AWSClient(
        access_key_id=aws_creds.get("access_key_id"),
        secret_access_key=aws_creds.get("secret_access_key"),
        region=args.region,
        profile_name=aws_creds.get("profile_name")
    )

    dynatrace_client = None
    cloudwatch_client = None

    if args.use_cloudwatch:
        cloudwatch_client = CloudWatchClient(
            access_key_id=aws_creds.get("access_key_id"),
            secret_access_key=aws_creds.get("secret_access_key"),
            region=args.region,
            profile_name=aws_creds.get("profile_name")
        )
    else:
        dt_creds = credentials.get("dynatrace", {})
        if dt_creds.get("environment_url") and dt_creds.get("api_token"):
            dynatrace_client = DynatraceClient(
                environment_url=dt_creds["environment_url"],
                api_token=dt_creds["api_token"]
            )

    # Test connections
    if args.dry_run:
        logger.info("Testing connections...")
        aws_ok = aws_client.test_connection()
        logger.info(f"AWS connection: {'OK' if aws_ok else 'FAILED'}")

        if dynatrace_client:
            dt_ok = dynatrace_client.test_connection()
            logger.info(f"Dynatrace connection: {'OK' if dt_ok else 'FAILED'}")

        if cloudwatch_client:
            cw_ok = cloudwatch_client.test_connection()
            logger.info(f"CloudWatch connection: {'OK' if cw_ok else 'FAILED'}")

        return

    # Get instances
    logger.info("Retrieving instances...")
    instances = get_instances(args, aws_client)
    logger.info(f"Found {len(instances)} instances to analyze")

    if not instances:
        logger.warning("No instances found. Check your input or tag filters.")
        sys.exit(0)

    # Get metrics
    logger.info("Retrieving metrics...")
    metrics_data = get_metrics(
        instances, args,
        dynatrace_client=dynatrace_client,
        cloudwatch_client=cloudwatch_client
    )

    # Initialize analyzers
    metrics_analyzer = MetricsAnalyzer(config.get("analysis", {}))
    contention_detector = ContentionDetector()
    rightsizing_engine = RightsizingEngine()
    spend_calculator = CurrentSpendCalculator(aws_client, region=args.region)
    savings_projector = SavingsProjector(spend_calculator)

    # Build report
    logger.info("Analyzing data...")
    report_builder = ReportDataBuilder()

    for instance in instances:
        instance_id = instance.get("instance_id")
        if not instance_id:
            continue

        # Get instance type info
        instance_type = instance.get("instance_type")
        if instance_type:
            instance_specs = aws_client.get_instance_type_info(instance_type)
        else:
            instance_specs = {}

        # Validate and analyze metrics
        instance_metrics = metrics_data.get(instance_id, {})
        validation = metrics_analyzer.validate_metrics(instance_metrics)

        if not validation["valid"]:
            logger.warning(f"Insufficient metrics for {instance_id}: {validation['warnings']}")
        elif validation["warnings"]:
            logger.debug(f"Metrics warnings for {instance_id}: {validation['warnings']}")

        server_metrics = metrics_analyzer.analyze_server(
            server_id=instance_id,
            metrics_data=instance_metrics,
            hostname=instance.get("name")
        )

        # Extract P95 values for contention detection and recommendations
        cpu_p95 = server_metrics.cpu.p95 if server_metrics.cpu else None
        memory_p95 = server_metrics.memory.p95 if server_metrics.memory else None

        # Detect contention - pass P95 values as fallback
        contention = contention_detector.analyze_server(
            server_id=instance_id,
            metrics_data=metrics_data.get(instance_id, {}),
            cpu_p95=cpu_p95,
            memory_p95=memory_p95
        )

        recommendation = rightsizing_engine.recommend(
            server_id=instance_id,
            current_instance_type=instance_type or "",
            cpu_p95=cpu_p95,
            memory_p95=memory_p95,
            has_contention=contention.has_contention,
            hostname=instance.get("name"),
            instance_specs=instance_specs
        )

        # Project savings
        projection = savings_projector.project_savings(recommendation)

        # Build server report
        server_report = report_builder.build_server_report(
            instance=instance,
            metrics=server_metrics,
            contention=contention,
            recommendation=recommendation,
            projection=projection
        )
        report_builder.add_server(server_report)

    # Generate Excel report
    logger.info(f"Generating report: {args.output}")
    generator = ExcelGenerator(args.output)
    output_path = generator.generate(report_builder)

    # Print summary
    summary = report_builder.build_summary()
    print("\n" + "=" * 60)
    print("AWS COST OPTIMIZATION SUMMARY")
    print("=" * 60)
    print(f"Servers Analyzed:      {summary['total_servers']}")
    print(f"Current Monthly Spend: ${summary['total_current_monthly']:,.2f}")
    print(f"Potential Savings:     ${summary['total_monthly_savings']:,.2f}/month")
    print(f"                       ${summary['total_yearly_savings']:,.2f}/year")
    print(f"Savings Percentage:    {summary['savings_percentage']:.1f}%")
    print("-" * 60)
    print(f"Oversized (downsize):  {summary['oversized_count']}")
    print(f"Right-sized:           {summary['right_sized_count']}")
    print(f"Undersized (upsize):   {summary['undersized_count']}")
    print(f"With Contention:       {summary['contention_count']}")
    print("=" * 60)
    print(f"\nReport saved to: {output_path}")


def launch_dashboard():
    """Launch the Streamlit dashboard."""
    import subprocess
    dashboard_path = Path(__file__).parent / "dashboard" / "app.py"

    if not dashboard_path.exists():
        print(f"Dashboard not found: {dashboard_path}")
        sys.exit(1)

    subprocess.run(["streamlit", "run", str(dashboard_path)])


def main():
    """Main entry point."""
    args = parse_args()

    # Set up logging early for all commands
    logger = setup_logging("DEBUG" if args.verbose else "INFO")

    # Load config and credentials for commands that need them
    try:
        config = load_config(args.config)
        credentials = load_credentials(args.credentials)
    except FileNotFoundError as e:
        # Some commands don't need config
        config = {}
        credentials = {}

    # Route to appropriate command
    if args.dashboard:
        launch_dashboard()
    elif args.detect_anomalies:
        run_anomaly_detection(args, config, credentials)
    elif args.daemon:
        run_scheduler_daemon(args, config, credentials)
    elif args.run_schedule:
        run_specific_schedule(args, config, credentials)
    elif args.list_schedules:
        list_schedules(config)
    elif args.test_email:
        test_email_notification(args, config, credentials)
    elif args.test_slack:
        test_slack_notification(config)
    elif args.multi_account:
        run_multi_account_analysis(args, config, credentials)
    elif args.validate_multi_account:
        validate_multi_account_access(args, config, credentials)
    else:
        run_analysis(args)


if __name__ == "__main__":
    main()

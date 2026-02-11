"""Historical cost retrieval for anomaly detection."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class HistoricalCostRetriever:
    """Retrieve historical cost data from AWS Cost Explorer.

    Provides methods to fetch daily costs by service for baseline
    calculation and anomaly detection.
    """

    # AWS service name mapping
    SERVICE_NAMES = {
        "EC2": "Amazon Elastic Compute Cloud - Compute",
        "RDS": "Amazon Relational Database Service",
        "Lambda": "AWS Lambda",
        "S3": "Amazon Simple Storage Service",
        "ElastiCache": "Amazon ElastiCache",
        "EBS": "Amazon Elastic Block Store",
        "ELB": "Elastic Load Balancing",
        "CloudWatch": "AmazonCloudWatch",
        "DynamoDB": "Amazon DynamoDB",
        "Redshift": "Amazon Redshift",
        "EKS": "Amazon Elastic Kubernetes Service",
        "ECS": "Amazon EC2 Container Service",
        "NAT Gateway": "EC2 - Other",
        "Data Transfer": "AWS Data Transfer",
    }

    def __init__(self, aws_client):
        """Initialize the retriever.

        Args:
            aws_client: Initialized AWSClient instance
        """
        self.aws_client = aws_client
        self.cost_explorer = aws_client.cost_explorer

    def get_daily_costs_by_service(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        services: Optional[List[str]] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get daily costs broken down by service.

        Args:
            start_date: Start of period (default: 30 days ago)
            end_date: End of period (default: today)
            services: Optional list of services to filter

        Returns:
            Dictionary mapping service name to list of {date, cost} records
        """
        if end_date is None:
            end_date = datetime.now(timezone.utc)
        if start_date is None:
            start_date = end_date - timedelta(days=30)

        try:
            response = self.cost_explorer.get_cost_and_usage(
                TimePeriod={
                    "Start": start_date.strftime("%Y-%m-%d"),
                    "End": end_date.strftime("%Y-%m-%d")
                },
                Granularity="DAILY",
                Metrics=["UnblendedCost"],
                GroupBy=[
                    {"Type": "DIMENSION", "Key": "SERVICE"}
                ]
            )

            costs_by_service: Dict[str, List[Dict[str, Any]]] = {}

            for result in response.get("ResultsByTime", []):
                date_str = result.get("TimePeriod", {}).get("Start")
                date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)

                for group in result.get("Groups", []):
                    service_name = group.get("Keys", [""])[0]
                    cost = float(group.get("Metrics", {}).get("UnblendedCost", {}).get("Amount", 0))

                    # Apply service filter if specified
                    if services:
                        # Check if service matches any of the requested services
                        service_key = self._normalize_service_name(service_name)
                        if service_key not in services and service_name not in services:
                            continue

                    if service_name not in costs_by_service:
                        costs_by_service[service_name] = []

                    costs_by_service[service_name].append({
                        "date": date,
                        "cost": cost,
                    })

            # Sort each service's data by date
            for service in costs_by_service:
                costs_by_service[service].sort(key=lambda x: x["date"])

            logger.info(f"Retrieved daily costs for {len(costs_by_service)} services")
            return costs_by_service

        except ClientError as e:
            logger.error(f"Failed to get daily costs: {e}")
            raise

    def get_costs_for_anomaly_detection(
        self,
        baseline_days: int = 30,
        detection_days: int = 7,
        services: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
        """Get costs formatted for anomaly detection.

        Retrieves historical data for baseline and recent data for detection,
        structured for the CostAnomalyDetector.

        Args:
            baseline_days: Number of days for baseline calculation
            detection_days: Number of recent days to check for anomalies
            services: Optional list of services to filter

        Returns:
            Dictionary mapping service -> {historical, current} data
        """
        now = datetime.now(timezone.utc)

        # Get baseline period (older data)
        baseline_end = now - timedelta(days=detection_days)
        baseline_start = baseline_end - timedelta(days=baseline_days)

        # Get detection period (recent data)
        detection_start = now - timedelta(days=detection_days)
        detection_end = now

        # Fetch both periods
        try:
            # Fetch all data in one request (baseline_start to detection_end)
            all_costs = self.get_daily_costs_by_service(
                start_date=baseline_start,
                end_date=detection_end,
                services=services
            )

            result: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}

            for service, costs in all_costs.items():
                historical = []
                current = []

                for record in costs:
                    if record["date"] < baseline_end:
                        historical.append(record)
                    else:
                        current.append(record)

                result[service] = {
                    "historical": historical,
                    "current": current,
                }

            logger.info(
                f"Prepared anomaly detection data: "
                f"{len(result)} services, baseline={baseline_days}d, detection={detection_days}d"
            )
            return result

        except Exception as e:
            logger.error(f"Failed to prepare anomaly detection data: {e}")
            raise

    def get_service_cost_trend(
        self,
        service: str,
        days: int = 90
    ) -> List[Dict[str, Any]]:
        """Get cost trend for a specific service.

        Args:
            service: Service name
            days: Number of days of history

        Returns:
            List of {date, cost} records
        """
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        all_costs = self.get_daily_costs_by_service(
            start_date=start_date,
            end_date=end_date,
            services=[service]
        )

        # Find matching service (may be full name or abbreviated)
        for svc_name, costs in all_costs.items():
            if service in svc_name or svc_name in service:
                return costs

        # Try normalized name
        full_name = self.SERVICE_NAMES.get(service, service)
        return all_costs.get(full_name, [])

    def get_total_daily_costs(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get total daily costs across all services.

        Args:
            start_date: Start of period
            end_date: End of period

        Returns:
            List of {date, cost} records
        """
        if end_date is None:
            end_date = datetime.now(timezone.utc)
        if start_date is None:
            start_date = end_date - timedelta(days=30)

        try:
            response = self.cost_explorer.get_cost_and_usage(
                TimePeriod={
                    "Start": start_date.strftime("%Y-%m-%d"),
                    "End": end_date.strftime("%Y-%m-%d")
                },
                Granularity="DAILY",
                Metrics=["UnblendedCost"],
            )

            costs = []
            for result in response.get("ResultsByTime", []):
                date_str = result.get("TimePeriod", {}).get("Start")
                date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                cost = float(result.get("Total", {}).get("UnblendedCost", {}).get("Amount", 0))

                costs.append({
                    "date": date,
                    "cost": cost,
                })

            costs.sort(key=lambda x: x["date"])
            logger.info(f"Retrieved {len(costs)} days of total costs")
            return costs

        except ClientError as e:
            logger.error(f"Failed to get total daily costs: {e}")
            raise

    def get_monthly_costs_by_service(
        self,
        months: int = 6
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get monthly costs broken down by service.

        Args:
            months: Number of months of history

        Returns:
            Dictionary mapping service name to list of {month, cost} records
        """
        end_date = datetime.now(timezone.utc).replace(day=1)
        start_date = (end_date - timedelta(days=months * 31)).replace(day=1)

        try:
            response = self.cost_explorer.get_cost_and_usage(
                TimePeriod={
                    "Start": start_date.strftime("%Y-%m-%d"),
                    "End": end_date.strftime("%Y-%m-%d")
                },
                Granularity="MONTHLY",
                Metrics=["UnblendedCost"],
                GroupBy=[
                    {"Type": "DIMENSION", "Key": "SERVICE"}
                ]
            )

            costs_by_service: Dict[str, List[Dict[str, Any]]] = {}

            for result in response.get("ResultsByTime", []):
                month_str = result.get("TimePeriod", {}).get("Start")
                month = datetime.strptime(month_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)

                for group in result.get("Groups", []):
                    service_name = group.get("Keys", [""])[0]
                    cost = float(group.get("Metrics", {}).get("UnblendedCost", {}).get("Amount", 0))

                    if service_name not in costs_by_service:
                        costs_by_service[service_name] = []

                    costs_by_service[service_name].append({
                        "month": month,
                        "cost": cost,
                    })

            # Sort by month
            for service in costs_by_service:
                costs_by_service[service].sort(key=lambda x: x["month"])

            logger.info(f"Retrieved monthly costs for {len(costs_by_service)} services")
            return costs_by_service

        except ClientError as e:
            logger.error(f"Failed to get monthly costs: {e}")
            raise

    def _normalize_service_name(self, full_name: str) -> str:
        """Normalize AWS service name to short form.

        Args:
            full_name: Full AWS service name

        Returns:
            Abbreviated service name
        """
        # Reverse lookup in SERVICE_NAMES
        for short, full in self.SERVICE_NAMES.items():
            if full in full_name or full_name in full:
                return short

        # Extract key part of name
        if "Elastic Compute Cloud" in full_name:
            return "EC2"
        if "Relational Database" in full_name:
            return "RDS"
        if "Lambda" in full_name:
            return "Lambda"
        if "Simple Storage" in full_name or "S3" in full_name:
            return "S3"

        return full_name

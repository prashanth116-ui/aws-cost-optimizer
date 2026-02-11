"""Cost anomaly detection for identifying unusual spending patterns."""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class CostAnomaly:
    """A detected cost anomaly event."""

    service: str
    anomaly_date: datetime
    actual_cost: float
    expected_cost: float
    deviation_amount: float
    deviation_percent: float
    std_dev_from_mean: float
    severity: str  # warning, critical
    anomaly_type: str  # spike, drop

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "service": self.service,
            "anomaly_date": self.anomaly_date.isoformat(),
            "actual_cost": round(self.actual_cost, 2),
            "expected_cost": round(self.expected_cost, 2),
            "deviation_amount": round(self.deviation_amount, 2),
            "deviation_percent": round(self.deviation_percent, 1),
            "std_dev_from_mean": round(self.std_dev_from_mean, 2),
            "severity": self.severity,
            "anomaly_type": self.anomaly_type,
        }


@dataclass
class ServiceBaseline:
    """Baseline statistics for a service's cost pattern."""

    service: str
    mean: float
    std_dev: float
    median: float
    p50: float
    p75: float
    p90: float
    p95: float
    min_cost: float
    max_cost: float
    data_points: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "service": self.service,
            "mean": round(self.mean, 2),
            "std_dev": round(self.std_dev, 2),
            "median": round(self.median, 2),
            "p50": round(self.p50, 2),
            "p75": round(self.p75, 2),
            "p90": round(self.p90, 2),
            "p95": round(self.p95, 2),
            "min_cost": round(self.min_cost, 2),
            "max_cost": round(self.max_cost, 2),
            "data_points": self.data_points,
        }


@dataclass
class AnomalySummary:
    """Summary of anomalies detected across all services."""

    total_anomalies: int
    critical_count: int
    warning_count: int
    spike_count: int
    drop_count: int
    total_excess_cost: float
    services_affected: List[str]
    anomalies: List[CostAnomaly]
    baselines: Dict[str, ServiceBaseline]
    detection_period_start: datetime
    detection_period_end: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_anomalies": self.total_anomalies,
            "critical_count": self.critical_count,
            "warning_count": self.warning_count,
            "spike_count": self.spike_count,
            "drop_count": self.drop_count,
            "total_excess_cost": round(self.total_excess_cost, 2),
            "services_affected": self.services_affected,
            "anomalies": [a.to_dict() for a in self.anomalies],
            "baselines": {k: v.to_dict() for k, v in self.baselines.items()},
            "detection_period_start": self.detection_period_start.isoformat(),
            "detection_period_end": self.detection_period_end.isoformat(),
        }


class CostAnomalyDetector:
    """Detect cost anomalies using statistical analysis.

    Detection methodology:
    - Build baseline from historical data (mean, std_dev, percentiles)
    - Detect spikes: current > baseline + N std_dev
    - Detect drops: current < baseline - N std_dev
    - Severity based on magnitude of deviation
    """

    DEFAULT_THRESHOLDS = {
        "warning": {"std_dev": 2.0, "percentage": 30},
        "critical": {"std_dev": 3.0, "percentage": 50},
    }

    DEFAULT_BASELINE_DAYS = 30
    MIN_DATA_POINTS = 7  # Minimum days of data for reliable baseline

    def __init__(
        self,
        thresholds: Optional[Dict[str, Dict[str, float]]] = None,
        baseline_days: int = 30
    ):
        """Initialize the detector.

        Args:
            thresholds: Custom thresholds for warning/critical detection
            baseline_days: Number of days to use for baseline calculation
        """
        self.thresholds = thresholds or self.DEFAULT_THRESHOLDS
        self.baseline_days = baseline_days

    def build_baseline(
        self,
        cost_data: List[Dict[str, Any]],
        service: str
    ) -> Optional[ServiceBaseline]:
        """Build a statistical baseline for a service's costs.

        Args:
            cost_data: List of {date, cost} dictionaries
            service: Service name

        Returns:
            ServiceBaseline or None if insufficient data
        """
        if not cost_data or len(cost_data) < self.MIN_DATA_POINTS:
            logger.warning(f"Insufficient data for baseline: {service} ({len(cost_data) if cost_data else 0} points)")
            return None

        costs = np.array([d.get("cost", 0) for d in cost_data])

        # Handle zero/negative values
        costs = np.maximum(costs, 0)

        return ServiceBaseline(
            service=service,
            mean=float(np.mean(costs)),
            std_dev=float(np.std(costs)),
            median=float(np.median(costs)),
            p50=float(np.percentile(costs, 50)),
            p75=float(np.percentile(costs, 75)),
            p90=float(np.percentile(costs, 90)),
            p95=float(np.percentile(costs, 95)),
            min_cost=float(np.min(costs)),
            max_cost=float(np.max(costs)),
            data_points=len(costs),
        )

    def detect_anomalies(
        self,
        current_cost: float,
        baseline: ServiceBaseline,
        date: datetime,
        service: str
    ) -> Optional[CostAnomaly]:
        """Detect if a cost value is anomalous.

        Args:
            current_cost: Current period cost
            baseline: Historical baseline for comparison
            date: Date of the cost
            service: Service name

        Returns:
            CostAnomaly if detected, None otherwise
        """
        if baseline.std_dev == 0:
            # No variance in historical data, use percentage-based detection
            if baseline.mean > 0:
                deviation_percent = ((current_cost - baseline.mean) / baseline.mean) * 100
            else:
                deviation_percent = 100 if current_cost > 0 else 0
            std_dev_from_mean = 0
        else:
            deviation_percent = ((current_cost - baseline.mean) / baseline.mean) * 100 if baseline.mean > 0 else 0
            std_dev_from_mean = (current_cost - baseline.mean) / baseline.std_dev

        deviation_amount = current_cost - baseline.mean

        # Determine anomaly type
        if std_dev_from_mean > 0:
            anomaly_type = "spike"
        else:
            anomaly_type = "drop"
            std_dev_from_mean = abs(std_dev_from_mean)
            deviation_percent = abs(deviation_percent)

        # Check thresholds
        critical_threshold = self.thresholds["critical"]
        warning_threshold = self.thresholds["warning"]

        severity = None
        if std_dev_from_mean >= critical_threshold["std_dev"] or deviation_percent >= critical_threshold["percentage"]:
            severity = "critical"
        elif std_dev_from_mean >= warning_threshold["std_dev"] or deviation_percent >= warning_threshold["percentage"]:
            severity = "warning"

        if severity is None:
            return None

        return CostAnomaly(
            service=service,
            anomaly_date=date,
            actual_cost=current_cost,
            expected_cost=baseline.mean,
            deviation_amount=deviation_amount,
            deviation_percent=deviation_percent if anomaly_type == "spike" else -deviation_percent,
            std_dev_from_mean=std_dev_from_mean if anomaly_type == "spike" else -std_dev_from_mean,
            severity=severity,
            anomaly_type=anomaly_type,
        )

    def analyze_service(
        self,
        historical_data: List[Dict[str, Any]],
        current_data: List[Dict[str, Any]],
        service: str
    ) -> List[CostAnomaly]:
        """Analyze a service for cost anomalies.

        Args:
            historical_data: Historical cost data for baseline
            current_data: Current period data to check for anomalies
            service: Service name

        Returns:
            List of detected anomalies
        """
        baseline = self.build_baseline(historical_data, service)
        if baseline is None:
            return []

        anomalies = []
        for data_point in current_data:
            date = data_point.get("date")
            cost = data_point.get("cost", 0)

            if isinstance(date, str):
                date = datetime.fromisoformat(date.replace("Z", "+00:00"))

            anomaly = self.detect_anomalies(cost, baseline, date, service)
            if anomaly:
                anomalies.append(anomaly)

        return anomalies

    def analyze_all_services(
        self,
        cost_data_by_service: Dict[str, Dict[str, List[Dict[str, Any]]]],
        detection_start: Optional[datetime] = None,
        detection_end: Optional[datetime] = None
    ) -> AnomalySummary:
        """Analyze all services for cost anomalies.

        Args:
            cost_data_by_service: Dict with service -> {historical, current} data
            detection_start: Start of detection period
            detection_end: End of detection period

        Returns:
            AnomalySummary with all detected anomalies
        """
        all_anomalies: List[CostAnomaly] = []
        baselines: Dict[str, ServiceBaseline] = {}

        if detection_end is None:
            detection_end = datetime.now(timezone.utc)
        if detection_start is None:
            detection_start = detection_end - timedelta(days=7)

        for service, data in cost_data_by_service.items():
            historical = data.get("historical", [])
            current = data.get("current", [])

            # Build baseline
            baseline = self.build_baseline(historical, service)
            if baseline:
                baselines[service] = baseline

            # Detect anomalies
            anomalies = self.analyze_service(historical, current, service)
            all_anomalies.extend(anomalies)

        # Sort anomalies by severity and date
        all_anomalies.sort(key=lambda x: (
            0 if x.severity == "critical" else 1,
            -abs(x.deviation_percent)
        ))

        # Calculate summary stats
        critical_count = len([a for a in all_anomalies if a.severity == "critical"])
        warning_count = len([a for a in all_anomalies if a.severity == "warning"])
        spike_count = len([a for a in all_anomalies if a.anomaly_type == "spike"])
        drop_count = len([a for a in all_anomalies if a.anomaly_type == "drop"])

        total_excess = sum(
            a.deviation_amount for a in all_anomalies
            if a.anomaly_type == "spike" and a.deviation_amount > 0
        )

        services_affected = list(set(a.service for a in all_anomalies))

        return AnomalySummary(
            total_anomalies=len(all_anomalies),
            critical_count=critical_count,
            warning_count=warning_count,
            spike_count=spike_count,
            drop_count=drop_count,
            total_excess_cost=total_excess,
            services_affected=services_affected,
            anomalies=all_anomalies,
            baselines=baselines,
            detection_period_start=detection_start,
            detection_period_end=detection_end,
        )

    def get_anomaly_report(self, summary: AnomalySummary) -> Dict[str, Any]:
        """Generate a high-level anomaly report.

        Args:
            summary: AnomalySummary object

        Returns:
            Report dictionary
        """
        return {
            "total_anomalies": summary.total_anomalies,
            "critical_anomalies": summary.critical_count,
            "warning_anomalies": summary.warning_count,
            "total_excess_cost": round(summary.total_excess_cost, 2),
            "services_affected": len(summary.services_affected),
            "detection_period": {
                "start": summary.detection_period_start.isoformat(),
                "end": summary.detection_period_end.isoformat(),
            },
            "top_anomalies": [
                {
                    "service": a.service,
                    "date": a.anomaly_date.isoformat(),
                    "severity": a.severity,
                    "type": a.anomaly_type,
                    "actual_cost": round(a.actual_cost, 2),
                    "expected_cost": round(a.expected_cost, 2),
                    "deviation_percent": round(a.deviation_percent, 1),
                }
                for a in summary.anomalies[:10]
            ],
            "service_baselines": {
                service: {
                    "mean": round(baseline.mean, 2),
                    "std_dev": round(baseline.std_dev, 2),
                    "p95": round(baseline.p95, 2),
                }
                for service, baseline in summary.baselines.items()
            },
        }

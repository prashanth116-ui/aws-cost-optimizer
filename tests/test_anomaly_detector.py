"""Tests for the cost anomaly detector."""

import pytest
from datetime import datetime, timedelta, timezone

from src.analysis.anomaly_detector import (
    CostAnomaly,
    CostAnomalyDetector,
    ServiceBaseline,
    AnomalySummary,
)


class TestServiceBaseline:
    """Tests for ServiceBaseline dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        baseline = ServiceBaseline(
            service="EC2",
            mean=100.555,
            std_dev=10.333,
            median=98.0,
            p50=98.0,
            p75=108.0,
            p90=115.0,
            p95=120.0,
            min_cost=80.0,
            max_cost=130.0,
            data_points=30,
        )

        result = baseline.to_dict()

        assert result["service"] == "EC2"
        assert result["mean"] == 100.56  # Rounded to 2 decimals
        assert result["std_dev"] == 10.33
        assert result["data_points"] == 30


class TestCostAnomaly:
    """Tests for CostAnomaly dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        now = datetime.now(timezone.utc)
        anomaly = CostAnomaly(
            service="EC2",
            anomaly_date=now,
            actual_cost=150.555,
            expected_cost=100.333,
            deviation_amount=50.222,
            deviation_percent=50.111,
            std_dev_from_mean=5.0,
            severity="critical",
            anomaly_type="spike",
        )

        result = anomaly.to_dict()

        assert result["service"] == "EC2"
        assert result["actual_cost"] == 150.56  # Rounded
        assert result["expected_cost"] == 100.33
        assert result["deviation_amount"] == 50.22
        assert result["deviation_percent"] == 50.1  # Rounded to 1 decimal
        assert result["severity"] == "critical"
        assert result["anomaly_type"] == "spike"


class TestCostAnomalyDetector:
    """Tests for CostAnomalyDetector."""

    def test_init_default_thresholds(self):
        """Test initialization with default thresholds."""
        detector = CostAnomalyDetector()

        assert detector.thresholds["warning"]["std_dev"] == 2.0
        assert detector.thresholds["critical"]["std_dev"] == 3.0
        assert detector.baseline_days == 30

    def test_init_custom_thresholds(self):
        """Test initialization with custom thresholds."""
        custom = {
            "warning": {"std_dev": 1.5, "percentage": 25},
            "critical": {"std_dev": 2.5, "percentage": 40},
        }
        detector = CostAnomalyDetector(thresholds=custom, baseline_days=14)

        assert detector.thresholds["warning"]["std_dev"] == 1.5
        assert detector.baseline_days == 14

    def test_build_baseline_normal_data(self):
        """Test baseline building with normal data."""
        detector = CostAnomalyDetector()

        cost_data = [
            {"date": datetime.now(timezone.utc) - timedelta(days=i), "cost": 100 + i}
            for i in range(30)
        ]

        baseline = detector.build_baseline(cost_data, "EC2")

        assert baseline is not None
        assert baseline.service == "EC2"
        assert baseline.data_points == 30
        assert baseline.mean > 0
        assert baseline.std_dev > 0
        assert baseline.min_cost <= baseline.mean <= baseline.max_cost

    def test_build_baseline_insufficient_data(self):
        """Test baseline building with insufficient data."""
        detector = CostAnomalyDetector()

        cost_data = [
            {"date": datetime.now(timezone.utc) - timedelta(days=i), "cost": 100}
            for i in range(5)  # Less than MIN_DATA_POINTS
        ]

        baseline = detector.build_baseline(cost_data, "EC2")

        assert baseline is None

    def test_build_baseline_empty_data(self):
        """Test baseline building with empty data."""
        detector = CostAnomalyDetector()

        baseline = detector.build_baseline([], "EC2")

        assert baseline is None

    def test_detect_anomalies_no_anomaly(self):
        """Test detection with normal cost value."""
        detector = CostAnomalyDetector()

        baseline = ServiceBaseline(
            service="EC2",
            mean=100.0,
            std_dev=10.0,
            median=100.0,
            p50=100.0,
            p75=108.0,
            p90=115.0,
            p95=120.0,
            min_cost=80.0,
            max_cost=120.0,
            data_points=30,
        )

        # Cost within normal range (1 std dev from mean)
        anomaly = detector.detect_anomalies(
            current_cost=110.0,  # 1 std dev above mean
            baseline=baseline,
            date=datetime.now(timezone.utc),
            service="EC2"
        )

        assert anomaly is None

    def test_detect_anomalies_warning_spike(self):
        """Test detection of warning-level spike."""
        detector = CostAnomalyDetector()

        baseline = ServiceBaseline(
            service="EC2",
            mean=100.0,
            std_dev=10.0,
            median=100.0,
            p50=100.0,
            p75=108.0,
            p90=115.0,
            p95=120.0,
            min_cost=80.0,
            max_cost=120.0,
            data_points=30,
        )

        # Cost 2.5 std devs above mean (warning threshold)
        anomaly = detector.detect_anomalies(
            current_cost=125.0,  # 2.5 std devs
            baseline=baseline,
            date=datetime.now(timezone.utc),
            service="EC2"
        )

        assert anomaly is not None
        assert anomaly.severity == "warning"
        assert anomaly.anomaly_type == "spike"
        assert anomaly.deviation_amount == 25.0

    def test_detect_anomalies_critical_spike(self):
        """Test detection of critical-level spike."""
        detector = CostAnomalyDetector()

        baseline = ServiceBaseline(
            service="EC2",
            mean=100.0,
            std_dev=10.0,
            median=100.0,
            p50=100.0,
            p75=108.0,
            p90=115.0,
            p95=120.0,
            min_cost=80.0,
            max_cost=120.0,
            data_points=30,
        )

        # Cost 4 std devs above mean (critical threshold)
        anomaly = detector.detect_anomalies(
            current_cost=140.0,  # 4 std devs
            baseline=baseline,
            date=datetime.now(timezone.utc),
            service="EC2"
        )

        assert anomaly is not None
        assert anomaly.severity == "critical"
        assert anomaly.anomaly_type == "spike"

    def test_detect_anomalies_drop(self):
        """Test detection of cost drop anomaly."""
        detector = CostAnomalyDetector()

        baseline = ServiceBaseline(
            service="EC2",
            mean=100.0,
            std_dev=10.0,
            median=100.0,
            p50=100.0,
            p75=108.0,
            p90=115.0,
            p95=120.0,
            min_cost=80.0,
            max_cost=120.0,
            data_points=30,
        )

        # Cost 3 std devs below mean
        anomaly = detector.detect_anomalies(
            current_cost=70.0,  # 3 std devs below
            baseline=baseline,
            date=datetime.now(timezone.utc),
            service="EC2"
        )

        assert anomaly is not None
        assert anomaly.anomaly_type == "drop"
        assert anomaly.deviation_percent < 0

    def test_detect_anomalies_percentage_threshold(self):
        """Test detection using percentage threshold."""
        detector = CostAnomalyDetector()

        baseline = ServiceBaseline(
            service="EC2",
            mean=100.0,
            std_dev=5.0,  # Low variance
            median=100.0,
            p50=100.0,
            p75=104.0,
            p90=107.0,
            p95=109.0,
            min_cost=90.0,
            max_cost=110.0,
            data_points=30,
        )

        # Cost 40% above mean (triggers warning via percentage threshold)
        anomaly = detector.detect_anomalies(
            current_cost=140.0,  # 40% increase
            baseline=baseline,
            date=datetime.now(timezone.utc),
            service="EC2"
        )

        assert anomaly is not None
        assert anomaly.deviation_percent >= 30  # Warning percentage threshold

    def test_analyze_service(self):
        """Test analyzing a full service."""
        detector = CostAnomalyDetector()

        now = datetime.now(timezone.utc)

        # Historical data with consistent costs
        historical = [
            {"date": now - timedelta(days=i + 7), "cost": 100 + (i % 5)}
            for i in range(30)
        ]

        # Current data with one anomaly
        current = [
            {"date": now - timedelta(days=5), "cost": 105},
            {"date": now - timedelta(days=4), "cost": 102},
            {"date": now - timedelta(days=3), "cost": 103},
            {"date": now - timedelta(days=2), "cost": 200},  # Anomaly
            {"date": now - timedelta(days=1), "cost": 104},
        ]

        anomalies = detector.analyze_service(historical, current, "EC2")

        assert len(anomalies) >= 1
        # The 200 cost should be detected as anomaly
        spike_anomalies = [a for a in anomalies if a.actual_cost > 150]
        assert len(spike_anomalies) >= 1

    def test_analyze_all_services(self):
        """Test analyzing multiple services."""
        detector = CostAnomalyDetector()

        now = datetime.now(timezone.utc)

        cost_data = {
            "EC2": {
                "historical": [
                    {"date": now - timedelta(days=i + 7), "cost": 100}
                    for i in range(30)
                ],
                "current": [
                    {"date": now - timedelta(days=1), "cost": 200},  # Anomaly
                ],
            },
            "RDS": {
                "historical": [
                    {"date": now - timedelta(days=i + 7), "cost": 50}
                    for i in range(30)
                ],
                "current": [
                    {"date": now - timedelta(days=1), "cost": 55},  # Normal
                ],
            },
        }

        summary = detector.analyze_all_services(cost_data)

        assert isinstance(summary, AnomalySummary)
        assert summary.total_anomalies >= 1
        assert "EC2" in summary.baselines
        assert "RDS" in summary.baselines
        assert summary.detection_period_start is not None
        assert summary.detection_period_end is not None

    def test_analyze_all_services_no_anomalies(self):
        """Test when no anomalies are found."""
        detector = CostAnomalyDetector()

        now = datetime.now(timezone.utc)

        cost_data = {
            "EC2": {
                "historical": [
                    {"date": now - timedelta(days=i + 7), "cost": 100}
                    for i in range(30)
                ],
                "current": [
                    {"date": now - timedelta(days=1), "cost": 102},  # Normal
                ],
            },
        }

        summary = detector.analyze_all_services(cost_data)

        assert summary.total_anomalies == 0
        assert summary.critical_count == 0
        assert summary.warning_count == 0
        assert summary.total_excess_cost == 0

    def test_get_anomaly_report(self):
        """Test report generation."""
        detector = CostAnomalyDetector()

        now = datetime.now(timezone.utc)

        anomalies = [
            CostAnomaly(
                service="EC2",
                anomaly_date=now,
                actual_cost=200.0,
                expected_cost=100.0,
                deviation_amount=100.0,
                deviation_percent=100.0,
                std_dev_from_mean=5.0,
                severity="critical",
                anomaly_type="spike",
            ),
        ]

        summary = AnomalySummary(
            total_anomalies=1,
            critical_count=1,
            warning_count=0,
            spike_count=1,
            drop_count=0,
            total_excess_cost=100.0,
            services_affected=["EC2"],
            anomalies=anomalies,
            baselines={},
            detection_period_start=now - timedelta(days=7),
            detection_period_end=now,
        )

        report = detector.get_anomaly_report(summary)

        assert report["total_anomalies"] == 1
        assert report["critical_anomalies"] == 1
        assert report["total_excess_cost"] == 100.0
        assert report["services_affected"] == 1
        assert len(report["top_anomalies"]) == 1


class TestIntegration:
    """Integration tests for anomaly detection pipeline."""

    def test_full_detection_pipeline(self):
        """Test the complete anomaly detection workflow."""
        detector = CostAnomalyDetector(baseline_days=14)

        now = datetime.now(timezone.utc)

        # Simulate realistic cost data
        cost_data = {
            "Amazon Elastic Compute Cloud - Compute": {
                "historical": [
                    {
                        "date": now - timedelta(days=i + 7),
                        "cost": 1000 + (50 * (i % 7))  # Weekly pattern
                    }
                    for i in range(30)
                ],
                "current": [
                    {"date": now - timedelta(days=3), "cost": 1050},
                    {"date": now - timedelta(days=2), "cost": 2500},  # Spike
                    {"date": now - timedelta(days=1), "cost": 1100},
                ],
            },
            "Amazon Relational Database Service": {
                "historical": [
                    {
                        "date": now - timedelta(days=i + 7),
                        "cost": 500 + (10 * (i % 3))
                    }
                    for i in range(30)
                ],
                "current": [
                    {"date": now - timedelta(days=3), "cost": 510},
                    {"date": now - timedelta(days=2), "cost": 505},
                    {"date": now - timedelta(days=1), "cost": 520},
                ],
            },
        }

        summary = detector.analyze_all_services(cost_data)

        # Should detect the EC2 spike
        assert summary.total_anomalies >= 1
        assert summary.spike_count >= 1

        # Check baselines were built
        assert len(summary.baselines) == 2

        # Generate report
        report = detector.get_anomaly_report(summary)
        assert "top_anomalies" in report
        assert "service_baselines" in report

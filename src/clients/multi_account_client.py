"""Multi-account orchestration client for cross-account analysis."""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple

import boto3

from .organizations_client import OrganizationsClient, AWSAccount
from .aws_client import AWSClient

logger = logging.getLogger(__name__)


@dataclass
class AccountAnalysisResult:
    """Results from analyzing a single account."""

    account_id: str
    account_name: str
    success: bool
    instances: List[Dict[str, Any]] = field(default_factory=list)
    costs: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    analysis_time: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "account_id": self.account_id,
            "account_name": self.account_name,
            "success": self.success,
            "instance_count": len(self.instances),
            "instances": self.instances,
            "costs": self.costs,
            "error": self.error,
            "analysis_time": round(self.analysis_time, 2),
        }


@dataclass
class MultiAccountSummary:
    """Summary of multi-account analysis."""

    total_accounts: int
    successful_accounts: int
    failed_accounts: int
    total_instances: int
    total_current_monthly: float
    total_potential_savings: float
    accounts: List[AccountAnalysisResult]
    by_account: Dict[str, Dict[str, Any]]
    analysis_start: datetime
    analysis_end: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_accounts": self.total_accounts,
            "successful_accounts": self.successful_accounts,
            "failed_accounts": self.failed_accounts,
            "total_instances": self.total_instances,
            "total_current_monthly": round(self.total_current_monthly, 2),
            "total_potential_savings": round(self.total_potential_savings, 2),
            "by_account": self.by_account,
            "analysis_duration_seconds": (self.analysis_end - self.analysis_start).total_seconds(),
        }


class MultiAccountClient:
    """Orchestrator for cross-account cost analysis.

    Coordinates analysis across multiple AWS accounts using
    role assumption and parallel execution.
    """

    def __init__(
        self,
        organizations_client: OrganizationsClient,
        max_workers: int = 5,
        region: str = "us-east-1"
    ):
        """Initialize the multi-account client.

        Args:
            organizations_client: OrganizationsClient for role assumption
            max_workers: Maximum parallel account analyses
            region: Default AWS region for analysis
        """
        self.org_client = organizations_client
        self.max_workers = max_workers
        self.region = region

    def get_client_for_account(
        self,
        account: AWSAccount
    ) -> Optional[AWSClient]:
        """Get an AWSClient for a specific account.

        Args:
            account: Account to get client for

        Returns:
            AWSClient or None if role assumption fails
        """
        try:
            session = self.org_client.create_session_for_account(
                account_id=account.account_id,
                role_name=account.role_name,
            )

            # Create AWSClient from session credentials
            credentials = session.get_credentials()

            return AWSClient(
                access_key_id=credentials.access_key,
                secret_access_key=credentials.secret_key,
                region=self.region,
            )

        except Exception as e:
            logger.error(f"Failed to get client for account {account.account_id}: {e}")
            return None

    def analyze_account(
        self,
        account: AWSAccount,
        analyzer_func: Optional[Callable] = None
    ) -> AccountAnalysisResult:
        """Analyze a single account.

        Args:
            account: Account to analyze
            analyzer_func: Optional custom analyzer function

        Returns:
            AccountAnalysisResult with analysis results
        """
        import time
        start_time = time.time()

        result = AccountAnalysisResult(
            account_id=account.account_id,
            account_name=account.name,
            success=False,
        )

        try:
            client = self.get_client_for_account(account)
            if not client:
                result.error = "Failed to assume role"
                return result

            # Get instances
            instances = client.get_instances()
            result.instances = instances

            # Get costs
            if instances:
                costs = {
                    "instance_count": len(instances),
                    "total_monthly": 0.0,
                }

                # Get instance costs
                for instance in instances:
                    instance_id = instance.get("instance_id")
                    if instance_id:
                        cost_data = client.get_instance_cost(instance_id)
                        costs["total_monthly"] += cost_data.get("monthly_estimate", 0)

                result.costs = costs

            # Run custom analyzer if provided
            if analyzer_func:
                analyzer_func(account, client, result)

            result.success = True
            result.analysis_time = time.time() - start_time

            logger.info(
                f"Analyzed account {account.account_id}: "
                f"{len(instances)} instances"
            )

        except Exception as e:
            result.error = str(e)
            result.analysis_time = time.time() - start_time
            logger.error(f"Failed to analyze account {account.account_id}: {e}")

        return result

    def analyze_all_accounts(
        self,
        accounts: Optional[List[AWSAccount]] = None,
        analyzer_func: Optional[Callable] = None
    ) -> MultiAccountSummary:
        """Analyze all accounts in parallel.

        Args:
            accounts: List of accounts to analyze (auto-discover if None)
            analyzer_func: Optional custom analyzer function

        Returns:
            MultiAccountSummary with aggregated results
        """
        analysis_start = datetime.now(timezone.utc)

        # Discover accounts if not provided
        if accounts is None:
            accounts = self.org_client.list_accounts()

        if not accounts:
            logger.warning("No accounts to analyze")
            return MultiAccountSummary(
                total_accounts=0,
                successful_accounts=0,
                failed_accounts=0,
                total_instances=0,
                total_current_monthly=0.0,
                total_potential_savings=0.0,
                accounts=[],
                by_account={},
                analysis_start=analysis_start,
                analysis_end=datetime.now(timezone.utc),
            )

        results: List[AccountAnalysisResult] = []

        # Analyze accounts in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self.analyze_account, account, analyzer_func): account
                for account in accounts
            }

            for future in as_completed(futures):
                account = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Unexpected error analyzing {account.account_id}: {e}")
                    results.append(AccountAnalysisResult(
                        account_id=account.account_id,
                        account_name=account.name,
                        success=False,
                        error=str(e),
                    ))

        analysis_end = datetime.now(timezone.utc)

        # Aggregate results
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        total_instances = sum(len(r.instances) for r in successful)
        total_monthly = sum(r.costs.get("total_monthly", 0) for r in successful)

        by_account = {
            r.account_id: {
                "name": r.account_name,
                "instance_count": len(r.instances),
                "monthly_cost": round(r.costs.get("total_monthly", 0), 2),
                "status": "success" if r.success else "failed",
                "error": r.error,
            }
            for r in results
        }

        summary = MultiAccountSummary(
            total_accounts=len(accounts),
            successful_accounts=len(successful),
            failed_accounts=len(failed),
            total_instances=total_instances,
            total_current_monthly=total_monthly,
            total_potential_savings=0.0,  # Calculated by analyzer
            accounts=results,
            by_account=by_account,
            analysis_start=analysis_start,
            analysis_end=analysis_end,
        )

        logger.info(
            f"Multi-account analysis complete: "
            f"{summary.successful_accounts}/{summary.total_accounts} accounts, "
            f"{summary.total_instances} instances"
        )

        return summary

    def get_aggregated_instances(
        self,
        summary: MultiAccountSummary
    ) -> List[Dict[str, Any]]:
        """Get all instances across accounts with account info.

        Args:
            summary: MultiAccountSummary from analyze_all_accounts

        Returns:
            List of instances with account_id and account_name added
        """
        all_instances = []

        for result in summary.accounts:
            if result.success:
                for instance in result.instances:
                    instance_with_account = instance.copy()
                    instance_with_account["account_id"] = result.account_id
                    instance_with_account["account_name"] = result.account_name
                    all_instances.append(instance_with_account)

        return all_instances

    def get_costs_by_account(
        self,
        summary: MultiAccountSummary
    ) -> Dict[str, Dict[str, Any]]:
        """Get cost breakdown by account.

        Args:
            summary: MultiAccountSummary from analyze_all_accounts

        Returns:
            Dictionary mapping account_id to cost data
        """
        costs = {}

        for result in summary.accounts:
            if result.success:
                costs[result.account_id] = {
                    "name": result.account_name,
                    "instance_count": len(result.instances),
                    "monthly_cost": result.costs.get("total_monthly", 0),
                    "percentage": 0.0,  # Calculated below
                }

        # Calculate percentages
        total = sum(c["monthly_cost"] for c in costs.values())
        if total > 0:
            for account_id in costs:
                costs[account_id]["percentage"] = round(
                    (costs[account_id]["monthly_cost"] / total) * 100, 1
                )

        return costs

    def validate_access(
        self,
        accounts: Optional[List[AWSAccount]] = None
    ) -> Dict[str, bool]:
        """Validate access to all accounts.

        Args:
            accounts: List of accounts to validate

        Returns:
            Dictionary mapping account_id to access status
        """
        if accounts is None:
            accounts = self.org_client.list_accounts()

        access_status = {}

        for account in accounts:
            access_status[account.account_id] = self.org_client.test_role_assumption(
                account.account_id,
                account.role_name
            )

        accessible = sum(1 for v in access_status.values() if v)
        logger.info(
            f"Access validation: {accessible}/{len(accounts)} accounts accessible"
        )

        return access_status

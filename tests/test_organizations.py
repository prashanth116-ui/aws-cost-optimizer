"""Tests for the organizations and multi-account modules."""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from src.clients.organizations_client import (
    OrganizationsClient,
    AWSAccount,
    AssumedCredentials,
)
from src.clients.multi_account_client import (
    MultiAccountClient,
    AccountAnalysisResult,
    MultiAccountSummary,
)


class TestAWSAccount:
    """Tests for AWSAccount dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        account = AWSAccount(
            account_id="123456789012",
            name="Production",
            email="prod@example.com",
            status="ACTIVE",
            role_name="CustomRole",
        )

        result = account.to_dict()

        assert result["account_id"] == "123456789012"
        assert result["name"] == "Production"
        assert result["email"] == "prod@example.com"
        assert result["status"] == "ACTIVE"
        assert result["role_name"] == "CustomRole"

    def test_default_values(self):
        """Test default values."""
        account = AWSAccount(
            account_id="123456789012",
            name="Test",
        )

        assert account.email is None
        assert account.status == "ACTIVE"
        assert account.role_name is None


class TestAssumedCredentials:
    """Tests for AssumedCredentials dataclass."""

    def test_is_expired_false(self):
        """Test credentials not expired."""
        creds = AssumedCredentials(
            access_key_id="AKIA...",
            secret_access_key="secret",
            session_token="token",
            expiration=datetime.now(timezone.utc) + timedelta(hours=1),
            account_id="123456789012",
            role_name="TestRole",
        )

        assert creds.is_expired is False

    def test_is_expired_true(self):
        """Test credentials expired."""
        creds = AssumedCredentials(
            access_key_id="AKIA...",
            secret_access_key="secret",
            session_token="token",
            expiration=datetime.now(timezone.utc) - timedelta(hours=1),
            account_id="123456789012",
            role_name="TestRole",
        )

        assert creds.is_expired is True


class TestOrganizationsClient:
    """Tests for OrganizationsClient."""

    @patch("src.clients.organizations_client.boto3.Session")
    def test_init(self, mock_session):
        """Test initialization."""
        client = OrganizationsClient(
            access_key_id="AKIA...",
            secret_access_key="secret",
            default_role_name="CustomRole",
            session_duration=1800,
        )

        assert client.default_role_name == "CustomRole"
        assert client.session_duration == 1800

    @patch("src.clients.organizations_client.boto3.Session")
    def test_init_max_session_duration(self, mock_session):
        """Test session duration capped at 3600."""
        client = OrganizationsClient(session_duration=7200)

        assert client.session_duration == 3600

    @patch("src.clients.organizations_client.boto3.Session")
    def test_get_current_account(self, mock_session):
        """Test getting current account ID."""
        mock_sts = MagicMock()
        mock_sts.get_caller_identity.return_value = {"Account": "123456789012"}
        mock_session.return_value.client.return_value = mock_sts

        client = OrganizationsClient()
        result = client.get_current_account()

        assert result == "123456789012"

    @patch("src.clients.organizations_client.boto3.Session")
    def test_list_accounts(self, mock_session):
        """Test listing accounts."""
        mock_org = MagicMock()
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [
            {
                "Accounts": [
                    {"Id": "111111111111", "Name": "Account1", "Status": "ACTIVE"},
                    {"Id": "222222222222", "Name": "Account2", "Status": "ACTIVE"},
                ]
            }
        ]
        mock_org.get_paginator.return_value = mock_paginator
        mock_session.return_value.client.return_value = mock_org

        client = OrganizationsClient()
        client.organizations = mock_org

        accounts = client.list_accounts()

        assert len(accounts) == 2
        assert accounts[0].account_id == "111111111111"
        assert accounts[1].name == "Account2"

    @patch("src.clients.organizations_client.boto3.Session")
    def test_assume_role(self, mock_session):
        """Test role assumption."""
        mock_sts = MagicMock()
        mock_sts.assume_role.return_value = {
            "Credentials": {
                "AccessKeyId": "AKIA...",
                "SecretAccessKey": "secret",
                "SessionToken": "token",
                "Expiration": datetime.now(timezone.utc) + timedelta(hours=1),
            }
        }
        mock_session.return_value.client.return_value = mock_sts

        client = OrganizationsClient()
        client.sts = mock_sts

        creds = client.assume_role("123456789012", "TestRole")

        assert creds.access_key_id == "AKIA..."
        assert creds.account_id == "123456789012"
        assert creds.role_name == "TestRole"

    @patch("src.clients.organizations_client.boto3.Session")
    def test_assume_role_cached(self, mock_session):
        """Test cached credentials are returned."""
        mock_sts = MagicMock()
        mock_sts.assume_role.return_value = {
            "Credentials": {
                "AccessKeyId": "AKIA...",
                "SecretAccessKey": "secret",
                "SessionToken": "token",
                "Expiration": datetime.now(timezone.utc) + timedelta(hours=1),
            }
        }
        mock_session.return_value.client.return_value = mock_sts

        client = OrganizationsClient()
        client.sts = mock_sts

        # First call
        creds1 = client.assume_role("123456789012", "TestRole")

        # Second call should use cache
        creds2 = client.assume_role("123456789012", "TestRole")

        # Should only call assume_role once
        assert mock_sts.assume_role.call_count == 1
        assert creds1 == creds2

    @patch("src.clients.organizations_client.boto3.Session")
    def test_get_accounts_from_config(self, mock_session):
        """Test loading accounts from config."""
        client = OrganizationsClient()

        config = [
            {"account_id": "111111111111", "name": "Prod", "role_name": "CustomRole"},
            {"account_id": "222222222222", "name": "Dev"},
        ]

        accounts = client.get_accounts_from_config(config)

        assert len(accounts) == 2
        assert accounts[0].role_name == "CustomRole"
        assert accounts[1].role_name is None

    @patch("src.clients.organizations_client.boto3.Session")
    def test_discover_accounts_explicit(self, mock_session):
        """Test discover with explicit config."""
        client = OrganizationsClient()

        config = [{"account_id": "111111111111", "name": "Test"}]

        accounts = client.discover_accounts(explicit_accounts=config)

        assert len(accounts) == 1

    @patch("src.clients.organizations_client.boto3.Session")
    def test_clear_credential_cache(self, mock_session):
        """Test clearing credential cache."""
        client = OrganizationsClient()
        client._credential_cache["test"] = AssumedCredentials(
            access_key_id="AKIA...",
            secret_access_key="secret",
            session_token="token",
            expiration=datetime.now(timezone.utc),
            account_id="123",
            role_name="Test",
        )

        client.clear_credential_cache()

        assert len(client._credential_cache) == 0


class TestMultiAccountClient:
    """Tests for MultiAccountClient."""

    def test_init(self):
        """Test initialization."""
        mock_org = MagicMock()
        client = MultiAccountClient(
            organizations_client=mock_org,
            max_workers=3,
            region="us-west-2",
        )

        assert client.max_workers == 3
        assert client.region == "us-west-2"

    def test_analyze_account_success(self):
        """Test successful account analysis."""
        mock_org = MagicMock()
        mock_session = MagicMock()
        mock_credentials = MagicMock()
        mock_credentials.access_key = "AKIA..."
        mock_credentials.secret_key = "secret"
        mock_session.get_credentials.return_value = mock_credentials
        mock_org.create_session_for_account.return_value = mock_session

        with patch("src.clients.multi_account_client.AWSClient") as MockAWSClient:
            mock_aws = MagicMock()
            mock_aws.get_instances.return_value = [
                {"instance_id": "i-1234", "instance_type": "m5.xlarge"}
            ]
            mock_aws.get_instance_cost.return_value = {"monthly_estimate": 100.0}
            MockAWSClient.return_value = mock_aws

            client = MultiAccountClient(mock_org)
            account = AWSAccount(account_id="123456789012", name="Test")

            result = client.analyze_account(account)

            assert result.success is True
            assert len(result.instances) == 1
            assert result.error is None

    def test_analyze_account_role_failure(self):
        """Test account analysis with role assumption failure."""
        mock_org = MagicMock()
        mock_org.create_session_for_account.side_effect = Exception("Role not found")

        client = MultiAccountClient(mock_org)
        account = AWSAccount(account_id="123456789012", name="Test")

        result = client.analyze_account(account)

        assert result.success is False
        assert "Failed to assume role" in result.error

    def test_get_aggregated_instances(self):
        """Test aggregating instances across accounts."""
        mock_org = MagicMock()
        client = MultiAccountClient(mock_org)

        results = [
            AccountAnalysisResult(
                account_id="111",
                account_name="Prod",
                success=True,
                instances=[{"instance_id": "i-1"}],
            ),
            AccountAnalysisResult(
                account_id="222",
                account_name="Dev",
                success=True,
                instances=[{"instance_id": "i-2"}, {"instance_id": "i-3"}],
            ),
            AccountAnalysisResult(
                account_id="333",
                account_name="Failed",
                success=False,
                instances=[],
            ),
        ]

        summary = MultiAccountSummary(
            total_accounts=3,
            successful_accounts=2,
            failed_accounts=1,
            total_instances=3,
            total_current_monthly=0,
            total_potential_savings=0,
            accounts=results,
            by_account={},
            analysis_start=datetime.now(timezone.utc),
            analysis_end=datetime.now(timezone.utc),
        )

        instances = client.get_aggregated_instances(summary)

        assert len(instances) == 3
        assert instances[0]["account_id"] == "111"
        assert instances[1]["account_id"] == "222"

    def test_get_costs_by_account(self):
        """Test getting cost breakdown by account."""
        mock_org = MagicMock()
        client = MultiAccountClient(mock_org)

        results = [
            AccountAnalysisResult(
                account_id="111",
                account_name="Prod",
                success=True,
                instances=[],
                costs={"total_monthly": 1000.0},
            ),
            AccountAnalysisResult(
                account_id="222",
                account_name="Dev",
                success=True,
                instances=[],
                costs={"total_monthly": 500.0},
            ),
        ]

        summary = MultiAccountSummary(
            total_accounts=2,
            successful_accounts=2,
            failed_accounts=0,
            total_instances=0,
            total_current_monthly=1500,
            total_potential_savings=0,
            accounts=results,
            by_account={},
            analysis_start=datetime.now(timezone.utc),
            analysis_end=datetime.now(timezone.utc),
        )

        costs = client.get_costs_by_account(summary)

        assert costs["111"]["monthly_cost"] == 1000.0
        assert costs["111"]["percentage"] == pytest.approx(66.7, rel=0.1)
        assert costs["222"]["percentage"] == pytest.approx(33.3, rel=0.1)


class TestAccountAnalysisResult:
    """Tests for AccountAnalysisResult dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        result = AccountAnalysisResult(
            account_id="123456789012",
            account_name="Test Account",
            success=True,
            instances=[{"id": "i-1"}, {"id": "i-2"}],
            costs={"total_monthly": 100.0},
            analysis_time=5.125,
        )

        data = result.to_dict()

        assert data["account_id"] == "123456789012"
        assert data["account_name"] == "Test Account"
        assert data["success"] is True
        assert data["instance_count"] == 2
        assert data["analysis_time"] == 5.12  # Rounded to 2 decimals

    def test_default_values(self):
        """Test default values."""
        result = AccountAnalysisResult(
            account_id="123",
            account_name="Test",
            success=False,
        )

        assert result.instances == []
        assert result.costs == {}
        assert result.error is None


class TestMultiAccountSummary:
    """Tests for MultiAccountSummary dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        start = datetime.now(timezone.utc)
        end = start + timedelta(seconds=30)

        summary = MultiAccountSummary(
            total_accounts=3,
            successful_accounts=2,
            failed_accounts=1,
            total_instances=100,
            total_current_monthly=50000.555,
            total_potential_savings=10000.333,
            accounts=[],
            by_account={"111": {"name": "Test"}},
            analysis_start=start,
            analysis_end=end,
        )

        data = summary.to_dict()

        assert data["total_accounts"] == 3
        assert data["total_current_monthly"] == 50000.56
        assert data["total_potential_savings"] == 10000.33
        assert data["analysis_duration_seconds"] == 30.0

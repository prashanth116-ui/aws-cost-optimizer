"""AWS Organizations client for multi-account support."""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


@dataclass
class AWSAccount:
    """Represents an AWS account in the organization."""

    account_id: str
    name: str
    email: Optional[str] = None
    status: str = "ACTIVE"
    role_name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "account_id": self.account_id,
            "name": self.name,
            "email": self.email,
            "status": self.status,
            "role_name": self.role_name,
        }


@dataclass
class AssumedCredentials:
    """Credentials obtained from assuming a role."""

    access_key_id: str
    secret_access_key: str
    session_token: str
    expiration: datetime
    account_id: str
    role_name: str

    @property
    def is_expired(self) -> bool:
        """Check if credentials have expired."""
        return datetime.now(timezone.utc) >= self.expiration


class OrganizationsClient:
    """Client for AWS Organizations and cross-account role assumption.

    Provides methods to:
    - List accounts in an AWS Organization
    - Assume roles in member accounts
    - Create sessions for member accounts
    """

    def __init__(
        self,
        access_key_id: Optional[str] = None,
        secret_access_key: Optional[str] = None,
        region: str = "us-east-1",
        profile_name: Optional[str] = None,
        default_role_name: str = "CostOptimizerRole",
        session_duration: int = 3600
    ):
        """Initialize the Organizations client.

        Args:
            access_key_id: AWS access key ID
            secret_access_key: AWS secret access key
            region: AWS region
            profile_name: AWS CLI profile name
            default_role_name: Default role to assume in member accounts
            session_duration: Duration for assumed role sessions (seconds)
        """
        self.region = region
        self.default_role_name = default_role_name
        self.session_duration = min(session_duration, 3600)  # Max 1 hour for chained roles

        # Configure boto3 session
        config = Config(
            retries={"max_attempts": 3, "mode": "adaptive"},
            connect_timeout=10,
            read_timeout=30
        )

        session_kwargs = {}
        if profile_name:
            session_kwargs["profile_name"] = profile_name
        elif access_key_id and secret_access_key:
            session_kwargs["aws_access_key_id"] = access_key_id
            session_kwargs["aws_secret_access_key"] = secret_access_key

        self.session = boto3.Session(**session_kwargs)
        self.sts = self.session.client("sts", region_name=region, config=config)
        self.organizations = self.session.client("organizations", region_name="us-east-1", config=config)

        # Cache for assumed credentials
        self._credential_cache: Dict[str, AssumedCredentials] = {}

    def get_current_account(self) -> str:
        """Get the current AWS account ID.

        Returns:
            Account ID
        """
        try:
            response = self.sts.get_caller_identity()
            return response["Account"]
        except ClientError as e:
            logger.error(f"Failed to get current account: {e}")
            raise

    def list_accounts(self) -> List[AWSAccount]:
        """List all accounts in the organization.

        Returns:
            List of AWSAccount objects
        """
        accounts = []

        try:
            paginator = self.organizations.get_paginator("list_accounts")

            for page in paginator.paginate():
                for account in page.get("Accounts", []):
                    accounts.append(AWSAccount(
                        account_id=account["Id"],
                        name=account.get("Name", account["Id"]),
                        email=account.get("Email"),
                        status=account.get("Status", "ACTIVE"),
                    ))

            logger.info(f"Found {len(accounts)} accounts in organization")
            return accounts

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "AWSOrganizationsNotInUseException":
                logger.warning("AWS Organizations not enabled for this account")
                return []
            elif error_code == "AccessDeniedException":
                logger.warning("Access denied to Organizations API. Check IAM permissions.")
                return []
            else:
                logger.error(f"Failed to list accounts: {e}")
                raise

    def assume_role(
        self,
        account_id: str,
        role_name: Optional[str] = None,
        session_name: str = "CostOptimizer"
    ) -> AssumedCredentials:
        """Assume a role in another account.

        Args:
            account_id: Target account ID
            role_name: Role to assume (default: default_role_name)
            session_name: Session name for audit trail

        Returns:
            AssumedCredentials with temporary credentials
        """
        role = role_name or self.default_role_name
        cache_key = f"{account_id}:{role}"

        # Check cache
        if cache_key in self._credential_cache:
            cached = self._credential_cache[cache_key]
            if not cached.is_expired:
                logger.debug(f"Using cached credentials for {account_id}")
                return cached

        role_arn = f"arn:aws:iam::{account_id}:role/{role}"

        try:
            response = self.sts.assume_role(
                RoleArn=role_arn,
                RoleSessionName=session_name,
                DurationSeconds=self.session_duration,
            )

            credentials = response["Credentials"]

            assumed = AssumedCredentials(
                access_key_id=credentials["AccessKeyId"],
                secret_access_key=credentials["SecretAccessKey"],
                session_token=credentials["SessionToken"],
                expiration=credentials["Expiration"],
                account_id=account_id,
                role_name=role,
            )

            # Cache credentials
            self._credential_cache[cache_key] = assumed

            logger.info(f"Assumed role {role} in account {account_id}")
            return assumed

        except ClientError as e:
            logger.error(f"Failed to assume role {role_arn}: {e}")
            raise

    def create_session_for_account(
        self,
        account_id: str,
        role_name: Optional[str] = None
    ) -> boto3.Session:
        """Create a boto3 session for another account.

        Args:
            account_id: Target account ID
            role_name: Role to assume

        Returns:
            boto3 Session with assumed credentials
        """
        credentials = self.assume_role(account_id, role_name)

        return boto3.Session(
            aws_access_key_id=credentials.access_key_id,
            aws_secret_access_key=credentials.secret_access_key,
            aws_session_token=credentials.session_token,
        )

    def get_accounts_from_config(
        self,
        accounts_config: List[Dict[str, Any]]
    ) -> List[AWSAccount]:
        """Get accounts from explicit configuration.

        Args:
            accounts_config: List of account dictionaries from config

        Returns:
            List of AWSAccount objects
        """
        accounts = []

        for acc in accounts_config:
            accounts.append(AWSAccount(
                account_id=acc.get("account_id", ""),
                name=acc.get("name", acc.get("account_id", "")),
                email=acc.get("email"),
                status="ACTIVE",
                role_name=acc.get("role_name"),
            ))

        return accounts

    def discover_accounts(
        self,
        explicit_accounts: Optional[List[Dict[str, Any]]] = None
    ) -> List[AWSAccount]:
        """Discover accounts either from config or Organizations.

        Args:
            explicit_accounts: Optional explicit account list from config

        Returns:
            List of AWSAccount objects
        """
        if explicit_accounts:
            logger.info(f"Using {len(explicit_accounts)} accounts from config")
            return self.get_accounts_from_config(explicit_accounts)

        # Auto-discover from Organizations
        logger.info("Auto-discovering accounts from AWS Organizations")
        return self.list_accounts()

    def test_role_assumption(
        self,
        account_id: str,
        role_name: Optional[str] = None
    ) -> bool:
        """Test if role assumption works for an account.

        Args:
            account_id: Target account ID
            role_name: Role to test

        Returns:
            True if role assumption succeeded
        """
        try:
            credentials = self.assume_role(account_id, role_name)
            return credentials is not None
        except Exception as e:
            logger.warning(f"Role assumption test failed for {account_id}: {e}")
            return False

    def clear_credential_cache(self) -> None:
        """Clear the credential cache."""
        self._credential_cache.clear()
        logger.debug("Credential cache cleared")

    def test_connection(self) -> bool:
        """Test the Organizations connection.

        Returns:
            True if connection is successful
        """
        try:
            # Test STS access
            self.sts.get_caller_identity()

            # Test Organizations access (may fail if not enabled)
            try:
                self.organizations.describe_organization()
                logger.info("Organizations connection successful")
            except ClientError as e:
                if "AWSOrganizationsNotInUse" in str(e):
                    logger.info("STS connection successful (Organizations not enabled)")
                else:
                    logger.warning(f"Organizations access limited: {e}")

            return True

        except ClientError as e:
            logger.error(f"Connection test failed: {e}")
            return False

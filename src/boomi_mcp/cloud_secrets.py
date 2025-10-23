"""
Cloud Secrets Manager - Abstraction layer for credential storage.

Provides unified interface for:
- SQLite (development/testing)
- AWS Secrets Manager (production)
- GCP Secret Manager (production)
- Azure Key Vault (production)
- HashiCorp Vault (production)

Usage:
    from boomi_mcp.cloud_secrets import get_secrets_backend

    # Auto-detect backend from environment
    backend = get_secrets_backend()

    # Store credentials
    backend.put_secret("user@example.com", "default", {
        "username": "BOOMI_TOKEN.user@example.com",
        "password": "api-token",
        "account_id": "account-123"
    })

    # Retrieve credentials
    creds = backend.get_secret("user@example.com", "default")
"""

import os
import json
import time
import logging
import sqlite3
from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class SecretsBackend(ABC):
    """Abstract base class for credential storage backends."""

    @abstractmethod
    def put_secret(self, subject: str, profile: str, payload: Dict[str, str]) -> None:
        """
        Store credentials for a user profile.

        Args:
            subject: User identifier (typically email or sub claim from JWT)
            profile: Profile name (e.g., 'default', 'sandbox', 'prod')
            payload: Credential data (username, password, account_id, base_url)
        """
        pass

    @abstractmethod
    def get_secret(self, subject: str, profile: str) -> Dict[str, str]:
        """
        Retrieve credentials for a user profile.

        Args:
            subject: User identifier
            profile: Profile name

        Returns:
            Credential data

        Raises:
            ValueError: If profile not found
        """
        pass

    @abstractmethod
    def list_profiles(self, subject: str) -> List[Dict[str, Any]]:
        """
        List all profiles for a user.

        Args:
            subject: User identifier

        Returns:
            List of profiles with metadata
        """
        pass

    @abstractmethod
    def delete_profile(self, subject: str, profile: str) -> None:
        """
        Delete a user profile.

        Args:
            subject: User identifier
            profile: Profile name

        Raises:
            ValueError: If profile not found
        """
        pass


class SQLiteSecretsBackend(SecretsBackend):
    """
    SQLite-based credential storage for development and testing.

    NOT recommended for production - use cloud secret managers instead.
    """

    def __init__(self, db_path: str = "secrets.sqlite"):
        self.db_path = db_path
        self._init_db()
        logger.info(f"Initialized SQLite secrets backend: {db_path}")

    @contextmanager
    def _db(self):
        """Database context manager with automatic schema initialization."""
        con = sqlite3.connect(self.db_path)
        try:
            yield con
            con.commit()
        finally:
            con.close()

    def _init_db(self):
        """Initialize database schema."""
        with self._db() as con:
            con.execute("""
            CREATE TABLE IF NOT EXISTS secrets (
                sub TEXT NOT NULL,
                profile TEXT NOT NULL,
                payload TEXT NOT NULL,
                updated_at REAL NOT NULL,
                PRIMARY KEY (sub, profile)
            )""")

    def put_secret(self, subject: str, profile: str, payload: Dict[str, str]) -> None:
        with self._db() as con:
            con.execute(
                "REPLACE INTO secrets (sub, profile, payload, updated_at) VALUES (?, ?, ?, ?)",
                (subject, profile, json.dumps(payload), time.time())
            )
        logger.info(f"Stored credentials for {subject}:{profile}")

    def get_secret(self, subject: str, profile: str) -> Dict[str, str]:
        with self._db() as con:
            cur = con.execute("SELECT payload FROM secrets WHERE sub=? AND profile=?", (subject, profile))
            row = cur.fetchone()
            if not row:
                raise ValueError(f"Profile '{profile}' not found for this user")
            return json.loads(row[0])

    def list_profiles(self, subject: str) -> List[Dict[str, Any]]:
        with self._db() as con:
            cur = con.execute("SELECT profile, updated_at FROM secrets WHERE sub=?", (subject,))
            return [{"profile": p, "updated_at": ts} for (p, ts) in cur.fetchall()]

    def delete_profile(self, subject: str, profile: str) -> None:
        with self._db() as con:
            cur = con.execute("DELETE FROM secrets WHERE sub=? AND profile=?", (subject, profile))
            if cur.rowcount == 0:
                raise ValueError(f"Profile '{profile}' not found")
        logger.info(f"Deleted profile {subject}:{profile}")


class AWSSecretsManagerBackend(SecretsBackend):
    """
    AWS Secrets Manager backend for production deployments.

    Configuration:
        AWS_REGION - AWS region (default: us-east-1)
        AWS_SECRET_PREFIX - Secret name prefix (default: boomi-mcp/)

    Credentials are stored as: {prefix}{subject}/{profile}
    """

    def __init__(
        self,
        region: Optional[str] = None,
        prefix: Optional[str] = None
    ):
        self.region = region or os.getenv("AWS_REGION", "us-east-1")
        self.prefix = prefix or os.getenv("AWS_SECRET_PREFIX", "boomi-mcp/")

        try:
            import boto3
            self.client = boto3.client("secretsmanager", region_name=self.region)
            logger.info(f"Initialized AWS Secrets Manager backend (region: {self.region})")
        except ImportError:
            raise ImportError("boto3 is required for AWS Secrets Manager. Install: pip install boto3")

    def _secret_name(self, subject: str, profile: str) -> str:
        """Generate secret name from subject and profile."""
        return f"{self.prefix}{subject}/{profile}"

    def put_secret(self, subject: str, profile: str, payload: Dict[str, str]) -> None:
        secret_name = self._secret_name(subject, profile)
        secret_string = json.dumps(payload)

        try:
            # Try to update existing secret
            self.client.update_secret(
                SecretId=secret_name,
                SecretString=secret_string
            )
            logger.info(f"Updated AWS secret: {secret_name}")
        except self.client.exceptions.ResourceNotFoundException:
            # Create new secret
            self.client.create_secret(
                Name=secret_name,
                SecretString=secret_string,
                Description=f"Boomi credentials for {subject} ({profile})"
            )
            logger.info(f"Created AWS secret: {secret_name}")

    def get_secret(self, subject: str, profile: str) -> Dict[str, str]:
        secret_name = self._secret_name(subject, profile)

        try:
            response = self.client.get_secret_value(SecretId=secret_name)
            return json.loads(response["SecretString"])
        except self.client.exceptions.ResourceNotFoundException:
            raise ValueError(f"Profile '{profile}' not found for this user")

    def list_profiles(self, subject: str) -> List[Dict[str, Any]]:
        # List all secrets with the user's prefix
        prefix = f"{self.prefix}{subject}/"
        profiles = []

        paginator = self.client.get_paginator("list_secrets")
        for page in paginator.paginate():
            for secret in page.get("SecretList", []):
                name = secret["Name"]
                if name.startswith(prefix):
                    profile = name[len(prefix):]
                    profiles.append({
                        "profile": profile,
                        "updated_at": secret.get("LastChangedDate", secret.get("CreatedDate")).timestamp()
                    })

        return profiles

    def delete_profile(self, subject: str, profile: str) -> None:
        secret_name = self._secret_name(subject, profile)

        try:
            # Schedule deletion (AWS requires 7-30 day waiting period)
            self.client.delete_secret(
                SecretId=secret_name,
                ForceDeleteWithoutRecovery=False,
                RecoveryWindowInDays=7  # Minimum recovery window
            )
            logger.info(f"Scheduled deletion of AWS secret: {secret_name}")
        except self.client.exceptions.ResourceNotFoundException:
            raise ValueError(f"Profile '{profile}' not found")


class GCPSecretManagerBackend(SecretsBackend):
    """
    Google Cloud Secret Manager backend for production deployments.

    Configuration:
        GCP_PROJECT_ID - GCP project ID (required)
        GCP_SECRET_PREFIX - Secret name prefix (default: boomi-mcp-)

    Credentials are stored as: {prefix}{subject}-{profile}
    """

    def __init__(
        self,
        project_id: Optional[str] = None,
        prefix: Optional[str] = None
    ):
        self.project_id = project_id or os.getenv("GCP_PROJECT_ID")
        if not self.project_id:
            raise ValueError("GCP_PROJECT_ID environment variable is required")

        self.prefix = prefix or os.getenv("GCP_SECRET_PREFIX", "boomi-mcp-")

        try:
            from google.cloud import secretmanager
            self.client = secretmanager.SecretManagerServiceClient()
            self.parent = f"projects/{self.project_id}"
            logger.info(f"Initialized GCP Secret Manager backend (project: {self.project_id})")
        except ImportError:
            raise ImportError(
                "google-cloud-secret-manager is required. "
                "Install: pip install google-cloud-secret-manager"
            )

    def _secret_id(self, subject: str, profile: str) -> str:
        """Generate secret ID (GCP has naming restrictions)."""
        # Replace @ and . with hyphens for valid secret names
        safe_subject = subject.replace("@", "-at-").replace(".", "-")
        return f"{self.prefix}{safe_subject}-{profile}"

    def _secret_name(self, subject: str, profile: str) -> str:
        """Full secret path."""
        secret_id = self._secret_id(subject, profile)
        return f"{self.parent}/secrets/{secret_id}"

    def put_secret(self, subject: str, profile: str, payload: Dict[str, str]) -> None:
        secret_id = self._secret_id(subject, profile)
        secret_name = self._secret_name(subject, profile)
        secret_data = json.dumps(payload).encode("utf-8")

        try:
            # Try to add new version to existing secret
            version_name = f"{secret_name}/versions/latest"
            self.client.access_secret_version(request={"name": version_name})

            # Secret exists, add new version
            self.client.add_secret_version(
                request={
                    "parent": secret_name,
                    "payload": {"data": secret_data}
                }
            )
            logger.info(f"Updated GCP secret: {secret_id}")

        except Exception:
            # Secret doesn't exist, create it
            self.client.create_secret(
                request={
                    "parent": self.parent,
                    "secret_id": secret_id,
                    "secret": {
                        "replication": {"automatic": {}}
                    }
                }
            )
            self.client.add_secret_version(
                request={
                    "parent": secret_name,
                    "payload": {"data": secret_data}
                }
            )
            logger.info(f"Created GCP secret: {secret_id}")

    def get_secret(self, subject: str, profile: str) -> Dict[str, str]:
        secret_name = self._secret_name(subject, profile)
        version_name = f"{secret_name}/versions/latest"

        try:
            response = self.client.access_secret_version(request={"name": version_name})
            payload = response.payload.data.decode("utf-8")
            return json.loads(payload)
        except Exception:
            raise ValueError(f"Profile '{profile}' not found for this user")

    def list_profiles(self, subject: str) -> List[Dict[str, Any]]:
        # GCP doesn't support prefix filtering, so we need to list all and filter
        profiles = []
        safe_subject = subject.replace("@", "-at-").replace(".", "-")
        search_prefix = f"{self.prefix}{safe_subject}-"

        request = {"parent": self.parent}
        for secret in self.client.list_secrets(request=request):
            secret_id = secret.name.split("/")[-1]
            if secret_id.startswith(search_prefix):
                profile = secret_id[len(search_prefix):]
                profiles.append({
                    "profile": profile,
                    "updated_at": secret.create_time.timestamp()
                })

        return profiles

    def delete_profile(self, subject: str, profile: str) -> None:
        secret_name = self._secret_name(subject, profile)

        try:
            self.client.delete_secret(request={"name": secret_name})
            logger.info(f"Deleted GCP secret: {self._secret_id(subject, profile)}")
        except Exception:
            raise ValueError(f"Profile '{profile}' not found")


class AzureKeyVaultBackend(SecretsBackend):
    """
    Azure Key Vault backend for production deployments.

    Configuration:
        AZURE_KEY_VAULT_URL - Key Vault URL (e.g., https://myvault.vault.azure.net/)
        AZURE_SECRET_PREFIX - Secret name prefix (default: boomi-mcp-)

    Uses DefaultAzureCredential for authentication.
    """

    def __init__(
        self,
        vault_url: Optional[str] = None,
        prefix: Optional[str] = None
    ):
        self.vault_url = vault_url or os.getenv("AZURE_KEY_VAULT_URL")
        if not self.vault_url:
            raise ValueError("AZURE_KEY_VAULT_URL environment variable is required")

        self.prefix = prefix or os.getenv("AZURE_SECRET_PREFIX", "boomi-mcp-")

        try:
            from azure.keyvault.secrets import SecretClient
            from azure.identity import DefaultAzureCredential

            credential = DefaultAzureCredential()
            self.client = SecretClient(vault_url=self.vault_url, credential=credential)
            logger.info(f"Initialized Azure Key Vault backend: {self.vault_url}")
        except ImportError:
            raise ImportError(
                "azure-keyvault-secrets and azure-identity are required. "
                "Install: pip install azure-keyvault-secrets azure-identity"
            )

    def _secret_name(self, subject: str, profile: str) -> str:
        """Generate secret name (Azure has naming restrictions)."""
        # Azure Key Vault allows alphanumeric and hyphens only
        safe_subject = subject.replace("@", "-at-").replace(".", "-")
        return f"{self.prefix}{safe_subject}-{profile}"

    def put_secret(self, subject: str, profile: str, payload: Dict[str, str]) -> None:
        secret_name = self._secret_name(subject, profile)
        secret_value = json.dumps(payload)

        self.client.set_secret(secret_name, secret_value)
        logger.info(f"Stored Azure Key Vault secret: {secret_name}")

    def get_secret(self, subject: str, profile: str) -> Dict[str, str]:
        secret_name = self._secret_name(subject, profile)

        try:
            secret = self.client.get_secret(secret_name)
            return json.loads(secret.value)
        except Exception:
            raise ValueError(f"Profile '{profile}' not found for this user")

    def list_profiles(self, subject: str) -> List[Dict[str, Any]]:
        profiles = []
        safe_subject = subject.replace("@", "-at-").replace(".", "-")
        search_prefix = f"{self.prefix}{safe_subject}-"

        for secret_properties in self.client.list_properties_of_secrets():
            if secret_properties.name.startswith(search_prefix):
                profile = secret_properties.name[len(search_prefix):]
                profiles.append({
                    "profile": profile,
                    "updated_at": secret_properties.updated_on.timestamp() if secret_properties.updated_on else 0
                })

        return profiles

    def delete_profile(self, subject: str, profile: str) -> None:
        secret_name = self._secret_name(subject, profile)

        try:
            self.client.begin_delete_secret(secret_name).wait()
            logger.info(f"Deleted Azure Key Vault secret: {secret_name}")
        except Exception:
            raise ValueError(f"Profile '{profile}' not found")


def get_secrets_backend(backend_type: Optional[str] = None) -> SecretsBackend:
    """
    Get secrets backend based on environment configuration.

    Args:
        backend_type: Override backend type (sqlite, aws, gcp, azure)
                     If None, auto-detected from SECRETS_BACKEND env var

    Returns:
        Configured secrets backend

    Environment Variables:
        SECRETS_BACKEND - Backend type (sqlite, aws, gcp, azure) [default: sqlite]

        SQLite:
            SECRETS_DB - Database file path [default: secrets.sqlite]

        AWS:
            AWS_REGION - AWS region [default: us-east-1]
            AWS_SECRET_PREFIX - Secret name prefix [default: boomi-mcp/]

        GCP:
            GCP_PROJECT_ID - GCP project ID [required]
            GCP_SECRET_PREFIX - Secret name prefix [default: boomi-mcp-]

        Azure:
            AZURE_KEY_VAULT_URL - Key Vault URL [required]
            AZURE_SECRET_PREFIX - Secret name prefix [default: boomi-mcp-]
    """
    backend_type = backend_type or os.getenv("SECRETS_BACKEND", "sqlite").lower()

    if backend_type == "sqlite":
        db_path = os.getenv("SECRETS_DB", "secrets.sqlite")
        return SQLiteSecretsBackend(db_path=db_path)

    elif backend_type == "aws":
        return AWSSecretsManagerBackend()

    elif backend_type == "gcp":
        return GCPSecretManagerBackend()

    elif backend_type == "azure":
        return AzureKeyVaultBackend()

    else:
        raise ValueError(
            f"Unknown secrets backend: {backend_type}. "
            f"Supported: sqlite, aws, gcp, azure"
        )

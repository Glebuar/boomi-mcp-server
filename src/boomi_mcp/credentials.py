"""Secure credential storage with encryption for per-user Boomi credentials."""

import sqlite3
import json
import os
from typing import Optional, Dict, List
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64


class CredentialStore:
    """
    Encrypted credential storage keyed by JWT subject + profile.

    Development: Uses SQLite with Fernet encryption.
    Production: Replace with cloud secret manager (AWS Secrets Manager, GCP Secret Manager, etc.)
    """

    def __init__(self, db_path: str = "credentials.db", encryption_key: Optional[str] = None):
        """
        Initialize credential store.

        Args:
            db_path: Path to SQLite database file
            encryption_key: Base64-encoded encryption key (generate with generate_key())
                           Falls back to MCP_ENCRYPTION_KEY env var
        """
        self.db_path = db_path

        # Get or generate encryption key
        key_str = encryption_key or os.getenv("MCP_ENCRYPTION_KEY")
        if not key_str:
            raise ValueError(
                "MCP_ENCRYPTION_KEY must be set. Generate with: "
                "python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
            )

        self.cipher = Fernet(key_str.encode() if isinstance(key_str, str) else key_str)
        self._init_db()

    def _init_db(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS credentials (
                    subject TEXT NOT NULL,
                    profile TEXT NOT NULL,
                    encrypted_data BLOB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (subject, profile)
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_subject ON credentials(subject)
            """)
            conn.commit()

    def store_credentials(
        self,
        subject: str,
        profile: str,
        username: str,
        password: str,
        account_id: str,
        base_url: str = "https://api.boomi.com/api/rest/v1"
    ):
        """
        Store encrypted credentials for a user profile.

        Args:
            subject: JWT subject (user identifier)
            profile: Profile name (e.g., 'sandbox', 'prod')
            username: Boomi username
            password: Boomi password (will be encrypted)
            account_id: Boomi account ID
            base_url: Boomi API base URL
        """
        credentials = {
            "username": username,
            "password": password,
            "account_id": account_id,
            "base_url": base_url,
        }

        # Encrypt credentials
        encrypted = self.cipher.encrypt(json.dumps(credentials).encode())

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO credentials (subject, profile, encrypted_data, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(subject, profile) DO UPDATE SET
                    encrypted_data = excluded.encrypted_data,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (subject, profile, encrypted)
            )
            conn.commit()

    def get_credentials(self, subject: str, profile: str) -> Optional[Dict[str, str]]:
        """
        Retrieve and decrypt credentials for a user profile.

        Args:
            subject: JWT subject (user identifier)
            profile: Profile name

        Returns:
            Dictionary with username, password, account_id, base_url or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT encrypted_data FROM credentials WHERE subject = ? AND profile = ?",
                (subject, profile)
            )
            row = cursor.fetchone()

        if not row:
            return None

        # Decrypt credentials
        decrypted = self.cipher.decrypt(row[0])
        return json.loads(decrypted.decode())

    def list_profiles(self, subject: str) -> List[str]:
        """
        List all profiles for a user.

        Args:
            subject: JWT subject (user identifier)

        Returns:
            List of profile names
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT profile FROM credentials WHERE subject = ? ORDER BY profile",
                (subject,)
            )
            return [row[0] for row in cursor.fetchall()]

    def delete_profile(self, subject: str, profile: str) -> bool:
        """
        Delete a user profile.

        Args:
            subject: JWT subject (user identifier)
            profile: Profile name

        Returns:
            True if deleted, False if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM credentials WHERE subject = ? AND profile = ?",
                (subject, profile)
            )
            conn.commit()
            return cursor.rowcount > 0

    @staticmethod
    def generate_key() -> str:
        """Generate a new encryption key for development."""
        return Fernet.generate_key().decode()


# Production migration notes:
"""
PRODUCTION SECRET MANAGER MIGRATION:

Replace CredentialStore with cloud secret manager integration:

AWS Secrets Manager:
    import boto3
    secrets_client = boto3.client('secretsmanager')
    secret_name = f"{subject}/{profile}/boomi-credentials"
    secrets_client.create_secret(Name=secret_name, SecretString=json.dumps(credentials))

GCP Secret Manager:
    from google.cloud import secretmanager
    client = secretmanager.SecretManagerServiceClient()
    parent = f"projects/{project_id}"
    secret_id = f"{subject}-{profile}-boomi"
    client.create_secret(request={"parent": parent, "secret_id": secret_id, ...})

Azure Key Vault:
    from azure.keyvault.secrets import SecretClient
    from azure.identity import DefaultAzureCredential
    client = SecretClient(vault_url=vault_url, credential=DefaultAzureCredential())
    client.set_secret(f"{subject}-{profile}-boomi", json.dumps(credentials))

Key considerations:
- Use IAM/RBAC to restrict access to secrets
- Enable audit logging for all secret access
- Use secret versioning for credential rotation
- Set up automatic secret rotation policies
- Tag secrets with environment, owner, expiry metadata
"""

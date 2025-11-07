"""GCP Secret Manager adapter for AsyncKeyValue protocol.

Implements the AsyncKeyValue protocol using GCP Secret Manager as backend.
Designed for persistent OAuth token storage in FastMCP GoogleProvider.
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any

from google.cloud import secretmanager
from google.api_core import exceptions as gcp_exceptions


class GCPSecretManagerKeyValue:
    """AsyncKeyValue adapter for GCP Secret Manager.

    Provides persistent key-value storage using GCP Secret Manager as backend.
    Implements the AsyncKeyValue protocol required by FastMCP's OAuthProxy.

    Features:
    - Automatic encryption at rest (GCP Secret Manager)
    - Collection-based namespacing
    - TTL support via expiry timestamp in labels
    - Async interface wrapping synchronous GCP client
    """

    def __init__(self, project_id: str, prefix: str = "fastmcp-oauth-"):
        """Initialize GCP Secret Manager key-value storage.

        Args:
            project_id: GCP project ID
            prefix: Prefix for all secret names (default: "fastmcp-oauth-")
        """
        self.project_id = project_id
        self.prefix = prefix
        self.client = secretmanager.SecretManagerServiceClient()
        self.parent = f"projects/{project_id}"

    def _secret_name(self, collection: str | None, key: str) -> str:
        """Generate GCP secret name with collection namespace.

        Args:
            collection: Collection name (e.g., "mcp-upstream-tokens")
            key: Key within collection

        Returns:
            Full GCP secret name
        """
        # Use collection as namespace, sanitize key for GCP naming
        collection_part = (collection or "default").replace("_", "-").replace("/", "-")
        key_safe = key.replace("/", "-").replace("_", "-").replace(":", "-")
        return f"{self.prefix}{collection_part}--{key_safe}"

    def _secret_path(self, secret_name: str) -> str:
        """Get full secret path for GCP API."""
        return f"{self.parent}/secrets/{secret_name}"

    async def get(self, key: str, collection: str | None = None) -> dict[str, Any] | None:
        """Get value from GCP Secret Manager.

        Args:
            key: Key to retrieve
            collection: Optional collection namespace

        Returns:
            Dictionary value or None if not found/expired
        """
        secret_name = self._secret_name(collection, key)

        try:
            # Get latest secret version (async wrapper around sync call)
            secret_path = f"{self._secret_path(secret_name)}/versions/latest"
            response = await asyncio.to_thread(
                self.client.access_secret_version,
                request={"name": secret_path}
            )

            # Parse JSON payload
            value = json.loads(response.payload.data.decode("UTF-8"))

            # Check TTL expiry
            if "_ttl_expires_at" in value:
                if time.time() > value["_ttl_expires_at"]:
                    # Expired, return None and delete asynchronously
                    asyncio.create_task(self.delete(key, collection))
                    return None

            return value

        except gcp_exceptions.NotFound:
            return None
        except json.JSONDecodeError:
            # Corrupted data, return None
            return None
        except Exception as e:
            # Log error but return None per protocol
            print(f"[ERROR] Failed to get secret {secret_name}: {e}")
            return None

    async def put(
        self,
        key: str,
        value: dict[str, Any],
        collection: str | None = None,
        ttl: float | None = None,
    ) -> None:
        """Store value in GCP Secret Manager.

        Args:
            key: Key to store
            value: Dictionary value to store
            collection: Optional collection namespace
            ttl: Optional TTL in seconds
        """
        secret_name = self._secret_name(collection, key)

        # Add TTL expiry timestamp if provided
        if ttl is not None:
            value = {**value, "_ttl_expires_at": time.time() + ttl}

        # Serialize to JSON
        payload = json.dumps(value).encode("UTF-8")

        try:
            # Try to create secret (if doesn't exist)
            await asyncio.to_thread(
                self.client.create_secret,
                request={
                    "parent": self.parent,
                    "secret_id": secret_name,
                    "secret": {"replication": {"automatic": {}}},
                }
            )
        except gcp_exceptions.AlreadyExists:
            # Secret exists, will add new version below
            pass
        except Exception as e:
            print(f"[ERROR] Failed to create secret {secret_name}: {e}")
            raise

        try:
            # Add new secret version with value
            secret_path = self._secret_path(secret_name)
            await asyncio.to_thread(
                self.client.add_secret_version,
                request={
                    "parent": secret_path,
                    "payload": {"data": payload},
                }
            )
        except Exception as e:
            print(f"[ERROR] Failed to add secret version {secret_name}: {e}")
            raise

    async def delete(self, key: str, collection: str | None = None) -> bool:
        """Delete secret from GCP Secret Manager.

        Args:
            key: Key to delete
            collection: Optional collection namespace

        Returns:
            True if deleted, False if not found
        """
        secret_name = self._secret_name(collection, key)
        secret_path = self._secret_path(secret_name)

        try:
            await asyncio.to_thread(
                self.client.delete_secret,
                request={"name": secret_path}
            )
            return True
        except gcp_exceptions.NotFound:
            return False
        except Exception as e:
            print(f"[ERROR] Failed to delete secret {secret_name}: {e}")
            return False

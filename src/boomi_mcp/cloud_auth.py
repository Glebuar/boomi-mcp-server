"""
Cloud Authentication Module for Boomi MCP Server.

Provides production-ready JWT authentication with:
- RS256/RS384/RS512 asymmetric algorithms using JWKS
- Support for major IdP providers (Auth0, Okta, Google, Azure, AWS Cognito)
- JWKS caching and automatic key rotation
- Backward compatibility with HS256 for development

Production Usage:
    Configure via environment variables:
    - MCP_JWT_ALG=RS256
    - MCP_JWT_JWKS_URI=https://your-idp.com/.well-known/jwks.json
    - MCP_JWT_ISSUER=https://your-idp.com/
    - MCP_JWT_AUDIENCE=your-audience
"""

import os
import time
import logging
from typing import Optional, Dict, Any
from urllib.parse import urljoin

import httpx
from jwt import PyJWKClient
from fastmcp.server.auth import JWTVerifier

logger = logging.getLogger(__name__)


class CloudAuthConfig:
    """
    Cloud authentication configuration.
    Supports multiple authentication strategies based on environment.
    """

    def __init__(self):
        self.algorithm = os.getenv("MCP_JWT_ALG", "HS256")
        self.issuer = os.getenv("MCP_JWT_ISSUER")
        self.audience = os.getenv("MCP_JWT_AUDIENCE", "boomi-mcp")

        # Symmetric key (HS256/384/512)
        self.secret = os.getenv("MCP_JWT_SECRET")

        # Asymmetric key (RS256/384/512, ES256, etc.)
        self.jwks_uri = os.getenv("MCP_JWT_JWKS_URI")

        # JWKS caching (default 5 minutes)
        self.jwks_cache_ttl = int(os.getenv("MCP_JWT_JWKS_CACHE_TTL", "300"))

        # Validate configuration
        self._validate()

    def _validate(self):
        """Validate authentication configuration."""
        if self.algorithm.startswith("HS"):
            if not self.secret:
                raise ValueError(
                    f"{self.algorithm} requires MCP_JWT_SECRET environment variable"
                )
            if self.secret == "change-this-dev-secret":
                logger.warning("Using default JWT secret - not secure for production!")
        else:
            # Asymmetric algorithms require JWKS URI
            if not self.jwks_uri:
                raise ValueError(
                    f"{self.algorithm} requires MCP_JWT_JWKS_URI environment variable"
                )

        if not self.issuer:
            logger.warning("MCP_JWT_ISSUER not set - token validation may be less secure")

    def is_symmetric(self) -> bool:
        """Check if using symmetric algorithm (HS*)."""
        return self.algorithm.startswith("HS")

    def is_asymmetric(self) -> bool:
        """Check if using asymmetric algorithm (RS*, ES*, PS*)."""
        return not self.is_symmetric()


class JWKSClient:
    """
    JWKS client with caching and error handling.
    Fetches and caches JSON Web Key Sets from IdP providers.
    """

    def __init__(self, jwks_uri: str, cache_ttl: int = 300):
        self.jwks_uri = jwks_uri
        self.cache_ttl = cache_ttl
        self._cache: Optional[Dict[str, Any]] = None
        self._cache_time: float = 0

        # Create PyJWT JWKS client
        self._client = PyJWKClient(
            uri=jwks_uri,
            cache_keys=True,
            max_cached_keys=16,
            cache_jwk_set=True,
            lifespan=cache_ttl,
        )

        logger.info(f"Initialized JWKS client for {jwks_uri}")

    def get_signing_key(self, kid: Optional[str] = None):
        """
        Get signing key from JWKS.

        Args:
            kid: Key ID from JWT header (optional)

        Returns:
            Signing key for token validation
        """
        try:
            return self._client.get_signing_key(kid)
        except Exception as e:
            logger.error(f"Failed to get signing key from JWKS: {e}")
            raise

    def fetch_jwks(self) -> Dict[str, Any]:
        """
        Fetch JWKS from IdP (with caching).

        Returns:
            JWKS data as dictionary
        """
        now = time.time()

        # Check cache
        if self._cache and (now - self._cache_time) < self.cache_ttl:
            return self._cache

        # Fetch fresh JWKS
        try:
            response = httpx.get(self.jwks_uri, timeout=10.0)
            response.raise_for_status()

            self._cache = response.json()
            self._cache_time = now

            logger.info(f"Fetched JWKS from {self.jwks_uri}")
            return self._cache

        except Exception as e:
            logger.error(f"Failed to fetch JWKS from {self.jwks_uri}: {e}")
            if self._cache:
                logger.warning("Using stale JWKS cache")
                return self._cache
            raise


def create_cloud_auth_verifier(config: Optional[CloudAuthConfig] = None) -> JWTVerifier:
    """
    Create JWT verifier for cloud deployment.

    Args:
        config: Authentication configuration (auto-loaded from env if None)

    Returns:
        Configured JWTVerifier instance

    Examples:
        Development (HS256):
            export MCP_JWT_ALG=HS256
            export MCP_JWT_SECRET=your-secret-key
            export MCP_JWT_ISSUER=https://local-issuer
            export MCP_JWT_AUDIENCE=boomi-mcp

        Production (RS256 with Auth0):
            export MCP_JWT_ALG=RS256
            export MCP_JWT_JWKS_URI=https://your-tenant.auth0.com/.well-known/jwks.json
            export MCP_JWT_ISSUER=https://your-tenant.auth0.com/
            export MCP_JWT_AUDIENCE=your-api-identifier

        Production (RS256 with Azure AD):
            export MCP_JWT_ALG=RS256
            export MCP_JWT_JWKS_URI=https://login.microsoftonline.com/{tenant}/discovery/v2.0/keys
            export MCP_JWT_ISSUER=https://sts.windows.net/{tenant}/
            export MCP_JWT_AUDIENCE=your-client-id

        Production (RS256 with Google):
            export MCP_JWT_ALG=RS256
            export MCP_JWT_JWKS_URI=https://www.googleapis.com/oauth2/v3/certs
            export MCP_JWT_ISSUER=https://accounts.google.com
            export MCP_JWT_AUDIENCE=your-client-id

        Production (RS256 with AWS Cognito):
            export MCP_JWT_ALG=RS256
            export MCP_JWT_JWKS_URI=https://cognito-idp.{region}.amazonaws.com/{userPoolId}/.well-known/jwks.json
            export MCP_JWT_ISSUER=https://cognito-idp.{region}.amazonaws.com/{userPoolId}
            export MCP_JWT_AUDIENCE=your-client-id
    """
    if config is None:
        config = CloudAuthConfig()

    logger.info(f"Creating JWT verifier with algorithm: {config.algorithm}")
    logger.info(f"Issuer: {config.issuer}")
    logger.info(f"Audience: {config.audience}")

    if config.is_symmetric():
        # Symmetric algorithm (HS256/384/512)
        logger.info("Using symmetric key authentication (development mode)")
        return JWTVerifier(
            public_key=config.secret,  # For HS*, public_key is the shared secret
            algorithm=config.algorithm,
            issuer=config.issuer,
            audience=config.audience,
        )
    else:
        # Asymmetric algorithm (RS256/384/512, ES256, etc.)
        logger.info(f"Using JWKS authentication from {config.jwks_uri}")

        return JWTVerifier(
            jwks_uri=config.jwks_uri,
            algorithm=config.algorithm,
            issuer=config.issuer,
            audience=config.audience,
        )


# Common IdP configurations
class IdPPresets:
    """
    Preset configurations for common Identity Providers.
    Use these as templates for your .env configuration.
    """

    @staticmethod
    def auth0(tenant: str, audience: str) -> Dict[str, str]:
        """
        Auth0 configuration.

        Args:
            tenant: Your Auth0 tenant (e.g., 'your-tenant.auth0.com')
            audience: Your API identifier

        Returns:
            Environment variable configuration
        """
        return {
            "MCP_JWT_ALG": "RS256",
            "MCP_JWT_JWKS_URI": f"https://{tenant}/.well-known/jwks.json",
            "MCP_JWT_ISSUER": f"https://{tenant}/",
            "MCP_JWT_AUDIENCE": audience,
        }

    @staticmethod
    def azure_ad(tenant_id: str, client_id: str) -> Dict[str, str]:
        """
        Azure AD configuration.

        Args:
            tenant_id: Your Azure AD tenant ID
            client_id: Your application client ID

        Returns:
            Environment variable configuration
        """
        return {
            "MCP_JWT_ALG": "RS256",
            "MCP_JWT_JWKS_URI": f"https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys",
            "MCP_JWT_ISSUER": f"https://sts.windows.net/{tenant_id}/",
            "MCP_JWT_AUDIENCE": client_id,
        }

    @staticmethod
    def google(client_id: str) -> Dict[str, str]:
        """
        Google OAuth configuration.

        Args:
            client_id: Your Google OAuth client ID

        Returns:
            Environment variable configuration
        """
        return {
            "MCP_JWT_ALG": "RS256",
            "MCP_JWT_JWKS_URI": "https://www.googleapis.com/oauth2/v3/certs",
            "MCP_JWT_ISSUER": "https://accounts.google.com",
            "MCP_JWT_AUDIENCE": client_id,
        }

    @staticmethod
    def aws_cognito(region: str, user_pool_id: str, client_id: str) -> Dict[str, str]:
        """
        AWS Cognito configuration.

        Args:
            region: AWS region (e.g., 'us-east-1')
            user_pool_id: Your Cognito user pool ID
            client_id: Your app client ID

        Returns:
            Environment variable configuration
        """
        return {
            "MCP_JWT_ALG": "RS256",
            "MCP_JWT_JWKS_URI": f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}/.well-known/jwks.json",
            "MCP_JWT_ISSUER": f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}",
            "MCP_JWT_AUDIENCE": client_id,
        }

    @staticmethod
    def okta(domain: str, audience: str) -> Dict[str, str]:
        """
        Okta configuration.

        Args:
            domain: Your Okta domain (e.g., 'your-domain.okta.com')
            audience: Your API identifier

        Returns:
            Environment variable configuration
        """
        return {
            "MCP_JWT_ALG": "RS256",
            "MCP_JWT_JWKS_URI": f"https://{domain}/oauth2/default/v1/keys",
            "MCP_JWT_ISSUER": f"https://{domain}/oauth2/default",
            "MCP_JWT_AUDIENCE": audience,
        }

"""
OAuth 2.0 Provider for Boomi MCP Server.

This module provides OAuth 2.0 authentication using FastMCP's OAuthProxy pattern.
It supports multiple Identity Providers (Google, Auth0, Azure AD, AWS Cognito, Okta, GitHub)
while presenting a standard OAuth 2.0 interface to MCP clients.

Features:
- OAuth 2.0 Authorization Code flow with PKCE
- Dynamic Client Registration (DCR) for MCP clients
- Refresh token support for long-lived sessions
- Token validation using upstream IdP's JWKS
- Automatic token refresh without user intervention
- Consent flow for security (protects against confused deputy attacks)

Architecture:
- MCP clients register dynamically and get unique credentials
- Proxy forwards authorization to upstream IdP (Google, Auth0, etc.)
- Tokens are validated against upstream JWKS
- Refresh tokens enable seamless session extension
"""

import os
import logging
from typing import Optional
from urllib.parse import urlparse

from fastmcp.server.auth.oauth_proxy import OAuthProxy
from fastmcp.server.auth.auth import TokenVerifier
from mcp.server.auth.provider import AccessToken

logger = logging.getLogger(__name__)


class BoomiOAuthProvider:
    """
    Factory for creating OAuth providers for different Identity Providers.

    Supports:
    - Google OAuth
    - Auth0
    - Azure AD (Microsoft Entra ID)
    - AWS Cognito
    - Okta
    - GitHub
    - Generic OAuth 2.0 providers

    Usage:
        # Using environment variables
        provider = BoomiOAuthProvider.from_env()

        # Using specific provider
        provider = BoomiOAuthProvider.create_google_provider(
            client_id="your-client-id",
            client_secret="your-client-secret",
            base_url="https://your-server.com"
        )
    """

    # Required scopes for MCP access
    REQUIRED_SCOPES = [
        "secrets:read",    # List Boomi profiles
        "secrets:write",   # Store/delete credentials
        "boomi:read"       # Call Boomi API
    ]

    @staticmethod
    def _create_token_verifier(
        issuer: str,
        jwks_uri: str,
        audience: str,
        required_scopes: Optional[list[str]] = None
    ) -> TokenVerifier:
        """Create token verifier for validating OAuth tokens."""

        class SimpleTokenVerifier(TokenVerifier):
            """Token verifier that validates tokens using upstream JWKS."""

            def __init__(self, issuer: str, jwks_uri: str, audience: str, required_scopes: list[str]):
                self.issuer = issuer
                self.jwks_uri = jwks_uri
                self.audience = audience
                self.required_scopes = required_scopes

                # Import JWT validation dependencies
                from jwt import PyJWKClient
                import jwt as pyjwt

                self.jwks_client = PyJWKClient(
                    uri=jwks_uri,
                    cache_keys=True,
                    max_cached_keys=16,
                    cache_jwk_set=True,
                    lifespan=300,  # 5 minutes
                )
                self.pyjwt = pyjwt

                logger.info(f"Initialized token verifier for {issuer}")

            async def verify_token(self, token: str) -> AccessToken | None:
                """Verify token signature and claims using upstream JWKS."""
                try:
                    # Get signing key from JWKS
                    signing_key = self.jwks_client.get_signing_key_from_jwt(token)

                    # Verify token
                    claims = self.pyjwt.decode(
                        token,
                        signing_key.key,
                        algorithms=["RS256", "RS384", "RS512"],
                        issuer=self.issuer,
                        audience=self.audience,
                        options={"verify_exp": True}
                    )

                    # Extract user info
                    client_id = claims.get("sub") or claims.get("client_id", "")
                    scopes = claims.get("scope", "").split() if isinstance(claims.get("scope"), str) else claims.get("scopes", [])
                    exp = claims.get("exp")

                    logger.debug(f"Token validated for user: {client_id}")

                    return AccessToken(
                        token=token,
                        client_id=client_id,
                        scopes=scopes,
                        expires_at=exp
                    )

                except Exception as e:
                    logger.debug(f"Token validation failed: {e}")
                    return None

        return SimpleTokenVerifier(
            issuer=issuer,
            jwks_uri=jwks_uri,
            audience=audience,
            required_scopes=required_scopes or BoomiOAuthProvider.REQUIRED_SCOPES
        )

    @staticmethod
    def from_env() -> OAuthProxy:
        """
        Create OAuth provider from environment variables.

        Required environment variables:
        - OIDC_PROVIDER: Provider type (google, auth0, azure, cognito, okta, github, generic)
        - OIDC_CLIENT_ID: OAuth client ID
        - OIDC_CLIENT_SECRET: OAuth client secret
        - OIDC_BASE_URL: Public URL of this server

        Provider-specific variables:

        For Google:
        - No additional variables needed

        For Auth0:
        - OIDC_DOMAIN: Auth0 domain (e.g., your-tenant.auth0.com)

        For Azure AD:
        - OIDC_TENANT_ID: Azure AD tenant ID

        For AWS Cognito:
        - OIDC_REGION: AWS region
        - OIDC_USER_POOL_ID: Cognito user pool ID

        For Okta:
        - OIDC_DOMAIN: Okta domain (e.g., your-domain.okta.com)

        For GitHub:
        - No additional variables needed

        For Generic:
        - OIDC_AUTHORIZATION_ENDPOINT: Authorization endpoint URL
        - OIDC_TOKEN_ENDPOINT: Token endpoint URL
        - OIDC_JWKS_URI: JWKS URI for token validation
        - OIDC_ISSUER: Token issuer
        """
        provider_type = os.getenv("OIDC_PROVIDER", "").lower()
        client_id = os.getenv("OIDC_CLIENT_ID")
        client_secret = os.getenv("OIDC_CLIENT_SECRET")
        base_url = os.getenv("OIDC_BASE_URL", "http://localhost:8000")

        if not client_id or not client_secret:
            raise ValueError("OIDC_CLIENT_ID and OIDC_CLIENT_SECRET must be set")

        if provider_type == "google":
            return BoomiOAuthProvider.create_google_provider(client_id, client_secret, base_url)
        elif provider_type == "auth0":
            domain = os.getenv("OIDC_DOMAIN")
            if not domain:
                raise ValueError("OIDC_DOMAIN must be set for Auth0")
            return BoomiOAuthProvider.create_auth0_provider(client_id, client_secret, domain, base_url)
        elif provider_type == "azure":
            tenant_id = os.getenv("OIDC_TENANT_ID")
            if not tenant_id:
                raise ValueError("OIDC_TENANT_ID must be set for Azure AD")
            return BoomiOAuthProvider.create_azure_provider(client_id, client_secret, tenant_id, base_url)
        elif provider_type == "cognito":
            region = os.getenv("OIDC_REGION")
            user_pool_id = os.getenv("OIDC_USER_POOL_ID")
            if not region or not user_pool_id:
                raise ValueError("OIDC_REGION and OIDC_USER_POOL_ID must be set for AWS Cognito")
            return BoomiOAuthProvider.create_cognito_provider(client_id, client_secret, region, user_pool_id, base_url)
        elif provider_type == "okta":
            domain = os.getenv("OIDC_DOMAIN")
            if not domain:
                raise ValueError("OIDC_DOMAIN must be set for Okta")
            return BoomiOAuthProvider.create_okta_provider(client_id, client_secret, domain, base_url)
        elif provider_type == "github":
            return BoomiOAuthProvider.create_github_provider(client_id, client_secret, base_url)
        elif provider_type == "generic":
            auth_endpoint = os.getenv("OIDC_AUTHORIZATION_ENDPOINT")
            token_endpoint = os.getenv("OIDC_TOKEN_ENDPOINT")
            jwks_uri = os.getenv("OIDC_JWKS_URI")
            issuer = os.getenv("OIDC_ISSUER")

            if not all([auth_endpoint, token_endpoint, jwks_uri, issuer]):
                raise ValueError(
                    "For generic OAuth provider, set: OIDC_AUTHORIZATION_ENDPOINT, "
                    "OIDC_TOKEN_ENDPOINT, OIDC_JWKS_URI, OIDC_ISSUER"
                )

            return BoomiOAuthProvider.create_generic_provider(
                client_id=client_id,
                client_secret=client_secret,
                authorization_endpoint=auth_endpoint,
                token_endpoint=token_endpoint,
                jwks_uri=jwks_uri,
                issuer=issuer,
                base_url=base_url
            )
        else:
            raise ValueError(
                f"Unknown OIDC_PROVIDER: {provider_type}. "
                f"Supported: google, auth0, azure, cognito, okta, github, generic"
            )

    @staticmethod
    def create_google_provider(
        client_id: str,
        client_secret: str,
        base_url: str
    ) -> OAuthProxy:
        """Create OAuth provider for Google."""
        issuer = "https://accounts.google.com"
        jwks_uri = "https://www.googleapis.com/oauth2/v3/certs"

        verifier = BoomiOAuthProvider._create_token_verifier(
            issuer=issuer,
            jwks_uri=jwks_uri,
            audience=client_id
        )

        return OAuthProxy(
            upstream_authorization_endpoint="https://accounts.google.com/o/oauth2/v2/auth",
            upstream_token_endpoint="https://oauth2.googleapis.com/token",
            upstream_client_id=client_id,
            upstream_client_secret=client_secret,
            token_verifier=verifier,
            base_url=base_url,
            redirect_path="/auth/callback",
            forward_pkce=True,
            extra_authorize_params={
                "access_type": "offline",  # Get refresh token
                "prompt": "consent"  # Force consent to get refresh token
            }
        )

    @staticmethod
    def create_auth0_provider(
        client_id: str,
        client_secret: str,
        domain: str,
        base_url: str
    ) -> OAuthProxy:
        """Create OAuth provider for Auth0."""
        issuer = f"https://{domain}/"
        jwks_uri = f"https://{domain}/.well-known/jwks.json"

        verifier = BoomiOAuthProvider._create_token_verifier(
            issuer=issuer,
            jwks_uri=jwks_uri,
            audience=client_id
        )

        return OAuthProxy(
            upstream_authorization_endpoint=f"https://{domain}/authorize",
            upstream_token_endpoint=f"https://{domain}/oauth/token",
            upstream_client_id=client_id,
            upstream_client_secret=client_secret,
            token_verifier=verifier,
            base_url=base_url,
            redirect_path="/auth/callback",
            forward_pkce=True
        )

    @staticmethod
    def create_azure_provider(
        client_id: str,
        client_secret: str,
        tenant_id: str,
        base_url: str
    ) -> OAuthProxy:
        """Create OAuth provider for Azure AD (Microsoft Entra ID)."""
        issuer = f"https://login.microsoftonline.com/{tenant_id}/v2.0"
        jwks_uri = f"https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys"

        verifier = BoomiOAuthProvider._create_token_verifier(
            issuer=issuer,
            jwks_uri=jwks_uri,
            audience=client_id
        )

        return OAuthProxy(
            upstream_authorization_endpoint=f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/authorize",
            upstream_token_endpoint=f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token",
            upstream_client_id=client_id,
            upstream_client_secret=client_secret,
            token_verifier=verifier,
            base_url=base_url,
            redirect_path="/auth/callback",
            forward_pkce=True,
            extra_authorize_params={
                "response_mode": "query"
            }
        )

    @staticmethod
    def create_cognito_provider(
        client_id: str,
        client_secret: str,
        region: str,
        user_pool_id: str,
        base_url: str
    ) -> OAuthProxy:
        """Create OAuth provider for AWS Cognito."""
        domain = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}"
        issuer = domain
        jwks_uri = f"{domain}/.well-known/jwks.json"

        verifier = BoomiOAuthProvider._create_token_verifier(
            issuer=issuer,
            jwks_uri=jwks_uri,
            audience=client_id
        )

        # Cognito uses a custom domain for OAuth endpoints
        cognito_domain = os.getenv("OIDC_COGNITO_DOMAIN")
        if not cognito_domain:
            raise ValueError("OIDC_COGNITO_DOMAIN must be set for AWS Cognito (e.g., your-app.auth.us-east-1.amazoncognito.com)")

        return OAuthProxy(
            upstream_authorization_endpoint=f"https://{cognito_domain}/oauth2/authorize",
            upstream_token_endpoint=f"https://{cognito_domain}/oauth2/token",
            upstream_client_id=client_id,
            upstream_client_secret=client_secret,
            token_verifier=verifier,
            base_url=base_url,
            redirect_path="/auth/callback",
            forward_pkce=True
        )

    @staticmethod
    def create_okta_provider(
        client_id: str,
        client_secret: str,
        domain: str,
        base_url: str
    ) -> OAuthProxy:
        """Create OAuth provider for Okta."""
        issuer = f"https://{domain}/oauth2/default"
        jwks_uri = f"https://{domain}/oauth2/default/v1/keys"

        verifier = BoomiOAuthProvider._create_token_verifier(
            issuer=issuer,
            jwks_uri=jwks_uri,
            audience="api://default"
        )

        return OAuthProxy(
            upstream_authorization_endpoint=f"https://{domain}/oauth2/default/v1/authorize",
            upstream_token_endpoint=f"https://{domain}/oauth2/default/v1/token",
            upstream_client_id=client_id,
            upstream_client_secret=client_secret,
            token_verifier=verifier,
            base_url=base_url,
            redirect_path="/auth/callback",
            forward_pkce=True
        )

    @staticmethod
    def create_github_provider(
        client_id: str,
        client_secret: str,
        base_url: str
    ) -> OAuthProxy:
        """
        Create OAuth provider for GitHub.

        Note: GitHub doesn't provide standard OIDC/JWKS, so token validation
        is done via GitHub's user API endpoint instead.
        """

        # GitHub doesn't use standard OIDC, so we need a custom verifier
        class GitHubTokenVerifier(TokenVerifier):
            """Token verifier for GitHub OAuth tokens."""

            def __init__(self):
                self.required_scopes = BoomiOAuthProvider.REQUIRED_SCOPES

            async def verify_token(self, token: str) -> AccessToken | None:
                """Verify GitHub token by calling user API."""
                import httpx

                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.get(
                            "https://api.github.com/user",
                            headers={
                                "Authorization": f"Bearer {token}",
                                "Accept": "application/vnd.github.v3+json"
                            },
                            timeout=10.0
                        )

                        if response.status_code != 200:
                            logger.debug(f"GitHub token validation failed: {response.status_code}")
                            return None

                        user_data = response.json()
                        user_id = str(user_data.get("id", ""))

                        logger.debug(f"Token validated for GitHub user: {user_id}")

                        return AccessToken(
                            token=token,
                            client_id=user_id,
                            scopes=self.required_scopes,  # GitHub doesn't return scopes in token
                            expires_at=None  # GitHub tokens don't expire
                        )

                except Exception as e:
                    logger.debug(f"GitHub token validation failed: {e}")
                    return None

        return OAuthProxy(
            upstream_authorization_endpoint="https://github.com/login/oauth/authorize",
            upstream_token_endpoint="https://github.com/login/oauth/access_token",
            upstream_client_id=client_id,
            upstream_client_secret=client_secret,
            token_verifier=GitHubTokenVerifier(),
            base_url=base_url,
            redirect_path="/auth/callback",
            forward_pkce=False,  # GitHub doesn't support PKCE
            extra_authorize_params={
                "scope": "user:email"  # Basic scope for user info
            }
        )

    @staticmethod
    def create_generic_provider(
        client_id: str,
        client_secret: str,
        authorization_endpoint: str,
        token_endpoint: str,
        jwks_uri: str,
        issuer: str,
        base_url: str,
        audience: Optional[str] = None
    ) -> OAuthProxy:
        """Create OAuth provider for a generic OAuth 2.0 / OIDC provider."""
        verifier = BoomiOAuthProvider._create_token_verifier(
            issuer=issuer,
            jwks_uri=jwks_uri,
            audience=audience or client_id
        )

        return OAuthProxy(
            upstream_authorization_endpoint=authorization_endpoint,
            upstream_token_endpoint=token_endpoint,
            upstream_client_id=client_id,
            upstream_client_secret=client_secret,
            token_verifier=verifier,
            base_url=base_url,
            redirect_path="/auth/callback",
            forward_pkce=True
        )

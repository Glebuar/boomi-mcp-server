"""JWT authentication and authorization for MCP server."""

import jwt
import os
from typing import Optional, Dict, List, Set
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class JWTConfig:
    """JWT configuration for development and production."""
    # Development: HS256 with shared secret
    algorithm: str = "HS256"
    secret_key: Optional[str] = None

    # Production: RS256 with JWKS
    jwks_uri: Optional[str] = None
    issuer: Optional[str] = None
    audience: Optional[str] = None

    # Token validation
    verify_exp: bool = True
    verify_iss: bool = True
    verify_aud: bool = True
    leeway: int = 0  # seconds of leeway for exp/nbf/iat

    @classmethod
    def from_env(cls) -> "JWTConfig":
        """Load JWT config from environment variables."""
        return cls(
            algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
            secret_key=os.getenv("JWT_SECRET_KEY"),
            jwks_uri=os.getenv("JWT_JWKS_URI"),
            issuer=os.getenv("JWT_ISSUER", "https://local-issuer"),
            audience=os.getenv("JWT_AUDIENCE", "boomi-mcp"),
            verify_exp=os.getenv("JWT_VERIFY_EXP", "true").lower() == "true",
            verify_iss=os.getenv("JWT_VERIFY_ISS", "true").lower() == "true",
            verify_aud=os.getenv("JWT_VERIFY_AUD", "true").lower() == "true",
            leeway=int(os.getenv("JWT_LEEWAY", "0")),
        )


@dataclass
class JWTClaims:
    """Parsed and validated JWT claims."""
    subject: str
    issuer: str
    audience: str
    expires_at: datetime
    issued_at: datetime
    scopes: Set[str]
    raw_claims: Dict

    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        return datetime.utcnow() > self.expires_at

    def has_scope(self, scope: str) -> bool:
        """Check if token has a specific scope."""
        return scope in self.scopes

    def has_any_scope(self, *scopes: str) -> bool:
        """Check if token has any of the given scopes."""
        return bool(self.scopes & set(scopes))

    def has_all_scopes(self, *scopes: str) -> bool:
        """Check if token has all of the given scopes."""
        return set(scopes).issubset(self.scopes)


class JWTAuthenticator:
    """
    JWT token authentication and validation.

    Development: Uses HS256 with shared secret
    Production: Uses RS256 with JWKS from identity provider
    """

    def __init__(self, config: Optional[JWTConfig] = None):
        """Initialize JWT authenticator with config."""
        self.config = config or JWTConfig.from_env()

        # Validate configuration
        if self.config.algorithm == "HS256" and not self.config.secret_key:
            raise ValueError(
                "JWT_SECRET_KEY must be set for HS256. Generate with: "
                "python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )

        if self.config.algorithm.startswith("RS") and not self.config.jwks_uri:
            raise ValueError("JWT_JWKS_URI must be set for RS256/RS384/RS512")

    def verify_token(self, token: str) -> JWTClaims:
        """
        Verify and decode JWT token.

        Args:
            token: JWT token string (without 'Bearer ' prefix)

        Returns:
            JWTClaims with parsed claims

        Raises:
            jwt.InvalidTokenError: If token is invalid
            jwt.ExpiredSignatureError: If token is expired
            ValueError: If token is missing required claims
        """
        # Decode options
        options = {
            "verify_signature": True,
            "verify_exp": self.config.verify_exp,
            "verify_iss": self.config.verify_iss,
            "verify_aud": self.config.verify_aud,
        }

        # Verify and decode based on algorithm
        if self.config.algorithm == "HS256":
            payload = jwt.decode(
                token,
                self.config.secret_key,
                algorithms=[self.config.algorithm],
                issuer=self.config.issuer if self.config.verify_iss else None,
                audience=self.config.audience if self.config.verify_aud else None,
                options=options,
                leeway=timedelta(seconds=self.config.leeway)
            )
        else:
            # RS256/RS384/RS512 with JWKS
            # In production, fetch JWKS and validate against public key
            jwks_client = jwt.PyJWKClient(self.config.jwks_uri)
            signing_key = jwks_client.get_signing_key_from_jwt(token)

            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=[self.config.algorithm],
                issuer=self.config.issuer if self.config.verify_iss else None,
                audience=self.config.audience if self.config.verify_aud else None,
                options=options,
                leeway=timedelta(seconds=self.config.leeway)
            )

        # Extract required claims
        if "sub" not in payload:
            raise ValueError("Token missing required 'sub' claim")

        # Parse scopes from 'scope' claim (space-separated string)
        scopes = set()
        if "scope" in payload:
            if isinstance(payload["scope"], str):
                scopes = set(payload["scope"].split())
            elif isinstance(payload["scope"], list):
                scopes = set(payload["scope"])

        return JWTClaims(
            subject=payload["sub"],
            issuer=payload.get("iss", ""),
            audience=payload.get("aud", ""),
            expires_at=datetime.fromtimestamp(payload["exp"]) if "exp" in payload else datetime.max,
            issued_at=datetime.fromtimestamp(payload["iat"]) if "iat" in payload else datetime.utcnow(),
            scopes=scopes,
            raw_claims=payload,
        )

    def authorize(self, claims: JWTClaims, required_scopes: List[str]) -> bool:
        """
        Check if token has required scopes.

        Args:
            claims: Parsed JWT claims
            required_scopes: List of required scopes (user must have ALL)

        Returns:
            True if authorized, False otherwise
        """
        return claims.has_all_scopes(*required_scopes)

    @staticmethod
    def generate_dev_token(
        subject: str,
        secret_key: str,
        scopes: List[str],
        issuer: str = "https://local-issuer",
        audience: str = "boomi-mcp",
        expires_in_minutes: int = 30,
    ) -> str:
        """
        Generate a development JWT token (HS256).

        Args:
            subject: User identifier (email, username, etc.)
            secret_key: Shared secret for HS256
            scopes: List of scopes to grant
            issuer: Token issuer
            audience: Token audience
            expires_in_minutes: Token expiration time

        Returns:
            JWT token string
        """
        now = datetime.utcnow()
        payload = {
            "sub": subject,
            "iss": issuer,
            "aud": audience,
            "iat": now,
            "exp": now + timedelta(minutes=expires_in_minutes),
            "scope": " ".join(scopes),
        }

        return jwt.encode(payload, secret_key, algorithm="HS256")


# Scope definitions
SCOPE_SECRETS_READ = "secrets:read"
SCOPE_SECRETS_WRITE = "secrets:write"
SCOPE_BOOMI_READ = "boomi:read"
SCOPE_BOOMI_WRITE = "boomi:write"
SCOPE_ADMIN = "admin"


# Production migration notes:
"""
PRODUCTION RS256/JWKS MIGRATION:

1. Set up identity provider (IdP) with JWKS endpoint:
   - Auth0: https://{tenant}.auth0.com/.well-known/jwks.json
   - Okta: https://{domain}/oauth2/default/v1/keys
   - Azure AD: https://login.microsoftonline.com/{tenant}/discovery/v2.0/keys
   - AWS Cognito: https://cognito-idp.{region}.amazonaws.com/{userPoolId}/.well-known/jwks.json

2. Update environment variables:
   JWT_ALGORITHM=RS256
   JWT_JWKS_URI=https://your-idp.com/.well-known/jwks.json
   JWT_ISSUER=https://your-idp.com/
   JWT_AUDIENCE=boomi-mcp
   # Remove JWT_SECRET_KEY (not needed for RS256)

3. Configure IdP to issue tokens with required claims:
   - sub: User unique identifier
   - iss: Your IdP issuer URL
   - aud: "boomi-mcp"
   - scope: Space-separated list of scopes (e.g., "secrets:write boomi:read")
   - exp: Token expiration (recommend 1 hour max for production)

4. Set up token refresh flow:
   - Use short-lived access tokens (1 hour)
   - Use refresh tokens for long-lived sessions
   - Implement token rotation

5. Add rate limiting and monitoring:
   - Track failed authentication attempts
   - Alert on suspicious patterns
   - Log all authentication events (without logging the token itself)

6. Consider adding:
   - Token revocation check (against IdP or local cache)
   - MFA enforcement via IdP
   - IP allowlisting for sensitive operations
   - Scope-based rate limits
"""

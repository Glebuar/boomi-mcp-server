#!/usr/bin/env python3
"""Generate a development JWT token for MCP authentication."""

import os
import time
import jwt
from datetime import datetime, timedelta

# Load environment variables from .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("[WARN] python-dotenv not installed, using system environment variables")

# Configuration
SECRET = os.getenv("MCP_JWT_SECRET", "change-this-dev-secret")
ALGORITHM = os.getenv("MCP_JWT_ALG", "HS256")
ISSUER = os.getenv("MCP_JWT_ISSUER", "https://local-issuer")
AUDIENCE = os.getenv("MCP_JWT_AUDIENCE", "boomi-mcp")

# Token claims
SUBJECT = os.getenv("JWT_SUBJECT", "dev-user@example.com")
SCOPES = os.getenv("JWT_SCOPES", "secrets:read secrets:write boomi:read")
EXPIRES_IN_MINUTES = int(os.getenv("JWT_EXPIRES_IN_MINUTES", "480"))  # 8 hours for development

def generate_token(
    subject: str = SUBJECT,
    scopes: str = SCOPES,
    expires_in_minutes: int = EXPIRES_IN_MINUTES
) -> str:
    """Generate a JWT token for development.

    Args:
        subject: User identifier (email)
        scopes: Space-separated list of OAuth scopes
        expires_in_minutes: Token expiration time (default: 480 minutes / 8 hours for dev)

    Returns:
        JWT token string
    """
    now = datetime.utcnow()
    exp = now + timedelta(minutes=expires_in_minutes)

    claims = {
        "sub": subject,
        "iss": ISSUER,
        "aud": AUDIENCE,
        "iat": now,
        "exp": exp,
        "scope": scopes,
        "scopes": scopes.split(),  # Some implementations expect array
    }

    token = jwt.encode(claims, SECRET, algorithm=ALGORITHM)

    print("\n" + "=" * 70)
    print("🔐 JWT Token Generated")
    print("=" * 70)
    print(f"Subject:    {subject}")
    print(f"Scopes:     {scopes}")
    print(f"Issued at:  {now.isoformat()}")
    print(f"Expires at: {exp.isoformat()}")
    print(f"Valid for:  {expires_in_minutes} minutes")
    print("=" * 70)
    print("\nToken:\n")
    print(token)
    print("\n" + "=" * 70)
    print("\nTo use this token with Claude Code:")
    print("1. Export it as an environment variable:")
    print(f"   export MCP_JWT='{token}'")
    print("\n2. Register the MCP server:")
    print("   claude mcp add-json boomi '{")
    print('     "type": "http",')
    print('     "url": "http://127.0.0.1:8000/mcp",')
    print('     "headers": { "Authorization": "Bearer ${MCP_JWT}" }')
    print("   }'")
    print("\n3. Or add to your Claude Code config manually")
    print("=" * 70 + "\n")

    return token

if __name__ == "__main__":
    import sys

    # Parse command line arguments
    subject = sys.argv[1] if len(sys.argv) > 1 else SUBJECT
    expires_in = int(sys.argv[2]) if len(sys.argv) > 2 else EXPIRES_IN_MINUTES

    token = generate_token(subject=subject, expires_in_minutes=expires_in)

# Boomi MCP Server

**Secure FastMCP server for integrating Boomi Platform APIs with Claude Code**

A production-ready Model Context Protocol (MCP) server that enables Claude Code to interact with Boomi Platform APIs using authenticated, per-user credentials with JWT-based security.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)
![FastMCP](https://img.shields.io/badge/FastMCP-2.12.4-green.svg)

## Features

- ⚡ **Auto-Configuration** - Automatically loads credentials from `.env` on startup - no manual setup required!
- 🔐 **OAuth 2.0 Authentication** - Industry-standard OAuth flow with Google, Auth0, Azure AD, AWS Cognito, Okta, GitHub
- 🔄 **Automatic Token Refresh** - Seamless session extension without re-authentication
- 🔒 **Secure Credential Storage** - Per-user encrypted credential management with GCP Secret Manager (automatic persistence across restarts)
- 🌐 **Streamable HTTP Transport** - Claude Code compatible remote MCP server
- 📦 **4 Ready-to-Use Tools** - Complete credential lifecycle management and Boomi API integration
- 🚀 **Production Ready** - Enterprise-grade security and deployment patterns
- ☁️ **Cloud Deployment** - Docker, Kubernetes, GCP Cloud Run, AWS ECS, Azure Container Apps support

## Deployment Options

This server supports both local development and cloud production deployments:

- **Local Development**: `server.py` - Quick start for testing and development
- **Cloud Production**: `cloud_server.py` - FastAPI wrapper with health checks, metrics, and cloud integration

📘 **For cloud deployment, see [Cloud Deployment Guide](README-CLOUD.md)**

## Quick Start

### Prerequisites

- Python 3.11 or higher
- Claude Code CLI
- Boomi account with API access
- OAuth 2.0 application registered with an Identity Provider (Google, Auth0, etc.)
  - OR: Use JWT mode for local development/testing (not recommended for production)

### Installation

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd boomi-mcp-server

# 2. Create virtual environment and install dependencies
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install --upgrade pip
pip install -r requirements.txt

# 3. Install Boomi Python SDK
pip install git+https://github.com/Glebuar/boomi-python.git

# 4. Configure environment
cp .env.example .env
# Edit .env and set your JWT_SECRET (generate with: python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
```

### Configuration

Create a `.env` file with your settings. See `.env.example` for all options.

**Option 1: OAuth 2.0 (Recommended)**

```bash
# Enable OAuth
OAUTH_ENABLED=true
OIDC_PROVIDER=google  # or auth0, azure, cognito, okta, github, generic
OIDC_CLIENT_ID=your-client-id-here
OIDC_CLIENT_SECRET=your-client-secret-here
OIDC_BASE_URL=http://localhost:8000

# Server Configuration
MCP_HOST=127.0.0.1
MCP_PORT=8000
MCP_PATH=/mcp

# Storage Configuration (GCP Secret Manager)
SECRETS_BACKEND=gcp
GCP_PROJECT_ID=your-gcp-project-id
```

**Option 2: JWT (Development/Testing Only)**

```bash
# Disable OAuth (fallback to JWT)
OAUTH_ENABLED=false

# JWT Configuration
MCP_JWT_ALG=HS256
MCP_JWT_SECRET=your-secret-key-here
MCP_JWT_ISSUER=https://local-issuer
MCP_JWT_AUDIENCE=boomi-mcp

# Server Configuration
MCP_HOST=127.0.0.1
MCP_PORT=8000
MCP_PATH=/mcp

# Storage Configuration (GCP Secret Manager)
SECRETS_BACKEND=gcp
GCP_PROJECT_ID=your-gcp-project-id
```

### Start the Server

```bash
# Start the MCP server
python3 server.py
```

The server will start on `http://127.0.0.1:8000/mcp`

### Generate JWT Token

```bash
# Generate a development token (valid for 8 hours by default)
python3 generate_token.py

# Custom token with different expiry (in minutes)
python3 generate_token.py your-email@example.com 120  # 2 hours
python3 generate_token.py your-email@example.com 1440  # 24 hours
```

**Note:** The default token expiration is 8 hours for development convenience. For production, use shorter-lived tokens (1 hour) with a refresh token mechanism.

### Connect Claude Code

```bash
# 1. Export the JWT token
export MCP_JWT='<your-generated-token>'

# 2. Register the server with Claude Code
claude mcp add-json boomi '{
  "type": "http",
  "url": "http://127.0.0.1:8000/mcp",
  "headers": { "Authorization": "Bearer ${MCP_JWT}" }
}'

# 3. Verify connection
claude mcp list
```

### Test the Integration

The server automatically loads credentials from `.env` on startup. You can immediately start using it!

**Simple usage** - just ask in natural language:
```
Show me my Boomi account information
```

**Available MCP tools** (type `/mcp` in Claude Code to see them):

1. **Get account information** (uses .env credentials automatically):
   ```
   Run boomi_account_info
   ```

2. **Store additional credentials** (optional):
   ```
   Run set_boomi_credentials with profile='sandbox',
   username='BOOMI_TOKEN.your@email.com',
   password='your-api-token',
   account_id='your-account-id'
   ```

3. **List stored profiles:**
   ```
   Run list_boomi_profiles
   ```

## Architecture

```
                           OAuth 2.0 Flow
┌──────────────┐                                   ┌──────────────┐
│              │  1. Navigate to /auth/login       │   Identity   │
│    User      │ ─────────────────────────────────>│   Provider   │
│  (Browser)   │                                   │ (Google,etc) │
│              │<─────────────────────────────────│              │
└──────────────┘  2. Authenticate & Consent        └──────────────┘
       │
       │ 3. OAuth Token (with refresh)
       ▼
┌──────────────┐  Bearer Token  ┌──────────────┐  Encrypted  ┌──────────────┐
│  Claude Code │ ──────────────>│  MCP Server  │ ──────────> │ GCP Secret   │
│              │   (Auto-refresh)│   (FastMCP)  │   Storage   │   Manager    │
└──────────────┘                 └──────────────┘             └──────────────┘
                                        │
                                        │ API Calls
                                        ▼
                                 ┌──────────────┐
                                 │  Boomi API   │
                                 └──────────────┘
```

**Key Components:**

1. **OAuth Provider** - Handles authentication flow, token validation, and automatic refresh
2. **MCP Server** - FastMCP-based server with tools for Boomi API integration
3. **Credential Store** - Secure per-user credential storage with GCP Secret Manager (encrypted at rest, automatic versioning, audit logging)
4. **Boomi SDK** - Python SDK for interacting with Boomi Platform APIs

## Available Tools

| Tool | Description |
|------|-------------|
| `set_boomi_credentials` | Store Boomi credentials for a profile (encrypted in GCP Secret Manager) |
| `list_boomi_profiles` | List all stored profiles for the user |
| `delete_boomi_profile` | Delete a stored profile |
| `boomi_account_info` | Retrieve account information from Boomi API |

## Security

### Authentication Methods

The Boomi MCP Server supports two authentication methods:

1. **OAuth 2.0 / OIDC (Recommended)** - Standard OAuth 2.0 flow with support for major Identity Providers
2. **JWT Tokens (Fallback)** - Development/testing only, not recommended for production

### OAuth 2.0 Authentication (Production)

**OAuth 2.0 is the recommended authentication method** for production deployments. It provides:

- ✅ Industry-standard authentication
- ✅ Automatic token refresh for long-lived sessions
- ✅ Support for MFA and enterprise policies
- ✅ Secure consent flow prevents confused deputy attacks
- ✅ No manual token generation needed

**Supported Identity Providers:**
- Google OAuth
- Auth0
- Azure AD (Microsoft Entra ID)
- AWS Cognito
- Okta
- GitHub
- Generic OAuth 2.0 / OIDC providers

**Setup Steps:**

1. **Register OAuth Application** with your Identity Provider:

   For Google (example):
   - Go to https://console.cloud.google.com/apis/credentials
   - Create OAuth 2.0 Client ID (Web application)
   - Add authorized redirect URI: `http://localhost:8000/auth/callback` (local) or `https://your-domain.com/auth/callback` (production)
   - Copy Client ID and Secret

2. **Configure Environment:**
   ```bash
   # Enable OAuth
   OAUTH_ENABLED=true
   OIDC_PROVIDER=google
   OIDC_CLIENT_ID=your-client-id-here
   OIDC_CLIENT_SECRET=your-client-secret-here
   OIDC_BASE_URL=http://localhost:8000  # or your production URL
   ```

3. **Start Server and Login:**
   ```bash
   python3 server.py
   ```

   The server will display OAuth endpoints. Open in browser:
   ```
   http://localhost:8000/auth/login
   ```

   You'll be redirected to your Identity Provider to authenticate. After successful login, you'll be redirected back to the server.

4. **Connect Claude Code:**

   The OAuth token will be provided after login. Use it to connect Claude Code:
   ```bash
   export MCP_OAUTH_TOKEN='<token-from-browser>'

   claude mcp add-json boomi '{
     "type": "http",
     "url": "http://localhost:8000/mcp",
     "headers": { "Authorization": "Bearer ${MCP_OAUTH_TOKEN}" }
   }'
   ```

**Token Refresh:**

OAuth tokens are automatically refreshed by the server when they expire. You don't need to manually refresh or re-authenticate unless:
- The server restarts (in-memory token store)
- The refresh token expires (typically 90 days or more)
- You revoke access in your Identity Provider

### JWT Authentication (Development/Testing Only)

For local development and testing, you can use JWT authentication:

```bash
# Disable OAuth (fallback to JWT)
OAUTH_ENABLED=false

# Configure JWT
MCP_JWT_ALG=HS256
MCP_JWT_SECRET=your-secret-key-here
MCP_JWT_ISSUER=https://local-issuer
MCP_JWT_AUDIENCE=boomi-mcp
```

Generate a token:
```bash
python3 generate_token.py your-email@example.com 480  # 8 hours
```

**⚠️ JWT mode is NOT suitable for production use!** Use OAuth 2.0 for production deployments.

### Cloud Deployment Security

For production environments, credentials are automatically stored in GCP Secret Manager with:
- ✅ **Encryption at rest and in transit**
- ✅ **Automatic versioning** - rollback capability
- ✅ **Audit logging** - Cloud Logging tracks all access
- ✅ **IAM-based access control**
- ✅ **Persistent storage** - survives container restarts

Also configure:

1. **HTTPS with TLS:**
   - Deploy behind Caddy or NGINX
   - Use Let's Encrypt certificates
   - Enable rate limiting

2. **Enhanced Security:**
   - OAuth 2.0 with automatic token refresh
   - Request logging and monitoring
   - MFA enforcement via IdP
   - All credentials encrypted in GCP Secret Manager

See the production deployment section in `src/boomi_mcp/credentials.py` and `src/boomi_mcp/auth.py` for detailed migration notes.

## Project Structure

```
boomi-mcp-server/
├── server.py              # Main FastMCP server
├── generate_token.py      # JWT token generator
├── requirements.txt       # Python dependencies
├── .env.example          # Configuration template
├── src/
│   └── boomi_mcp/
│       ├── credentials.py # Credential storage with prod notes
│       ├── auth.py        # JWT authentication with RS256 examples
│       └── tools.py       # MCP tool implementations
├── pyproject.toml        # Project metadata
└── README.md             # This file
```

## Configuration Options

### JWT Authentication

```bash
# Development (HS256 - shared secret)
MCP_JWT_ALG=HS256
MCP_JWT_SECRET=your-secret-here

# Production (RS256 - public/private key)
MCP_JWT_ALG=RS256
MCP_JWT_JWKS_URI=https://your-idp.com/.well-known/jwks.json
MCP_JWT_ISSUER=https://your-idp.com/
```

### Server Settings

```bash
MCP_HOST=127.0.0.1              # Bind address (0.0.0.0 for all interfaces)
MCP_PORT=8000                   # Server port
MCP_PATH=/mcp                   # MCP endpoint path
SECRETS_BACKEND=gcp             # Secret storage backend (gcp, aws, azure, sqlite)
GCP_PROJECT_ID=your-project-id  # GCP project ID for Secret Manager
```

## Troubleshooting

### Server Won't Start

```bash
# Check if port is in use
lsof -i :8000

# Verify Python version
python3 --version  # Should be 3.11+

# Check dependencies
pip list | grep -E "(fastmcp|pydantic|pyjwt)"
```

### Authentication Failures

```bash
# Verify token is set
echo $MCP_JWT

# Check token claims (decode without verification)
python3 -c "
import jwt
token = '$MCP_JWT'
print(jwt.decode(token, options={'verify_signature': False}))
"

# Generate new token
python3 generate_token.py
```

### Boomi API Errors

- Verify credentials are correct
- Check account_id format
- Ensure API access is enabled in Boomi
- Test credentials directly:
  ```bash
  curl -u "USERNAME:PASSWORD" \
    "https://api.boomi.com/api/rest/v1/ACCOUNT_ID/Account/ACCOUNT_ID"
  ```

## Development

### Running Tests

```bash
# Install dev dependencies
pip install pytest pytest-asyncio

# Run tests (when implemented)
pytest tests/
```

### Code Style

This project uses:
- Black for code formatting
- Ruff for linting
- Pydantic for data validation

```bash
# Format code
black .

# Lint
ruff check .
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Resources

- **Cloud Deployment Guide:** [README-CLOUD.md](README-CLOUD.md)
- **FastMCP Documentation:** https://gofastmcp.com
- **Boomi Python SDK:** https://github.com/Glebuar/boomi-python
- **MCP Specification:** https://modelcontextprotocol.io
- **Boomi Platform API:** https://help.boomi.com/docs/atomsphere/integration/platform_management/c-atm-platform_api_2cf25c18-ca93-43d2-a53e-048017d0b102/

## Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Include relevant logs (with secrets redacted)
- Describe your environment and steps to reproduce

## Acknowledgments

- Built with [FastMCP](https://gofastmcp.com) framework
- Integrates [Boomi Python SDK](https://github.com/Glebuar/boomi-python)
- Implements the [Model Context Protocol](https://modelcontextprotocol.io)

---

**Note:** This server is designed for development and testing. For production deployments, implement the security enhancements documented in the source code comments.

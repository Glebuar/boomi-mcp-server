# Boomi MCP Server

**Secure FastMCP server for integrating Boomi Platform APIs with Claude Code**

A production-ready Model Context Protocol (MCP) server that enables Claude Code to interact with Boomi Platform APIs using authenticated, per-user credentials with JWT-based security.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)
![FastMCP](https://img.shields.io/badge/FastMCP-2.12.4-green.svg)

## Features

- 🔐 **JWT Authentication** - Industry-standard authentication (HS256 for development, RS256+JWKS for production)
- 🔒 **Secure Credential Storage** - Per-user encrypted credential management (SQLite for dev, cloud secret managers for production)
- 🎯 **Scope-based Authorization** - Fine-grained access control using OAuth 2.0 scopes
- 🌐 **Streamable HTTP Transport** - Claude Code compatible remote MCP server
- 📦 **4 Ready-to-Use Tools** - Complete credential lifecycle management and Boomi API integration
- 🚀 **Production Ready** - Clear upgrade paths for enterprise deployment

## Quick Start

### Prerequisites

- Python 3.11 or higher
- Claude Code CLI
- Boomi account with API access
- Basic understanding of JWT tokens

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

Create a `.env` file with your settings:

```bash
# JWT Configuration (Development - HS256)
MCP_JWT_ALG=HS256
MCP_JWT_SECRET=your-secret-key-here
MCP_JWT_ISSUER=https://local-issuer
MCP_JWT_AUDIENCE=boomi-mcp

# Server Configuration
MCP_HOST=127.0.0.1
MCP_PORT=8000
MCP_PATH=/mcp

# Storage Configuration
SECRETS_DB=secrets.sqlite
```

### Start the Server

```bash
# Start the MCP server
python3 server.py
```

The server will start on `http://127.0.0.1:8000/mcp`

### Generate JWT Token

```bash
# Generate a development token (valid for 30 minutes)
python3 generate_token.py

# Custom token with 2-hour expiry
python3 generate_token.py your-email@example.com 120
```

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

In Claude Code, type `/mcp` to see available tools:

1. **Store credentials:**
   ```
   Run set_boomi_credentials with profile='sandbox',
   username='BOOMI_TOKEN.your@email.com',
   password='your-api-token',
   account_id='your-account-id'
   ```

2. **List profiles:**
   ```
   Run list_boomi_profiles
   ```

3. **Get account information:**
   ```
   Run boomi_account_info with profile='sandbox'
   ```

## Architecture

```
┌──────────────┐  JWT Auth  ┌──────────────┐  Encrypted  ┌──────────┐
│  Claude Code │ ─────────> │  MCP Server  │ ──────────> │  SQLite  │
│              │   Bearer    │   (FastMCP)  │   Storage   │ secrets  │
└──────────────┘             └──────────────┘             └──────────┘
                                    │
                                    │ API Calls
                                    ▼
                             ┌──────────────┐
                             │  Boomi API   │
                             └──────────────┘
```

## Available Tools

| Tool | Description | Required Scope |
|------|-------------|----------------|
| `set_boomi_credentials` | Store Boomi credentials for a profile | `secrets:write` |
| `list_boomi_profiles` | List all stored profiles for the user | `secrets:read` |
| `delete_boomi_profile` | Delete a stored profile | `secrets:write` |
| `boomi_account_info` | Retrieve account information from Boomi API | `boomi:read` |

## Security

### Development Environment

The default configuration uses:
- HS256 JWT with shared secret
- SQLite credential storage
- HTTP localhost-only access
- 30-minute token expiry

**⚠️ Not suitable for production use!**

### Production Deployment

For production environments, upgrade to:

1. **RS256 JWT with JWKS:**
   ```bash
   export MCP_JWT_ALG=RS256
   export MCP_JWT_JWKS_URI=https://your-idp.com/.well-known/jwks.json
   export MCP_JWT_ISSUER=https://your-idp.com/
   ```

2. **Cloud Secret Manager:**
   - AWS Secrets Manager
   - GCP Secret Manager
   - Azure Key Vault
   - HashiCorp Vault

3. **HTTPS with TLS:**
   - Deploy behind Caddy or NGINX
   - Use Let's Encrypt certificates
   - Enable rate limiting

4. **Enhanced Security:**
   - 1-hour token expiry maximum
   - Token refresh flow
   - Request logging and monitoring
   - MFA enforcement via IdP

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
MCP_HOST=127.0.0.1        # Bind address (0.0.0.0 for all interfaces)
MCP_PORT=8000             # Server port
MCP_PATH=/mcp             # MCP endpoint path
SECRETS_DB=secrets.sqlite # Database file path
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

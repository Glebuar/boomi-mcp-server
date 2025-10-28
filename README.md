# Boomi MCP Server

**Secure MCP server for Boomi Platform API integration with Claude Code**

A production-ready Model Context Protocol (MCP) server that enables Claude Code and other MCP clients to interact with Boomi Platform APIs using OAuth 2.0 authentication and secure credential storage.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)
![FastMCP](https://img.shields.io/badge/FastMCP-2.13.0-green.svg)

**🌐 Live Service**: [https://boomi.renera.ai](https://boomi.renera.ai)

---

## Features

- 🔐 **Google OAuth 2.0** - Secure authentication with consent screen
- 🔒 **GCP Secret Manager** - Encrypted per-user credential storage
- 👤 **Multi-Profile Support** - Store up to 10 Boomi account profiles per user
- 🌐 **Web UI** - Browser-based credential management
- ✅ **Credential Validation** - Test credentials before saving
- 🚀 **Auto-Deploy** - GitHub push → Cloud Build → Cloud Run
- 📦 **MCP Tools** - Account info, profile management
- ☁️ **Cloud Native** - Running on Google Cloud Run

---

## Quick Start

### For Users

1. **Visit the Web UI**: [https://boomi.renera.ai](https://boomi.renera.ai)
2. **Login with Google** - OAuth authentication
3. **Add Boomi Credentials**:
   - Email: Your Boomi account email
   - API Token: Your Boomi API token
   - Account ID: Your Boomi account ID
   - Profile Name: A name for this credential set (e.g., "production", "sandbox")

4. **Connect Claude Code**:
```bash
claude mcp add --transport http boomi https://boomi.renera.ai/mcp
```

5. **Authorize** - Browser opens for OAuth consent, click "Approve"

6. **Use MCP Tools**:
```
Show me my Boomi account information from the production profile
```

---

## Architecture

```
┌──────────────┐
│    User      │
│  (Browser)   │
└──────┬───────┘
       │ 1. Visit https://boomi.renera.ai
       │ 2. Google OAuth Login
       ▼
┌──────────────────────────────────────┐
│      Boomi MCP Server (Cloud Run)    │
│  ┌────────────┐    ┌──────────────┐ │
│  │  Web UI    │    │  MCP Server  │ │
│  │ (FastAPI)  │    │  (FastMCP)   │ │
│  └────────────┘    └──────────────┘ │
└───────┬──────────────────┬───────────┘
        │                  │
        │ Store            │ Retrieve
        │ Credentials      │ Credentials
        ▼                  ▼
┌──────────────────────────────────────┐
│      GCP Secret Manager              │
│  boomi-mcp-{user-id}-{profile-name}  │
└──────────────────────────────────────┘
                    │
                    │ API Calls
                    ▼
             ┌──────────────┐
             │  Boomi API   │
             └──────────────┘
```

---

## Available MCP Tools

### 1. `boomi_account_info(profile: str)`

Get Boomi account information from a specific profile.

**Parameters:**
- `profile` (required): Profile name (e.g., "production", "sandbox")

**Example:**
```
Get account info from the production profile
```

### 2. `list_boomi_profiles()`

List all saved Boomi credential profiles for the authenticated user.

**Example:**
```
Show me my Boomi profiles
```

---

## Deployment

### Current Production Deployment

- **Hosting**: Google Cloud Run (us-central1)
- **URL**: https://boomi.renera.ai
- **CI/CD**: Automated via GitHub
- **Region**: us-central1
- **Authentication**: Google OAuth 2.0

### CI/CD Pipeline

Automatic deployment on push to `main` branch:

```
GitHub Push → Cloud Build → Docker Build → Artifact Registry → Cloud Run
```

### Manual Deployment

If you need to deploy manually:

```bash
# Authenticate with GCP
gcloud auth login
gcloud config set project boomimcp

# Build and deploy
gcloud builds submit --config cloudbuild.yaml.example

# Or use the trigger
git push origin main
```

---

## Configuration

### Environment Variables (Cloud Run)

Configured in Cloud Run service using GCP Secret Manager:

```bash
OIDC_CLIENT_ID          # From secret: oidc-client-id
OIDC_CLIENT_SECRET      # From secret: oidc-client-secret
OIDC_BASE_URL           # https://boomi.renera.ai
SESSION_SECRET          # From secret: session-secret
SECRETS_BACKEND         # gcp
GCP_PROJECT_ID          # boomimcp
```

### User Credentials Storage

User Boomi credentials are stored in GCP Secret Manager:
- Format: `boomi-mcp-{user-id}-{profile-name}`
- Example: `boomi-mcp-glebuar-at-gmail-com-production`
- Encryption: At rest and in transit
- Access: IAM-controlled, audit logged

---

## Local Development

### Prerequisites

- Python 3.11+
- Google Cloud SDK
- Access to GCP project with Secret Manager enabled

### Setup

```bash
# Clone repository
git clone https://github.com/RenEra-ai/boomi-mcp-server.git
cd boomi-mcp-server

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt -r requirements-cloud.txt

# Configure environment
cp .env.example .env
# Edit .env with your OAuth credentials
```

### Run Locally

```bash
# Set environment variables
export OIDC_CLIENT_ID="your-google-oauth-client-id"
export OIDC_CLIENT_SECRET="your-google-oauth-client-secret"
export OIDC_BASE_URL="http://localhost:8080"
export SESSION_SECRET="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export SECRETS_BACKEND=gcp
export GCP_PROJECT_ID=boomimcp

# Run server
python server_http.py
```

Visit http://localhost:8080 to access the web UI.

---

## Project Structure

```
boomi-mcp-server/
├── server.py                  # Core MCP server with FastMCP
├── server_http.py             # HTTP wrapper with OAuth middleware
├── src/boomi_mcp/
│   ├── cloud_auth.py          # OAuth provider implementations
│   ├── cloud_secrets.py       # Secret Manager backends (GCP/AWS/Azure)
│   └── tools.py               # MCP tool implementations
├── templates/
│   ├── credentials.html       # Web UI for credential management
│   └── login.html             # OAuth login page
├── static/
│   └── favicon.png            # RenEra logo
├── requirements.txt           # Core dependencies
├── requirements-cloud.txt     # Cloud provider SDKs
├── Dockerfile                 # Multi-stage Docker build
├── .env.example               # Environment configuration template
└── README.md                  # This file
```

---

## Security Features

### Authentication & Authorization
- ✅ Google OAuth 2.0 with PKCE
- ✅ OAuth consent screen (prevents confused deputy attacks)
- ✅ Session-based authentication with cryptographic signing
- ✅ Per-user credential isolation

### Data Protection
- ✅ HTTPS-only (enforced by Cloud Run)
- ✅ Credentials encrypted at rest (GCP Secret Manager)
- ✅ Credentials encrypted in transit (TLS)
- ✅ No credentials in environment variables
- ✅ Audit logging via Cloud Logging

### Access Control
- ✅ IAM-based access to secrets
- ✅ Profile limit (10 per user)
- ✅ Credential validation before storage
- ✅ Automatic session expiration

---

## Monitoring & Logs

### View Logs

```bash
# Recent logs
gcloud run services logs read boomi-mcp-server \
  --region us-central1 --limit 50 --project boomimcp

# Follow logs in real-time
gcloud run services logs tail boomi-mcp-server \
  --region us-central1 --project boomimcp

# Check service status
gcloud run services describe boomi-mcp-server \
  --region us-central1 --project boomimcp
```

### Cloud Console

- **Service**: https://console.cloud.google.com/run/detail/us-central1/boomi-mcp-server
- **Logs**: https://console.cloud.google.com/run/detail/us-central1/boomi-mcp-server/logs
- **Builds**: https://console.cloud.google.com/cloud-build/builds?project=boomimcp

---

## Troubleshooting

### Cannot Connect to MCP Server

1. Check service is running:
```bash
curl https://boomi.renera.ai/
```

2. Verify OAuth consent was completed:
   - Browser should open during `claude mcp add`
   - Click "Approve" on consent screen
   - Check for success message

3. Check Claude Code MCP configuration:
```bash
claude mcp list
```

### Credentials Not Saving

1. Verify all fields are filled in web UI
2. Check credential validation passes
3. Review browser console for errors (F12)
4. Check server logs for error messages

### API Errors

1. Verify Boomi credentials are correct:
   - Email should be registered in Boomi
   - API token should be valid
   - Account ID should match your account

2. Test credentials directly:
```bash
curl -u "BOOMI_TOKEN.email@example.com:your-token" \
  "https://api.boomi.com/api/rest/v1/YOUR_ACCOUNT_ID/Account/YOUR_ACCOUNT_ID"
```

---

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## Technical Details

### FastMCP Version

Currently using **FastMCP 2.13.0** which includes:
- OAuth consent screen
- Session middleware support
- Google OAuth provider

**Note**: Server branding (custom icons, site URL) requires FastMCP 2.14.0+ (not yet released).

### Session Management

- Uses `SessionMiddleware` from Starlette
- Session secret stored in GCP Secret Manager
- Sessions persist across requests via cryptographically signed cookies
- Max age: 1 hour (configurable)

### Profile Management

- Maximum 10 profiles per user
- Profile names are required (no default profile)
- Profile names must be unique per user
- Examples: "production", "sandbox", "dev", "staging"

---

## Resources

- **Live Service**: https://boomi.renera.ai
- **GitHub Repository**: https://github.com/RenEra-ai/boomi-mcp-server
- **FastMCP Documentation**: https://gofastmcp.com
- **Boomi Python SDK**: https://github.com/RenEra-ai/boomi-python
- **MCP Specification**: https://modelcontextprotocol.io
- **Boomi Platform API**: https://help.boomi.com/docs/atomsphere/integration/platform_management/c-atm-platform_api_2cf25c18-ca93-43d2-a53e-048017d0b102/

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

## Support

For issues, questions, or feature requests:
- Open an issue on [GitHub](https://github.com/RenEra-ai/boomi-mcp-server/issues)
- Include relevant logs (with secrets redacted)
- Describe your environment and steps to reproduce

---

## Acknowledgments

- Built with [FastMCP](https://gofastmcp.com) framework
- Integrates [Boomi Python SDK](https://github.com/RenEra-ai/boomi-python)
- Implements the [Model Context Protocol](https://modelcontextprotocol.io)
- Powered by Google Cloud Platform

---

**Last Updated**: 2025-10-28
**Status**: ✅ Production (Stable)
**Version**: FastMCP 2.13.0

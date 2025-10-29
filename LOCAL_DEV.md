# Local Development Setup

Fast local development environment for testing new MCP tools without Docker or cloud deployment.

## Quick Start

```bash
# 1. Setup (one time only)
./setup_local.sh

# 2. Run the local server
./run_local.sh

# 3. In another terminal, test with Claude Code
claude mcp add boomi-local stdio -- /Users/gleb/Documents/Projects/Boomi/boomi-mcp-server/.venv/bin/python /Users/gleb/Documents/Projects/Boomi/boomi-mcp-server/server_local.py
```

## Features

- ✅ **No OAuth** - Instant testing without authentication
- ✅ **No Docker** - No build time
- ✅ **Fast startup** - Instant reload when you change code
- ✅ **Local storage** - Credentials in `~/.boomi_mcp_local_secrets.json`
- ✅ **Additional tools** - `set_boomi_credentials` and `delete_boomi_profile` available
- ⚠️ **NOT for production** - Use server.py with OAuth for production

## Available Tools

1. **`list_boomi_profiles()`** - List all saved credential profiles
2. **`set_boomi_credentials(profile, account_id, username, password)`** - Store Boomi credentials
3. **`delete_boomi_profile(profile)`** - Delete a credential profile
4. **`boomi_account_info(profile)`** - Get account info from Boomi API

## Setup Details

The setup script:
1. Creates a fresh Python virtual environment (`.venv`)
2. Installs all dependencies from `requirements.txt`
3. Checks for boomi-python SDK

## Troubleshooting

### Import Error: boomi-python not found

The server expects boomi-python to be at `../boomi-python` relative to this directory.

```bash
cd /Users/gleb/Documents/Projects/Boomi/
git clone https://github.com/RenEra-ai/boomi-python.git
```

### Virtual Environment Issues

If you're having issues with the virtual environment:

```bash
# Remove and recreate
rm -rf .venv
./setup_local.sh
```

## File Structure

```
boomi-mcp-server/
├── server_local.py              # Local development server (no OAuth)
├── run_local.sh                 # Start the local server
├── setup_local.sh               # Setup script (creates venv)
├── src/boomi_mcp/
│   └── local_secrets.py         # Local file-based storage
└── .venv/                       # Virtual environment (created by setup)
```

## Making Changes

After making changes to `server_local.py`:
1. Stop the server (Ctrl+C)
2. Run `./run_local.sh` again
3. Changes are reflected immediately (no Docker rebuild needed)

## Credential Storage

Credentials are stored in: `~/.boomi_mcp_local_secrets.json`

Format:
```json
{
  "local-dev-user": {
    "production": {
      "account_id": "your-account-id",
      "username": "BOOMI_TOKEN.your-username",
      "password": "your-password"
    }
  }
}
```

You can manually edit this file or use the `set_boomi_credentials` tool.

## When to Use

Use local development when:
- 🔧 Developing new MCP tools
- 🐛 Debugging tool behavior
- ⚡ Testing changes quickly
- 📝 Iterating on tool responses

Use production server when:
- 🚀 Deploying to users
- 🔒 Need OAuth authentication
- ☁️ Running in the cloud
- 👥 Multi-user environment

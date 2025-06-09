# Integrating Boomi MCP Server with Cursor and Claude Desktop

This guide walks through adding the Boomi MCP Server to both Cursor (the AI code
editor) and Claude Desktop. The server can be run either from source code or
using Docker.

## Configuration file locations

### Cursor

- **macOS:** `~/Library/Application Support/Cursor`
- **Windows:** `%AppData%\Cursor`
- **Linux:** `~/.config/Cursor`

`mcp.json` lives in this directory.

### Claude Desktop

- **macOS:** `~/Library/Application Support/Claude`
- **Windows:** `%AppData%\Claude`

Claude reads `claude_desktop_config.json` from this folder.

## Adding the server entry

Choose one of the following approaches:

### Option 1: Running from source (Development)

1. Clone the repository and set up credentials:

```bash
git clone https://github.com/glebuar/boomi-mcp-server.git
cd boomi-mcp-server
cp .env.example .env
# Edit .env with your Boomi credentials
```

2. Add this configuration to your host's config file:

```jsonc
{
  "mcpServers": {
    "boomi": {
      "command": "python",
      "args": [
        "-m",
        "boomi_mcp_server.server"
      ],
      "cwd": "/path/to/boomi-mcp-server",
      "env": {
        "PYTHONPATH": "src"
      }
    }
  }
}
```

### Option 2: Using Docker (Recommended)

1. Ensure Docker is running and the server is started:

```bash
docker run -d --name boomi-mcp -p 8080:8080 \
  -e BOOMI_ACCOUNT=your_account \
  -e BOOMI_USER=your_user \
  -e BOOMI_SECRET=your_secret \
  ghcr.io/glebuar/boomi-mcp-server:latest
```

2. Configure your host to connect to the HTTP endpoint:

```jsonc
{
  "mcpServers": {
    "boomi": {
      "url": "http://localhost:8080"
    }
  }
}
```

3. Merge the configuration into your host's file:
   - For **Cursor**, edit `mcp.json` in the directory listed above.
   - For **Claude Desktop**, open `claude_desktop_config.json` and add the entry
     under the `"mcpServers"` section.

4. Restart Cursor or Claude Desktop and enable the **boomi** server entry.

## Platform-specific examples

### Running from source

**Windows:**

```jsonc
{
  "mcpServers": {
    "boomi": {
      "command": "python",
      "args": [
        "-m",
        "boomi_mcp_server.server"
      ],
      "cwd": "C:\\Users\\YourName\\Projects\\boomi-mcp-server",
      "env": {
        "PYTHONPATH": "src",
        "BOOMI_ACCOUNT": "your_account",
        "BOOMI_USER": "your_user",
        "BOOMI_SECRET": "your_secret"
      }
    }
  }
}
```

**macOS/Linux:**

```jsonc
{
  "mcpServers": {
    "boomi": {
      "command": "python",
      "args": [
        "-m",
        "boomi_mcp_server.server"
      ],
      "cwd": "/home/yourname/projects/boomi-mcp-server",
      "env": {
        "PYTHONPATH": "src"
      }
    }
  }
}
```

### Using Docker (HTTP endpoint)

**All platforms:**

```jsonc
{
  "mcpServers": {
    "boomi": {
      "url": "http://localhost:8080"
    }
  }
}
```

## Troubleshooting

- **Port conflicts:** The server runs on port `8080` by default. If the port is
  already in use, change the Docker run command to use a different port:
  `docker run -p 9090:8080 ...` and update the URL to `http://localhost:9090`.
  
- **Docker not running:** Ensure Docker Desktop is running before starting the
  container. Check with `docker ps` to see if the container is active.
  
- **Connection refused:** If using the HTTP endpoint configuration, verify the
  Docker container is running: `docker logs boomi-mcp`.
  
- **Missing credentials:** The server requires three environment variables:
  - `BOOMI_ACCOUNT` - Your Boomi account ID
  - `BOOMI_USER` - Your Boomi username  
  - `BOOMI_SECRET` - Your Boomi password
  
  For Docker, pass these with `-e` flags. For source mode, set them in the
  `env` section of the configuration or use a `.env` file.
  
- **Python not found:** When running from source, ensure Python 3.10+ is
  installed and accessible from your PATH. Use the full path to python if needed.
  
- **Configuration differences:** Cursor reads `mcp.json` while Claude Desktop
  uses `claude_desktop_config.json`. Both support stdio (command/args) and HTTP
  (url) connection methods.


# Integrating Boomi MCP Server with Cursor and Claude Desktop

This guide walks through adding the Boomi MCP Server to both Cursor (the AI code
editor) and Claude Desktop.

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

1. Copy the contents of `.well-known/mcp.json` from this repository:

```jsonc
{
  "mcpServers": {
    "boomi": {
      "command": "uv",
      "args": [
        "--directory",
        "${workspaceFolder}",
        "run",
        "boomi_mcp_server/server.py"
      ]
    }
  }
}
```

Note: You will need to replace `"${workspaceFolder}"` with the actual absolute path to the `boomi-mcp-server` repository directory. See the examples below for platform-specific guidance. If `uv` is not in your `PATH`, replace `uv` with the full path to the `uv` executable.

2. Merge this block into your host's configuration file:
   - For **Cursor**, edit `mcp.json` in the directory listed above.
   - For **Claude Desktop**, open `claude_desktop_config.json` and add the entry
     under the `"mcpServers"` section.

3. Restart Cursor or Claude Desktop and enable the **boomi** server entry.

## Example `mcp.json` entries

Example configuration files are available under the [`examples`](../examples)
folder. They demonstrate using absolute paths on each platform.

Windows:

```jsonc
{
  "mcpServers": {
    "boomi": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\ABSOLUTE\\PATH\\TO\\boomi-mcp-server",
        "run",
        "boomi_mcp_server/server.py"
      ]
    }
  }
}
```

macOS/Linux:

```jsonc
{
  "mcpServers": {
    "boomi": {
      "command": "uv",
      "args": [
        "--directory",
        "/ABSOLUTE/PATH/TO/boomi-mcp-server",
        "run",
        "boomi_mcp_server/server.py"
      ]
    }
  }
}
```

## Troubleshooting

- **Port conflicts:** the server runs on port `8080` in SSE mode by default. If
  the port is already in use, add `"--port", "9090"` to the `args` list and
  update the URL in your client configuration.
- **Docker network/firewall:** when running via Docker, ensure that localhost
  ports are accessible. Windows may prompt for firewall access the first time
  the container starts.
- **Missing credentials:** if the server exits with a "Missing Boomi
  credentials" error, set the `BOOMI_ACCOUNT`, `BOOMI_USER` and `BOOMI_SECRET`
  environment variables. Cursor and Claude Desktop let you specify these in their
  settings UI, or you can provide a `.env` file in the root directory of your cloned `boomi-mcp-server` project.
- **Configuration differences:** Cursor reads `mcp.json` while Claude Desktop
  uses `claude_desktop_config.json`. Both require absolute paths and support
  only the `command` and `args` fields.


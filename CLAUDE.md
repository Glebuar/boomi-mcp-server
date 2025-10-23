# Claude Code + FastMCP + Boomi (basic auth) — Quickstart

This guide sets up a **Python FastMCP** server that:
- Uses **Streamable HTTP** (remote-friendly) so Claude Code can connect.
- Implements **JWT auth** for the MCP server.
- Lets each user store **their own Boomi basic credentials** on the server.
- Exposes a tool that runs the core of the Boomi sample: `account.get_account(...)` from `boomi-python/examples/12_utilities/sample.py`.

> Works on macOS/Linux/WSL2. Requires Python 3.10+ (recommend 3.11/3.12).

---

## 1) Clone & set up

```bash
# Choose or create a workspace
mkdir -p ~/mcp-boomi && cd ~/mcp-boomi

# (A) Option 1: start fresh
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install --upgrade pip uv

# (B) Option 2: use uv from the start (fast resolver)
# curl -LsSf https://astral.sh/uv/install.sh | sh   # install uv if needed
# uv venv && source .venv/bin/activate

# Install deps
uv pip install fastmcp "pydantic>=2" pyjwt python-dotenv
# Boomi SDK from your repo (editable dev optional)
uv pip install git+https://github.com/Glebuar/boomi-python.git
```

Create a minimal project layout:

```
mcp-boomi/
  server.py
  secrets.sqlite   # created at runtime (if you use SQLite option)
  .env             # optional local settings
```

---

## 2) Server code (`server.py`)

This server exposes **4 tools**:

- `set_boomi_credentials(profile, username, password, account_id, base_url)` — store per-user creds (encrypted at rest if you later swap the storage layer).
- `list_boomi_profiles()` — list your stored profiles.
- `delete_boomi_profile(profile)` — remove a profile.
- `boomi_account_info(profile)` — **runs the sample's core behavior**: initialize the Boomi SDK from your stored creds and call `account.get_account(...)`.

It also enables **JWT auth** (HS256 by default) and runs **Streamable HTTP** on `/mcp`.

> **Note**: This uses a tiny SQLite secrets store for local development. For production, swap with AWS/GCP/Azure Secret Manager or Vault.

```python
# server.py
import os, json, sqlite3, time
from contextlib import contextmanager
from typing import Optional, Dict

from fastmcp import FastMCP, tool
from fastmcp.auth import JWTVerifier
from pydantic import BaseModel, Field

# --- Simple local secrets store (SQLite) ---
DB_PATH = os.getenv("SECRETS_DB", "secrets.sqlite")

@contextmanager
def db():
    con = sqlite3.connect(DB_PATH)
    con.execute("""
    CREATE TABLE IF NOT EXISTS secrets (
        sub TEXT NOT NULL,
        profile TEXT NOT NULL,
        payload TEXT NOT NULL,
        updated_at REAL NOT NULL,
        PRIMARY KEY (sub, profile)
    )""")
    try:
        yield con
        con.commit()
    finally:
        con.close()

def put_secret(sub: str, profile: str, payload: Dict[str, str]):
    with db() as con:
        con.execute("REPLACE INTO secrets (sub, profile, payload, updated_at) VALUES (?, ?, ?, ?)",
                    (sub, profile, json.dumps(payload), time.time()))

def get_secret(sub: str, profile: str) -> Dict[str, str]:
    with db() as con:
        cur = con.execute("SELECT payload FROM secrets WHERE sub=? AND profile=?", (sub, profile))
        row = cur.fetchone()
        if not row:
            raise ValueError(f"Profile '{profile}' not found for this user.")
        return json.loads(row[0])

def list_profiles(sub: str):
    with db() as con:
        cur = con.execute("SELECT profile, updated_at FROM secrets WHERE sub=?", (sub,))
        return [{"profile": p, "updated_at": ts} for (p, ts) in cur.fetchall()]

def delete_profile(sub: str, profile: str):
    with db() as con:
        con.execute("DELETE FROM secrets WHERE sub=? AND profile=?", (sub, profile))

# --- Auth: JWT (HS256) for dev; use JWKS/RS256 in prod ---
JWT_ALG = os.getenv("MCP_JWT_ALG", "HS256")
JWT_ISSUER = os.getenv("MCP_JWT_ISSUER", "https://local-issuer")
JWT_AUDIENCE = os.getenv("MCP_JWT_AUDIENCE", "boomi-mcp")
JWT_HS_SECRET = os.getenv("MCP_JWT_SECRET", "change-this-dev-secret")  # dev only

auth = JWTVerifier(
    alg=JWT_ALG,              # "HS256" for dev; prefer RS256/ECDSA with JWKS in prod
    secret=JWT_HS_SECRET,     # only for HS* algs
    issuer=JWT_ISSUER,
    audience=JWT_AUDIENCE,
)

mcp = FastMCP(name="boomi-mcp", auth=auth)

# --- Schemas ---
class Profile(BaseModel):
    profile: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,32}$")

class SetCreds(Profile):
    username: str
    password: str
    account_id: str
    base_url: str

def require(scope: str, ctx):
    scopes = (ctx and getattr(ctx, "scopes", None)) or []
    if scope not in scopes:
        raise PermissionError(f"Missing scope: {scope}")

# --- Tools ---
@mcp.tool()
def set_boomi_credentials(p: SetCreds, ctx=None) -> str:
    # Require write scope to store secrets
    require("secrets:write", ctx)
    sub = getattr(ctx, "sub", None) or "anonymous"
    put_secret(sub, p.profile, {
        "username": p.username,
        "password": p.password,
        "account_id": p.account_id,
        "base_url": p.base_url,
    })
    return f"Stored credentials for profile '{p.profile}'."

@mcp.tool()
def list_boomi_profiles(_: None = None, ctx=None):
    sub = getattr(ctx, "sub", None) or "anonymous"
    return {"profiles": list_profiles(sub)}

@mcp.tool()
def delete_boomi_profile(p: Profile, ctx=None):
    require("secrets:write", ctx)
    sub = getattr(ctx, "sub", None) or "anonymous"
    delete_profile(sub, p.profile)
    return f"Deleted profile '{p.profile}'."

@mcp.tool()
def boomi_account_info(p: Profile, ctx=None):
    # Require read scope to use Boomi APIs
    require("boomi:read", ctx)
    sub = getattr(ctx, "sub", None) or "anonymous"
    creds = get_secret(sub, p.profile)

    # Initialize Boomi SDK (matches the sample's intent)
    from boomi import Boomi
    sdk = Boomi(
        account_id=creds["account_id"],
        username=creds["username"],
        password=creds["password"],
        timeout=10000,
        base_url=creds["base_url"],
    )
    # Call the same endpoint the sample demonstrates
    result = sdk.account.get_account(id_=creds["account_id"])
    # Convert to plain dict for transport
    if hasattr(result, "__dict__"):
        out = {k: v for k, v in result.__dict__.items() if not k.startswith("_") and v is not None}
        out.setdefault("_note", "Account object returned; fields depend on your Boomi account")
        return out
    return {"message": "Account object created; minimal data returned."}

if __name__ == "__main__":
    # Streamable HTTP transport
    mcp.run(transport="http", host="0.0.0.0", port=8000, path="/mcp")
```

> **Prod note**: Replace HS256 with RS256 + JWKS via your IdP (Auth0/Okta/Azure AD). In that case, set `jwks_uri=...` and remove `secret=`.

---

## 3) Run the server

```bash
# (re)activate your venv if needed
source .venv/bin/activate

# Optionally configure dev JWT env (HS256)
export MCP_JWT_ALG=HS256
export MCP_JWT_SECRET='replace-with-a-long-random-string'
export MCP_JWT_ISSUER='https://local-issuer'
export MCP_JWT_AUDIENCE='boomi-mcp'

# Start the server
python server.py
# -> listens on http://127.0.0.1:8000/mcp (via reverse proxy you can add TLS later)
```

---

## 4) Generate a JWT (dev) and point Claude Code at your server

Create a short‑lived token (e.g., 30 minutes) and set it in your environment for Claude Code to send as a header.

```bash
python - <<'PY'
import os, time, jwt
secret = os.environ.get("MCP_JWT_SECRET","change-this-dev-secret")
claims = {
  "sub": "dev-user@example.com",
  "aud": os.environ.get("MCP_JWT_AUDIENCE","boomi-mcp"),
  "iss": os.environ.get("MCP_JWT_ISSUER","https://local-issuer"),
  "scope": "secrets:write boomi:read",
  "exp": int(time.time()) + 1800  # 30 minutes
}
print(jwt.encode(claims, secret, algorithm=os.environ.get("MCP_JWT_ALG","HS256")))
PY
```

Export it for Claude Code to use in the HTTP header:

```bash
export MCP_JWT="PASTE_TOKEN_HERE"
```

Now **register the MCP server** with Claude Code (user scope) using the HTTP transport and an `Authorization` header:

```bash
# Example: add via JSON (works on macOS/Linux/Windows)
claude mcp add-json boomi '{
  "type": "http",
  "url": "http://127.0.0.1:8000/mcp",
  "headers": { "Authorization": "Bearer ${MCP_JWT}" }
}'
```

> You can also use a project-scoped `.mcp.json` and commit it for teams, using env expansion for the header.

---

## 5) Store your own Boomi credentials (per user)

Inside Claude Code, open a new chat and type:

```
/mcp
```

Make sure the **boomi** server is listed and connected. Then ask Claude to run:

> "Run the `set_boomi_credentials` tool with profile `sandbox` and fields: `username=...`, `password=...`, `account_id=...`, `base_url=https://api.boomi.com`."

(Claude will show a tool call card; confirm it.)

You can verify:

> "Run `list_boomi_profiles`."

---

## 6) Execute the sample behavior via MCP

Now call the tool that mirrors the sample's logic:

> "Run `boomi_account_info` with `profile=sandbox`."

You should see an object with your **Boomi account details**. If auth fails, double‑check your stored credentials and that your account has API access.

---

## 7) Security & production notes

- Replace HS256 with **RS256/ECDSA + JWKS** from your IdP; tokens should be **short‑lived**.
- Run behind **TLS** (Caddy/NGINX) and expose `https://YOUR_HOST/mcp`.
- **Never log secrets**; audit tool calls (subject, tool, profile, outcome).
- Consider **rate limiting** `set_boomi_credentials` and tool timeouts/retries.
- Swap the SQLite store for a **managed secrets backend** (AWS/GCP/Azure/Vault).

---

## 8) Troubleshooting

- If Claude Code can't connect: check the URL, port, and that your JWT header is present.
- Use `claude mcp list` and `claude mcp get boomi` to inspect config.
- If tools aren't visible, restart Claude Code or run `/mcp` to refresh.
- If Boomi calls fail, confirm your **base_url**, user/password, and that your account permits API calls.

---

**You're done.** Claude Code can now authenticate to your MCP server and run the Boomi sample behavior safely with **per-user credentials**.

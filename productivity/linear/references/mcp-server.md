# Linear MCP Server Reference

Source: https://linear.app/docs/mcp (accessed 2026-06-25)

## Server URL
`https://mcp.linear.app/mcp`

## Transport
- **Protocol:** StreamableHTTP (remote MCP)
- **Auth:** OAuth (browser login flow, not personal API key)

## Hermes Agent Setup

### Via `hermes mcp add` (recommended — handles OAuth)

```bash
hermes mcp add linear --url "https://mcp.linear.app/mcp" --auth oauth
```

⚠️ `hermes mcp install linear` — does NOT exist (documentation typo).
⚠️ `hermes mcp add linear --preset linear` — fails, no preset named "linear".

### Via direct config.yaml (stdio with npx)

```yaml
mcp_servers:
  linear:
    command: "npx"
    args: ["-y", "mcp-remote", "https://mcp.linear.app/mcp"]
    timeout: 60
```

### Claude Desktop
```
mcp add --transport http linear-server https://mcp.linear.app/mcp
```

### Codex CLI
```
codex mcp login linear
```

### Cursor
- Cmd/Ctrl+P → "MCP: Add Server" → Command (stdio)
- Config: `npx mcp-remote https://mcp.linear.app/mcp`
- Name: `Linear`

## Available Tools
The MCP server exposes tools for:
- Finding issues, projects, documents, teams
- Creating and updating issues
- Adding comments
- Updating status

## Setup | Auth | Best for
|--------|--------------------------|------------|
| Personal API key (static) | `export LINEAR_API_KEY=lin_api_...` | Headless/servers/cron |
| OAuth (browser) | One-time browser login via `hermes mcp add` | Interactive/client-side |

## OAuth Flow Details

When you run `hermes mcp add linear --url https://mcp.linear.app/mcp --auth oauth`:

1. Hermes starts a local HTTP callback server on a random port (e.g., `127.0.0.1:47179`)
2. Prints an authorize URL like:
   ```
   https://mcp.linear.app/authorize?response_type=code&client_id=...&redirect_uri=http://127.0.0.1:47179/callback&...
   ```
3. You open the URL in a browser, log in, authorize → callback hits the local server → MCP connected.

### ⚠️ Headless Server Pitfall

On a remote server without a browser, the callback URL's redirect_uri is hardcoded to `127.0.0.1:<random-port>`. The server is listening there, but your local browser can't reach it.

**Fix — SSH port forwarding:**
```bash
# From your local machine, before opening the OAuth URL:
ssh -L 47179:localhost:47179 ubuntu@<server-ip>
# Now open the authorize URL in your local browser.
# The callback → localhost:47179 → SSH tunnel → server:47179
```

### Webhook HTTPS Requirement

Linear webhooks require **HTTPS URLs**. The Hermes gateway (port 8644) serves HTTP. Workaround:
```bash
cloudflared tunnel --url http://localhost:8644
# → https://something.trycloudflare.com
```

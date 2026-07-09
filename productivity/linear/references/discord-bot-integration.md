# ⚠️ Linear Discord Bot — Slash Command Only

## Reality Check

The official **Linear Discord integration** (`/linear` commands) is **slash-command only**. See https://linear.app/docs/discord.

- `/linear issue` — Create a Linear issue with title, description, team, assignee, project
- `/linear search` — Search and display Linear issues
- `/linear wrap` — Post a summary of your day's work (리스트 조회)
- `/linear link` — Link Discord message to Linear issue

## Critical Limitation

**Hermes-as-bot CANNOT execute slash commands.** Slash commands can only be typed by a human user in the Discord UI. The Linear Discord bot does NOT support @mention-based workflows.

**This means: Hermes cannot create/search/list Linear issues through Discord.**

## Workarounds (in priority order)

### 1. Linear API Key (Best — for headless servers)

```bash
# ~/.hermes/.env
LINEAR_API_KEY=lin_api_...
```

Then use the `linear_api.py` script:
```bash
# Find script
SCRIPT=$(find ~/.hermes -path '*/linear/scripts/linear_api.py' | head -1)

# Who am I?
python3 "$SCRIPT" whoami

# List teams
python3 "$SCRIPT" list-teams

# Create issue
python3 "$SCRIPT" create-issue --team SHO --title "Title" --description "Body" --priority 2

# List issues (wrap 역할)
python3 "$SCRIPT" list-issues --team SHO --limit 20

# Search issues (search 역할)
python3 "$SCRIPT" search-issues "query"
```

**API key issuance:** Go to Linear Settings → API → Personal API keys. Create a key that starts with `lin_api_...`.

### 2. MCP OAuth (if API key unavailable)

```bash
hermes mcp add linear --url https://mcp.linear.app/mcp --auth oauth
```

⚠️ **Headless server pitfall:** OAuth callback URL binds to `127.0.0.1:<random-port>`. On a remote server, use SSH port forwarding:

```bash
# Laptop terminal:
ssh -L <local-port>:localhost:<server-callback-port> ubuntu@<server-ip>
# Then open the OAuth URL in laptop browser
```

### 3. User Relay (last resort)

Prepare the issue content and ask the user to run `/linear issue` in Discord manually.

## Terminology Mapping

| User says | Linear API equivalent |
|-----------|----------------------|
| `wrap` (리스트 조회) | `list-issues --team SHO` |
| `search` (검색) | `search-issues <query>` |
| issue 등록 | `create-issue --title ... --description ...` |

## Pitfalls

- **Do NOT attempt @Linear mention** — the official bot ignores it. Only `/linear` commands work.
- **Only workspace admins** can configure the Linear Discord integration (Settings → Integrations → Discord).
- **Every Linear user** must individually link their Discord account to use `/linear` commands.
- **Make API key portable**: When writing scripts that call Linear API, pass `LINEAR_API_KEY` as env var, never hardcode it.
- **Linear API keys** are issued per-user, not per-team. Found at Linear Settings (NOT org Settings).

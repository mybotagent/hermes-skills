---
name: linear
description: "Linear: manage issues, projects, teams via GraphQL + curl, plus official MCP server."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  env_vars: [LINEAR_API_KEY]
  commands: [curl]
metadata:
  hermes:
    tags: [Linear, Project Management, Issues, GraphQL, API, Productivity]
---

# Linear — Issue & Project Management

Two connection methods:

1. **Direct GraphQL API** (this page) — curl/`linear_api.py` with `LINEAR_API_KEY`. Best for headless servers and cron jobs.
2. **Official MCP Server** (`https://mcp.linear.app/mcp`) — OAuth-based, exposes tools as native Hermes MCP tools. Best for interactive agent use.

Pick whichever fits your environment. See `references/mcp-server.md` for MCP details.

## Alternative: Linear MCP Server (OAuth-based)

The Hermes Agent docs recommend connecting Linear via MCP instead of the direct API:

```bash
hermes mcp add linear --url https://mcp.linear.app/mcp --auth oauth
```

This uses OAuth — see the `native-mcp` skill for OAuth setup details including SSH port forwarding for headless servers.

**When to use which:**
- **Direct API (this skill):** Scripting, cron jobs, automated pipelines — no interactive auth needed
- **MCP:** Interactive agent sessions where Hermes needs to read/search/create issues in real-time

1. Get a personal API key from **Linear Settings > Account > Security & access > Personal API keys** (URL: https://linear.app/settings/account/security). Note: the org-level *Settings > API* page only shows OAuth apps and workspace-member keys, not personal keys.
2. Set `LINEAR_API_KEY` in your environment (via `hermes setup` or your env config)

## API Basics

- **Endpoint:** `https://api.linear.app/graphql` (POST)
- **Auth header:** `Authorization: $LINEAR_API_KEY` (no "Bearer" prefix for API keys)
- **All requests are POST** with `Content-Type: application/json`
- **Both UUIDs and short identifiers** (e.g., `ENG-123`) work for `issue(id:)`

Base curl pattern:
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ viewer { id name } }"}' | python3 -m json.tool
```

## Python helper script (ergonomic alternative)

For faster one-liners that don't need hand-written GraphQL, this skill ships a stdlib Python CLI at `scripts/linear_api.py`. Zero dependencies. Same auth (reads `LINEAR_API_KEY`).

```bash
SCRIPT=$(dirname "$(find ~/.hermes -path '*skills/productivity/linear/scripts/linear_api.py' 2>/dev/null | head -1)")/linear_api.py

python3 "$SCRIPT" whoami
python3 "$SCRIPT" list-teams
python3 "$SCRIPT" get-issue ENG-42
python3 "$SCRIPT" get-document 38359beef67c      # fetch a doc by slugId from the URL
python3 "$SCRIPT" raw 'query { viewer { name } }'
```

All subcommands: `whoami`, `list-teams`, `list-projects`, `list-states`, `list-issues`, `get-issue`, `search-issues`, `create-issue`, `update-issue`, `update-status`, `add-comment`, `list-documents`, `get-document`, `search-documents`, `raw`. Run with `--help` for flags.

Use the script when: you want a quick answer without crafting GraphQL. Use curl when: you need a query the script doesn't wrap, or you want to compose filters inline.

## Workflow States

Linear uses `WorkflowState` objects with a `type` field. **6 state types:**

| Type | Description |
|------|-------------|
| `triage` | Incoming issues needing review |
| `backlog` | Acknowledged but not yet planned |
| `unstarted` | Planned/ready but not started |
| `started` | Actively being worked on |
| `completed` | Done |
| `canceled` | Won't do |

Each team has its own named states (e.g., "In Progress" is type `started`). To change an issue's status, you need the `stateId` (UUID) of the target state — query workflow states first.

**Priority values:** 0 = None, 1 = Urgent, 2 = High, 3 = Medium, 4 = Low

## Common Queries

### Get current user
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ viewer { id name email } }"}' | python3 -m json.tool
```

### List teams
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ teams { nodes { id name key } } }"}' | python3 -m json.tool
```

### List workflow states for a team
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ workflowStates(filter: { team: { key: { eq: \"ENG\" } } }) { nodes { id name type } } }"}' | python3 -m json.tool
```

### List issues (first 20)
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ issues(first: 20) { nodes { identifier title priority state { name type } assignee { name } team { key } url } pageInfo { hasNextPage endCursor } } }"}' | python3 -m json.tool
```

### List my assigned issues
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ viewer { assignedIssues(first: 25) { nodes { identifier title state { name type } priority url } } } }"}' | python3 -m json.tool
```

### Get a single issue (by identifier like ENG-123)
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ issue(id: \"ENG-123\") { id identifier title description priority state { id name type } assignee { id name } team { key } project { name } labels { nodes { name } } comments { nodes { body user { name } createdAt } } url } }"}' | python3 -m json.tool
```

### Search issues by text
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ issueSearch(query: \"bug login\", first: 10) { nodes { identifier title state { name } assignee { name } url } } }"}' | python3 -m json.tool
```

### Filter issues by state type
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ issues(filter: { state: { type: { in: [\"started\"] } } }, first: 20) { nodes { identifier title state { name } assignee { name } } } }"}' | python3 -m json.tool
```

### Filter by team and assignee
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ issues(filter: { team: { key: { eq: \"ENG\" } }, assignee: { email: { eq: \"user@example.com\" } } }, first: 20) { nodes { identifier title state { name } priority } } }"}' | python3 -m json.tool
```

### List projects
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ projects(first: 20) { nodes { id name description progress lead { name } teams { nodes { key } } url } } }"}' | python3 -m json.tool
```

### List team members
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ users { nodes { id name email active } } }"}' | python3 -m json.tool
```

### List labels
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ issueLabels { nodes { id name color } } }"}' | python3 -m json.tool
```

## Common Mutations

### Create an issue
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "mutation($input: IssueCreateInput!) { issueCreate(input: $input) { success issue { id identifier title url } } }",
    "variables": {
      "input": {
        "teamId": "TEAM_UUID",
        "title": "Fix login bug",
        "description": "Users cannot login with SSO",
        "priority": 2
      }
    }
  }' | python3 -m json.tool
```

### Update issue status
First get the target state UUID from the workflow states query above, then:
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "mutation { issueUpdate(id: \"ENG-123\", input: { stateId: \"STATE_UUID\" }) { success issue { identifier state { name type } } } }"}' | python3 -m json.tool
```

### Assign an issue
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "mutation { issueUpdate(id: \"ENG-123\", input: { assigneeId: \"USER_UUID\" }) { success issue { identifier assignee { name } } } }"}' | python3 -m json.tool
```

### Set priority
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "mutation { issueUpdate(id: \"ENG-123\", input: { priority: 1 }) { success issue { identifier priority } } }"}' | python3 -m json.tool
```

### Add a comment
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "mutation { commentCreate(input: { issueId: \"ISSUE_UUID\", body: \"Investigated. Root cause is X.\" }) { success comment { id body } } }"}' | python3 -m json.tool
```

**`linear_api.py` arg syntax (2026-07-01 검증)**: `add-comment`는 **positional args** (identifier + body). `--body` 같은 flag 없음.
```bash
# ✅ 올바른 사용
python3 "$SCRIPT" add-comment SHO-34 "코멘트 본문 (멀티라인 가능)"

# ❌ 흔한 실수 (헐렁된 flag 인식)
python3 "$SCRIPT" add-comment SHO-34 --body "코멘트 본문"
# → unrecognized arguments: --body 에러
```

**`create-issue`도 `--state` 미지원** (2026-07-01 확인). Done으로 직접 생성하려면:
```bash
# 1) create (Backlog/Todo에 생성)
ISSUE=$(python3 "$SCRIPT" create-issue --team SHO --title "..." --priority 3)
# 2) update-status 별도 호출
python3 "$SCRIPT" update-status "$ISSUE_ID" Done
```

### Set due date
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "mutation { issueUpdate(id: \"ENG-123\", input: { dueDate: \"2026-04-01\" }) { success issue { identifier dueDate } } }"}' | python3 -m json.tool
```

### Add labels to an issue
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "mutation { issueUpdate(id: \"ENG-123\", input: { labelIds: [\"LABEL_UUID_1\", \"LABEL_UUID_2\"] }) { success issue { identifier labels { nodes { name } } } } }"}' | python3 -m json.tool
```

### Add issue to a project
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "mutation { issueUpdate(id: \"ENG-123\", input: { projectId: \"PROJECT_UUID\" }) { success issue { identifier project { name } } } }"}' | python3 -m json.tool
```

### Create a project
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "mutation($input: ProjectCreateInput!) { projectCreate(input: $input) { success project { id name url } } }",
    "variables": {
      "input": {
        "name": "Q2 Auth Overhaul",
        "description": "Replace legacy auth with OAuth2 and PKCE",
        "teamIds": ["TEAM_UUID"]
      }
    }
  }' | python3 -m json.tool
```

## Documents

Linear **Documents** are prose docs (RFCs, specs, notes) stored alongside issues. They have their own `documents` root query and `document(id:)` single-fetch.

### Document URLs and `slugId`

Document URLs look like:
```
https://linear.app/<workspace>/document/<slug>-<hexSlugId>
```

The trailing hex segment is the `slugId`. Example: `https://linear.app/nousresearch/document/rfc-hermes-permission-gateway-discord-38359beef67c` → `slugId` is `38359beef67c`.

**Important schema detail:** the Markdown body is in the `content` field. The ProseMirror JSON is in `contentState` (not `contentData` — that field does not exist and the API returns 400).

### Fetch a document by slugId

`document(id:)` only accepts UUIDs. To fetch by the URL's hex slug, filter the collection:

```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "query($s: String!) { documents(filter: { slugId: { eq: $s } }, first: 1) { nodes { id title content contentState slugId url creator { name } project { name } updatedAt } } }", "variables": {"s": "38359beef67c"}}' \
  | python3 -m json.tool
```

Or via the Python helper:
```bash
python3 scripts/linear_api.py get-document 38359beef67c
```

### Fetch a document by UUID

```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ document(id: \"11700cff-b514-4db3-afcc-3ed1afacba1c\") { title content url } }"}' \
  | python3 -m json.tool
```

### List recent documents

```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ documents(first: 25, orderBy: updatedAt) { nodes { id title slugId url updatedAt project { name } } } }"}' \
  | python3 -m json.tool
```

### Search documents by title

Linear's schema has no `searchDocuments` root. Use a title-substring filter instead:

```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ documents(filter: { title: { containsIgnoreCase: \"RFC\" } }, first: 25) { nodes { title slugId url } } }"}' \
  | python3 -m json.tool
```

## Pagination

Linear uses Relay-style cursor pagination:

```bash
# First page
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ issues(first: 20) { nodes { identifier title } pageInfo { hasNextPage endCursor } } }"}' | python3 -m json.tool

# Next page — use endCursor from previous response
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ issues(first: 20, after: \"CURSOR_FROM_PREVIOUS\") { nodes { identifier title } pageInfo { hasNextPage endCursor } } }"}' | python3 -m json.tool
```

Default page size: 50. Max: 250. Always use `first: N` to limit results.

## Filtering Reference

Comparators: `eq`, `neq`, `in`, `nin`, `lt`, `lte`, `gt`, `gte`, `contains`, `startsWith`, `containsIgnoreCase`

Combine filters with `or: [...]` for OR logic (default is AND within a filter object).

## Typical Workflow

1. **Query teams** to get team IDs and keys
2. **Query workflow states** for target team to get state UUIDs
3. **List or search issues** to find what needs work
4. **Create issues** with team ID, title, description, priority
5. **Update status** by setting `stateId` to the target workflow state
6. **Add comments** to track progress
7. **Mark complete** by setting `stateId` to the team's "completed" type state

## Rate Limits

- 5,000 requests/hour per API key
- 3,000,000 complexity points/hour
- Use `first: N` to limit results and reduce complexity cost
- Monitor `X-RateLimit-Requests-Remaining` response header

## Official MCP Server

Linear also provides an official MCP server at `https://mcp.linear.app/mcp` (docs: https://linear.app/docs/mcp). See `references/mcp-server.md` for full config details.

**Key difference from the curl approach:**
- **curl API** (this skill): Uses `LINEAR_API_KEY` (personal API key), no OAuth. Best for server/headless environments.
- **MCP server**: Uses OAuth (browser login flow). Exposes tools for finding, creating, and updating issues/projects/documents as native MCP tools.

### Hermes Agent Setup (via `hermes mcp add`)

```bash
hermes mcp add linear --url "https://mcp.linear.app/mcp" --auth oauth
```

**Note:** `hermes mcp install linear` does NOT exist. Use `hermes mcp add` with the URL above. The `--preset linear` flag also does not exist.

This command spawns a local OAuth callback server on a random port (e.g., `127.0.0.1:47179`), then prints a browser URL to complete the OAuth flow.

### ⚠️ Headless Server OAuth Pitfall

The callback URL is `http://127.0.0.1:<random-port>/callback` — bound to the server's localhost. On a headless/remote server you cannot open the browser URL directly because the callback won't reach the server.

**Workaround — SSH port forwarding from your local machine:**

```bash
# In a separate terminal on your local machine:
ssh -L <local-port>:localhost:<server-callback-port> ubuntu@<server-ip>

# Then open the OAuth URL in your local browser
```

Alternatively, use the direct GraphQL API with `LINEAR_API_KEY` for fully headless workflows — no OAuth needed.

### Stdio via npx (alternative for Hermes Agent)

```yaml
mcp_servers:
  linear:
    command: "npx"
    args: ["-y", "mcp-remote", "https://mcp.linear.app/mcp"]
    timeout: 60
```

### Linear Webhook → Hermes Agent

Linear webhooks require **HTTPS** URLs. If your Hermes gateway only has HTTP (port 8644), use a tunnel:

```bash
cloudflared tunnel --url http://localhost:8644
# → https://something.trycloudflare.com
```

Then register `https://something.trycloudflare.com/webhooks/<name>` in Linear Settings → Webhooks.

Create the Hermes webhook subscription:

```bash
hermes webhook subscribe kanban-linear-sync \
  --events "linear-issue" \
  --prompt '...' \
  --skills "linear,kanban-worker" \
  --deliver origin
```

## Kanban ↔ Linear Sync Workflow

When connecting a local Kanban board (Hermes kanban SQLite) to Linear issues:

### 1. Map Kanban tasks → Linear issues

```bash
SCRIPT=$(find ~/.hermes -path '*/linear/scripts/linear_api.py' | head -1)

# Get team ID first
python3 "$SCRIPT" list-teams

# Create one issue per Kanban task
python3 "$SCRIPT" create-issue --team SHO --title "Kanban task title" \
  --description "Task body from kanban. Priority: P1" --priority 2
```

### 2. Store Linear ID in Kanban DB

```bash
sqlite3 ~/.hermes/kanban.db "
UPDATE tasks SET body = body || char(10) || '**Linear:** SHO-14 https://linear.app/shootingstock/issue/SHO-14'
WHERE id = 't_xxx';
"
```

### 3. List (wrap) — show current Linear issues

```bash
python3 "$SCRIPT" list-issues --team SHO --limit 20
```

### 4. Search (search) — find issues by text

```bash
python3 "$SCRIPT" search-issues "keyword"
```

### 5. Update Kanban → Linear status (when Kanban task completes)

```bash
# Move Linear issue to "Done" state
python3 "$SCRIPT" update-status SHO-14 Done
```

### Priority Mapping

| Kanban priority | Linear priority value |
|-----------------|----------------------|
| P1 (highest) | 1 (Urgent) or 2 (High) |
| P2 | 3 (Medium) |
| P0 (backlog) | 4 (Low) |
| none | 0 (None) |

### Pitfalls

- **Always verify** with `list-issues` after creation — the user might not see issues if Linear UI has filters set (e.g., "My issues" instead of "All issues").
- **Kanban DB needs `created_at` as epoch integer**: `strftime('%s','now')` for INSERT.
- **Kanban `workspace_kind` requires value**: Default `'scratch'` for new tasks.
- **Store the Linear identifier** (SHO-14 not the UUID) in Kanban body for human readability.
- **Linear API keys** emit from `lin_api_*` pattern. Stored in `~/.hermes/.env`.
- **Team key case-sensitive**: Verify with `list-teams` before creating issues.

### Linear API key location (Hermes default)

`LINEAR_API_KEY` lives in `~/.hermes/.env` — **not exported to the shell environment by default**. Scripts that need it must read the file directly:

```bash
# Pattern A: source into current shell
set -a; source ~/.hermes/.env; set +a
echo "$LINEAR_API_KEY"

# Pattern B: inline load + use (no env export)
KEY=$(grep LINEAR_API_KEY ~/.hermes/.env | cut -d= -f2)
curl -s -H "Authorization: $KEY" ...
```

If you call Linear from a Python script and `os.environ.get('LINEAR_API_KEY')` returns None, the key is in `~/.hermes/.env` — load it before any request. Trying to use the OAuth client in `~/.hermes/mcp-tokens/linear.client.json` is **not** a substitute; that file only has `client_id`, not the API token.

### GraphQL filter pitfalls (SHO-22 session, 2026-06-29)

These are real errors hit while writing a Kanban→Linear sync script:

- **`searchIssues` field is `term`, not `query`**: `searchIssues(query: "X")` returns `Unknown argument "query". Did you mean "term"?`. Use:
  ```graphql
  { searchIssues(term: "SHO-22", first: 5) { nodes { id identifier } } }
  ```

- **Filter issue by number uses `number: { eq: N }`** inside the `issues` filter, not `identifier`:
  ```graphql
  { issues(filter: { state: { type: { eq: "backlog" } }, number: { eq: 22 } }) { nodes { id identifier } } }
  ```
  (Identifier like `SHO-22` is the *display* format, but the filter takes the bare integer `number`.)

- **`workflowStates` without team filter returns ALL teams' states**: helpful when you don't know which team to query. Filter by `name: { eq: "Done" }` + `type: { eq: "completed" }` to find the right state UUID for any team in one call.

- **`commentCreate` requires `issueId` (UUID)**, not the identifier `SHO-22`. Get the UUID from the issue's `id` field first.

### Linear issue → Kanban mirror pattern (bidirectional sync)

When a Linear issue is worked on or completed, mirror it as a Kanban task to keep the local SQLite board in sync:

```python
import sqlite3, time, secrets

conn = sqlite3.connect('/home/ubuntu/.hermes/kanban.db')
mapping_file = '/home/ubuntu/.hermes/data/kanban_linear_mapping.json'

# 1. Find or create mirror task (idempotent)
title = f'[SHO-22] {issue["title"]}'
existing = conn.execute("SELECT id FROM tasks WHERE title = ?", (title,)).fetchone()
if existing:
    task_id = existing[0]
else:
    task_id = f't_{secrets.token_hex(4)}'
    body = f'''---
linear_id: {issue["identifier"]}
linear_url: {issue["url"]}
---

# Source
Linear issue: {issue["identifier"]} — {issue["title"]}
'''
    now = int(time.time())
    conn.execute("""
        INSERT INTO tasks (id, title, body, assignee, status, priority, created_by, created_at, workspace_kind, max_retries)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (task_id, title, body, 'hermes', 'done', 2, 'user', now, 'scratch', 0))

# 2. Update status (Kanban done when Linear done)
conn.execute("UPDATE tasks SET status = 'done', completed_at = ? WHERE id = ?", (int(time.time()), task_id))
conn.commit()

# 3. Maintain ID mapping
import json, os
mapping = {}
if os.path.exists(mapping_file):
    mapping = json.load(open(mapping_file))
mapping[task_id] = {
    'linear_issue_id': issue['identifier'],
    'linear_url': issue['url'],
    'kanban_updated_at': int(time.time()),
    'linear_updated_at': issue['updatedAt'],
    'last_synced': '2026-06-29T20:30:00Z',
}
os.makedirs(os.path.dirname(mapping_file), exist_ok=True)
json.dump(mapping, open(mapping_file, 'w'), indent=2, ensure_ascii=False)
```

The mapping file (`~/.hermes/data/kanban_linear_mapping.json`) is the source of truth for which Kanban task mirrors which Linear issue. Daily cron (07:00 KST) compares both sides and applies status changes; the manual mirror pattern above is for ad-hoc work done outside the cron cycle.

## 📎 추가 참고 파일

- `references/post-task-tracking-sync.md` — 작업 완료 후 Linear + Kanban + GitHub + Wiki 4-way sync 워크플로 (사용자 정책 "코드랑 문서 업데이트해 리니어 칸반 github까지" 대응).

## ⚠️ Discord Bot Integration — Slash Command Trap

The official **Linear Discord integration** (https://linear.app/docs/discord) is **slash-command only** (`/linear issue`, `/linear search`, `/linear wrap`).

**Hermes as a Discord bot CANNOT execute slash commands.** There is no @mention-based workflow for the official Linear bot.

This means:
- ❌ **Cannot** create issues via Discord from Hermes
- ❌ **Cannot** search via Discord from Hermes
- ❌ **Cannot** list/wrap via Discord from Hermes
- ✅ **Must** use `LINEAR_API_KEY` (GraphQL API) or MCP OAuth instead

**Bypass options when API key is unavailable:**
- **Direct GraphQL API** with `LINEAR_API_KEY` (this page) — headless-friendly
- **MCP OAuth** (`hermes mcp add linear --url https://mcp.linear.app/mcp --auth oauth`) — requires SSH port forwarding for callback on headless servers
- **User relay**: Prepare the issue data, user manually runs `/linear issue` in Discord channel

⏩ **Do NOT** attempt to mention `@Linear` in Discord. It will not work. Go directly to API key or MCP setup.

See `references/discord-bot-integration.md` for background.

## Important Notes

- Always use `terminal` tool with `curl` for API calls — do NOT use `web_extract` or `browser`
- Always check the `errors` array in GraphQL responses — HTTP 200 can still contain errors
- If `stateId` is omitted when creating issues, Linear defaults to the first backlog state
- The `description` field supports Markdown
- Use `python3 -m json.tool` or `jq` to format JSON responses for readability

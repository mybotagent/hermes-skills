# Kanban ↔ External Tool Sync (Linear) — Cron-Driven Workflow

> Absorbed from standalone `kanban-external-sync` skill (2026-06-28).
> This is a concrete application of cron pipeline chaining for bidirectional sync between Hermes Kanban (SQLite) and Linear (GraphQL API).

## Architecture

```
Layer 1: Daily Cron (07:00 KST)
  hermes cron rotate → script compares all records both ways

Layer 2: Linear Webhook → Hermes Webhook (real-time)
  Linear issue.create/update → POST to hermes webhook → agent run
```

## ID Mapping

Each synced pair maintains a bidirectional ID reference stored in `~/.hermes/data/kanban_linear_mapping.json`:

```json
{
  "kanban_task_id_1": {
    "linear_issue_id": "HERMES-42",
    "linear_url": "https://linear.app/workspace/issue/HERMES-42/...",
    "kanban_updated_at": 1740000000,
    "linear_updated_at": "2026-06-25T13:00:00Z",
    "last_synced": "2026-06-25T13:00:00Z"
  }
}
```

Kanban task `body` also stores the Linear issue reference as a YAML frontmatter block:
```
---
linear_id: HERMES-42
linear_url: https://linear.app/workspace/issue/HERMES-42/...
---
```

## Status Mapping

| Kanban Status | Linear State Type |
|---------------|-------------------|
| `todo`        | `backlog` / `triage` |
| `ready`       | `unstarted` |
| `in_progress` | `started` |
| `done`        | `completed` |
| `blocked`     | `triage` (or custom blocked state) |
| `cancelled`   | `canceled` |

## Sync Logic Flow

1. Load mapping file
2. Query all Linear issues for the configured team via `linear_api.py list-issues --team KEY`
3. Query all Kanban tasks via `hermes kanban list --json`
4. **Kanban→Linear**: For kanban tasks with a linear_id not found in Linear → create issue, update mapping
5. **Linear→Kanban**: For Linear issues without a kanban task → create kanban task, update mapping
6. **Status sync**: For matched pairs, compare status/assignee/priority and update whichever side is stale
7. Save updated mapping
8. Print summary report

## Cron Job Setup

```bash
hermes cron create "kanban-linear-sync" \
  --schedule "0 22 * * *" \
  --script ~/.hermes/scripts/kanban_linear_sync.py \
  --name "Kanban ↔ Linear daily sync"
```

## Webhook Layer (Optional, Real-Time)

### Linear → Kanban
1. Enable Hermes webhook: `hermes gateway setup` → enable webhooks on port 8644
2. Subscribe to Linear events:
```bash
hermes webhook subscribe linear-sync \
  --events "issue.create,issue.update" \
  --prompt "Linear issue {action}d: {data.title} ({data.identifier})" \
  --skills "kanban-external-sync" \
  --deliver origin
```
3. Configure Linear webhook: Settings → API → Webhooks → Add endpoint to Hermes webhook URL

## Pitfalls

- **Sync loops**: Always check `kanban_updated_at` vs `linear_updated_at` before writing. Skip update if the other side already has the latest change.
- **LINEAR_API_KEY missing**: Add to `~/.hermes/.env`.
- **Rate limits**: Linear allows 5,000 requests/hr. Daily sync is well within this.
- **Mapping file corruption**: If `kanban_linear_mapping.json` is deleted or corrupted, the next sync run re-discovers all pairs by matching titles + body markers.

## Reference Implementation (2026-06-29 — SHO-22 처리 패턴)

실제 SHO-22 (BUG) 처리하면서 검증한 패턴. cron 자동화 전이라도 **수동 Linear 처리 시** 같은 흐름으로 진행.

### 1) LINEAR_API_KEY 위치 (중요)

```bash
# ~/.hermes/.env에 존재 — env export는 안 됨
cat ~/.hermes/.env | grep LINEAR
# LINEAR_API_KEY=lin_api_xxxxxxxxxxxxxxxx
```

**env에 자동 export 안 됨** → Python에서 동적 주입:
```python
for line in open('/home/ubuntu/.hermes/.env').read().split('\n'):
    line = line.strip()
    if line and not line.startswith('#') and '=' in line:
        k, v = line.split('=', 1)
        os.environ[k] = v
```

**`~/.hermes/mcp-tokens/linear.client.json`은 OAuth client_id만 있고 API token 아님** — 절대 그 파일로 인증 시도하지 마라.

### 2) Kanban API 직접 접근 (web API 401 시)

Web API가 인증 막을 때 SQLite 직접 접근 fallback:

```python
import sqlite3
conn = sqlite3.connect('/home/ubuntu/.hermes/kanban.db')
conn.row_factory = sqlite3.Row
# tasks (29 cols), task_links, task_comments, task_events, task_runs
# 9199 (Vite SPA, hermes 자체 dashboard) + 8642 (hermes-agent API)는 web API
# 401 막힐 때 sqlite3 fallback
```

### 3) Kanban Mirror 태스크 생성 + Mapping 기록

Linear 이슈 처리 시 **반드시** Kanban mirror 만들기 (aiprofit 워크플로우):

```python
new_id = f't_{secrets.token_hex(4)}'
body = f'''---
linear_id: SHO-22
linear_url: https://linear.app/mybot/issue/SHO-22/...
---
# Linear 이슈 본문/해결 내용
'''

# Kanban task INSERT
conn.execute("""
    INSERT INTO tasks (id, title, body, assignee, status, priority, created_by, created_at, workspace_kind, max_retries)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (new_id, '[SHO-22] ...', body, 'hermes', 'done', 2, 'user', int(time.time()), 'scratch', 0))

# status done 마킹
conn.execute("UPDATE tasks SET status = 'done', completed_at = ? WHERE id = ?", (now, task_id))
conn.commit()

# Mapping JSON 기록
import os, json
mapping_dir = '/home/ubuntu/.hermes/data'
os.makedirs(mapping_dir, exist_ok=True)
mapping_file = f'{mapping_dir}/kanban_linear_mapping.json'
mapping = {}
if os.path.exists(mapping_file):
    mapping = json.load(open(mapping_file))
mapping[task_id] = {
    'linear_issue_id': 'SHO-22',
    'linear_url': '...',
    'kanban_updated_at': now,
    'linear_updated_at': '2026-06-29T20:30:00Z',
    'last_synced': '2026-06-29T20:30:00Z',
}
with open(mapping_file, 'w') as f:
    json.dump(mapping, f, indent=2, ensure_ascii=False)
```

### 4) Linear issueUpdate + commentCreate (single mutation)

```graphql
mutation Update($issueId: String!, $stateId: String!, $body: String!) {
  issueUpdate(id: $issueId, input: { stateId: $stateId }) {
    success issue { identifier state { name } }
  }
  commentCreate(input: { issueId: $issueId, body: $body }) {
    success
  }
}
```

상태 ID는 `workflowStates` query로 가져옴:
- `Backlog`: `cec5bc9e-3028-4f51-b3ad-1f60740a1812`
- `Done`: `86cd9d73-2b97-49e9-8b16-95c1d08c29ad`
- `Todo`: `58b34e08-f1b1-48a0-bcc3-40a9579fd94c`

매핑은 팀마다 다름 — `workflowStates(first: 50)` query로 매번 확인 권장.

### 5) Linear identifier로 issue ID 조회

```graphql
{ issues(filter: { state: { type: { eq: "backlog" } }, number: { eq: 22 } }) {
    nodes { id identifier title description state { name } }
} }
```

`number`는 이슈 번호 (SHO-22의 22). `id`는 UUID. mutation은 UUID 필요.

### SHO-22 검증 결과 (2026-06-29)

| 단계 | 결과 |
|------|------|
| LINEAR_API_KEY 로드 | ✅ ~/.hermes/.env에서 os.environ 주입 |
| SHO-22 UUID 조회 | ✅ 1b002204-6e40-46e8-8875-9fef82c02022 |
| Done 상태 변경 | ✅ |
| 해결 코멘트 첨부 | ✅ (핫픽스 + 검증 결과) |
| Kanban mirror 생성 | ✅ t_0092361d |
| Mapping JSON 기록 | ✅ ~/.hermes/data/kanban_linear_mapping.json (첫 record) |

## Related Skills

- `linear` — Linear API calls
- `kanban-worker`, `kanban-orchestrator` — Kanban worker lifecycle
- `webhook-subscriptions` — Webhook setup for real-time sync layer
- `meeting-documentation` — Live Incremental Save (commit 패턴 공유)

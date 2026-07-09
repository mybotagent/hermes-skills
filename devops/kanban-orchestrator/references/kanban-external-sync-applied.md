---
title: "Kanban ↔ External System Sync — 실전 적용 사례 (2026-06-29)"
tags: ["kanban", "linear", "sync", "applied-pattern", "sqlite"]
applies_to: "kanban-orchestrator, kanban-external-sync workflows"
---

# Kanban ↔ External Sync — 실전 적용 사례

> 아키텍처 디자인: `references/kanban-linear-sync-workflow.md` (이건 Linear + Kanban cron 기반 양방향 sync 전체 디자인)
> 본 문서: **실전 적용 한 사이클** (2026-06-29 SHO-22 핫픽스)에서 검증된 패턴

## 동기: 왜 매번 sync인가

Hermes Kanban (`~/.hermes/kanban.db` SQLite)은 워커의 일일 실행 단위, Linear는 사용자/PM의 전략 단위. 이 둘을 별도로 운영하면:

- ❌ Linear 이슈가 닫혀도 Kanban task가 `in_progress`로 남음
- ❌ Kanban에서 task 완료해도 Linear는 `Backlog` 그대로
- ❌ 한쪽에서 history 사라져도 다른 쪽에서 추적 가능성 (감사 추적)

→ **이벤트 발생 시점에 즉시 sync**가 가장 안전. cron daily sync는 safety net.

## SHO-22 실전 사례 (2026-06-29)

**상황**: Linear SHO-22 (BUG, priority 2) "dawn_wiki_sync.sh push rejected" 핫픽스. 작업 완료 후 즉시 sync 필요.

### Step 1: Linear에서 issue ID 가져오기

```python
import os, json, urllib.request

# .env에서 LINEAR_API_KEY 로드 (단, env에 export 안 되어 있음 → 직접 load)
for line in open('/home/ubuntu/.hermes/.env').read().split('\n'):
    line = line.strip()
    if line and not line.startswith('#') and '=' in line:
        k, v = line.split('=', 1)
        os.environ[k] = v

KEY = os.environ['LINEAR_API_KEY']

def gql(query, variables=None):
    body = {'query': query}
    if variables:
        body['variables'] = variables
    req = urllib.request.Request('https://api.linear.app/graphql',
        data=json.dumps(body).encode(),
        headers={'Content-Type': 'application/json', 'Authorization': KEY})
    return json.loads(urllib.request.urlopen(req, timeout=15).read())

# SHO-XX → UUID 매핑 (Done state 전환 시 필요)
issues = gql('{ issues(filter: { state: { type: { eq: "backlog" } }, number: { eq: 22 } }) { nodes { id identifier title state { name } } } }')
issue = issues['data']['issues']['nodes'][0]
# → {'id': '1b002204-6e40-46e8-8875-9fef82c02022', 'identifier': 'SHO-22', ...}
```

### Step 2: Kanban에 mirror task 생성 (없으면) + Done 마킹

```python
import sqlite3, secrets, time

conn = sqlite3.connect('/home/ubuntu/.hermes/kanban.db')
conn.row_factory = sqlite3.Row

new_id = f't_{secrets.token_hex(4)}'
cur = conn.execute("SELECT id FROM tasks WHERE title = ?", ('[SHO-22] dawn_wiki_sync.sh push rejected 핫픽스',))
existing = cur.fetchone()

if not existing:
    body = '''---
linear_id: SHO-22
linear_url: https://linear.app/mybot/issue/SHO-22/...
---

# 증상
새벽 04:00 KST wiki 동기화 cron이 git push rejected로 실패.

# 해결 (2026-06-29)
- `set -e` 제거
- stash → pull → pop 순서
- push rejected 시 pull --rebase && push 재시도
- orphan submodule 자동 정리
- 최종 실패 시 exit 2

# 검증
직접 실행 테스트 완료 ✅ commit 10312ce
'''
    now = int(time.time())
    conn.execute("""
        INSERT INTO tasks (id, title, body, assignee, status, priority, created_by, created_at, workspace_kind, max_retries)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (new_id, '[SHO-22] dawn_wiki_sync.sh push rejected 핫픽스', body, 'hermes', 'done', 2, 'user', now, 'scratch', 0))
    task_id = new_id
else:
    task_id = existing['id']

# Status → done
now = int(time.time())
conn.execute("UPDATE tasks SET status = 'done', completed_at = ?, last_heartbeat_at = ? WHERE id = ?", (now, now, task_id))
conn.commit()
```

### Step 3: mapping.json에 양방향 ID 기록 (워크플로우의 첫 sync record)

```python
import os, json

mapping_dir = '/home/ubuntu/.hermes/data'
os.makedirs(mapping_dir, exist_ok=True)
mapping_file = f'{mapping_dir}/kanban_linear_mapping.json'

mapping = {}
if os.path.exists(mapping_file):
    mapping = json.load(open(mapping_file))

mapping[task_id] = {
    'linear_issue_id': 'SHO-22',
    'linear_url': 'https://linear.app/mybot/issue/SHO-22/...',
    'kanban_updated_at': now,
    'linear_updated_at': '2026-06-29T20:30:00Z',
    'last_synced': '2026-06-29T20:30:00Z'
}

with open(mapping_file, 'w') as f:
    json.dump(mapping, f, indent=2, ensure_ascii=False)
```

### Step 4: Linear에서 state → Done 전환 + 해결 코멘트

```python
# Done state ID 조회 (워크플로우마다 다름 — 한 번 캐시 추천)
ws = gql('{ workflowStates(first: 50) { nodes { id name type } } }')
done_id = [s for s in ws['data']['workflowStates']['nodes'] if s['type'] == 'completed'][0]['id']

comment = """## 해결 (2026-06-29 20:29 KST)

### 핫픽스 적용 (`~/.hermes/scripts/dawn_wiki_sync.sh`)
- `set -e` 제거 → 각 단계 명시적 `||` 처리
- stash → pull → pop 순서 보장
- push rejected 시 pull --rebase && push 재시도
- orphan submodule `code/stock-analysis-toolkit` 자동 정리
- 최종 실패 시 exit 2 → self-heal 감지 신호

### 검증
- 직접 실행 ✅ exit 0
- push 정상 ✅ commit 10312ce (orphan 정리 + auto-sync)
"""

r = gql('''
  mutation Update($issueId: String!, $stateId: String!, $body: String!) {
    issueUpdate(id: $issueId, input: { stateId: $stateId }) { success }
    commentCreate(input: { issueId: $issueId, body: $body }) { success }
  }
''', {'issueId': issue['id'], 'stateId': done_id, 'body': comment})
```

## 발견한 함정

### 1. `LINEAR_API_KEY`가 env에 export 안 됨
`.env` 파일에 저장돼 있지만 `export` 안 되어 있음. 스크립트에서 직접 load 필요:
```python
for line in open('/home/ubuntu/.hermes/.env').read().split('\n'):
    line = line.strip()
    if line and not line.startswith('#') and '=' in line:
        k, v = line.split('=', 1)
        os.environ[k] = v
```
또는 `subprocess.run(['bash', '-c', 'source ~/.hermes/.env && ...'])` 패턴. 단 subprocess는 child process에서만 적용.

### 2. Linear GraphQL filter 문법 — `number: { eq: 22 }` 만 동작
`identifier: { eq: "SHO-22" }` 같은 filter는 동작 안 함. number (정수) + state type (enum)만 직접 filter.

### 3. Workflow state ID는 "Done" 이름이 아닌 "completed" type으로 검색
```python
done_id = [s for s in states if s['type'] == 'completed'][0]['id']
# name이 "Done"인 것과 type이 "completed"인 것은 다를 수 있음
```

### 4. mapping.json은 양방향 키 구조
```json
{
  "<kanban_task_id>": {
    "linear_issue_id": "SHO-XX",
    "linear_url": "...",
    "kanban_updated_at": <unix_ts>,
    "linear_updated_at": "<iso8601>",
    "last_synced": "<iso8601>"
  }
}
```
kanban_task_id가 primary key. 한 Linear issue가 여러 kanban tasks (subtask) 가질 수 있으니, 이중 key 구조 고려 가능.

### 5. Kanban DB 직접 sqlite3 접근이 sync의 백엔드
`hermes kanban` CLI는 sync 자동화엔 너무 무거움. sqlite3 직접 호출이 cron sync 스크립트에 적합.
```bash
sqlite3 ~/.hermes/kanban.db "UPDATE tasks SET status = 'done', completed_at = $(date +%s) WHERE id = 't_xxx'"
```

## SHO-24 (Phase ②) 적용 계획

같은 패턴으로:
1. Phase ② 구현 완료
2. SHO-24 → Backlog → Done (해결 코멘트)
3. Kanban mirror task `t_<hex>` 생성 + Done
4. mapping.json 업데이트

## 다른 Linear state 전환 사례 (참고)

- **Backlog → Done**: `stateId = done_id` (completed type)
- **Backlog → Canceled**: `stateId = canceled_id` (canceled type)
- **Backlog → Todo** (시작): `stateId = todo_id` (unstarted type)
- **Todo → In Progress** (워크플로우에 따라 다름): `started` type

type enum은 Linear의 standard workflow에 정의됨: backlog, unstarted, started, completed, canceled, triage.

## 다음 cron sync 시 할 일

1. `~/.hermes/data/kanban_linear_mapping.json`을 source of truth로
2. Kanban의 모든 task body에 `linear_id: SHO-XX` frontmatter가 있는 것 찾기
3. mapping.json에 없는 Linear issue는 새 Kanban task 생성
4. mapping.json에 없는 Kanban task는 그대로 (Linear는 optional mirror)
5. 양쪽 모두 있는 경우 last_synced 비교 → 더 최근 쪽이 source of truth

## 검증된 safe state (2026-06-29 20:30 KST)

- Kanban DB: 1 task 추가 (t_0092361d) + done 마킹 ✅
- Linear SHO-22: Backlog → Done ✅ + comment 작성 ✅
- mapping.json: SHO-22 매핑 추가 ✅
- hermes-wiki GitHub: commit 10312ce push ✅

→ 단일 세션에서 4개 시스템 (Kanban + Linear + mapping.json + GitHub) 동시 sync 완료.

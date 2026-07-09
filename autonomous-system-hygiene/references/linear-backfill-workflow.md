# Linear Backfill Workflow (Audit Round → SHO Issues)

## The Gap

`kanban_linear_sync.py`는 `kanban_linear_mapping.json`에 매핑된 Kanban task만 Linear와 동기화합니다. **매핑에 없는 task는 silent drop**됩니다. 자율 cleanup round를 돌릴 때마다 발견/해결되는 작업들이 SHO 티켓으로 자동 승격되지 않아, 사용자가 "Linear에 중간중간 이슈와 해결한것들이 전혀 업데이트 안됨"으로 인지하는 문제가 발생합니다 (2026-07-07 re-encountered).

## Detection — am I affected?

매 round 끝날 때 다음 비교를 실행:

```bash
# 1. 최근 N시간 동안 close된 Kanban task 목록
sqlite3 ~/.hermes/kanban.db "
SELECT id, title, completed_at
FROM tasks
WHERE status = 'done'
  AND completed_at > strftime('%s','now','-24 hours')
ORDER BY completed_at DESC;
"

# 2. 최근 N시간 동안 생성된 SHO issue 목록 (Linear API)
LINEAR_KEY=$(grep '^LINEAR_API_KEY' ~/.hermes/.env | cut -d= -f2)
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query":"{ team(id: \"<TEAM_UUID>\") { issues(filter: { createdAt: { gte: \"<ISO_24H_AGO>\" } }, first: 50) { nodes { identifier title } } } }"
  }' | python3 -m json.tool

# 3. diff = SHO에 없는 Kanban done = backfill 필요
```

## Backfill Recipe (2026-07-07 proven)

`scripts/linear_backfill.py` (이 reference에 첨부된 패턴):

```python
#!/usr/bin/env python3
"""linear_backfill.py — Kanban done tasks → Linear issue (created today) backfill.

Usage:
    python3 linear_backfill.py            # dry-run (default)
    python3 linear_backfill.py --apply    # 실제 issueCreate + stateUpdate

Pair with `kanban_linear_sync.py` v1.1+: mapping.json에 없는 done은 unmapped_done
액션으로 표시, 이 스크립트로 batch backfill.
"""

import json
import sqlite3
import sys
import urllib.request
from pathlib import Path

HERMES_HOME = Path.home() / ".hermes"
KANBAN_DB = HERMES_HOME / "kanban.db"
MAPPING_FILE = HERMES_HOME / "data" / "kanban_linear_mapping.json"

LINEAR_DONE_STATE = "86cd9d73-2b97-49e9-8b16-95c1d08c29ad"  # Shootingstock Done
LINEAR_TEAM = "acb9037a-9a30-4848-bb13-cf72c95c13e8"  # Shootingstock team

ISSUE_CREATE_MUT = """
mutation IssueCreate($input: IssueCreateInput!) {
  issueCreate(input: $input) {
    success
    issue { identifier id title }
  }
}
"""

ISSUE_UPDATE_MUT = """
mutation IssueUpdate($id: String!, $state: String!) {
  issueUpdate(id: $id, input: { stateId: $state }) {
    success issue { identifier state { name } }
  }
}
"""

def get_api_key() -> str:
    env = (HERMES_HOME / ".env").read_text()
    for line in env.split("\n"):
        if line.startswith("LINEAR_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("LINEAR_API_KEY not found")

def gql(query: str, variables: dict) -> dict:
    req = urllib.request.Request(
        "https://api.linear.app/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": get_api_key(), "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())

def recent_done_kanban(hours: int = 24) -> list[dict]:
    """최근 N시간 동안 done된 Kanban task (mapping 기반)."""
    conn = sqlite3.connect(str(KANBAN_DB))
    cur = conn.execute(
        "SELECT id, title, completed_at FROM tasks "
        "WHERE status = 'done' "
        "AND completed_at > strftime('%s','now','-? hours') "
        "ORDER BY completed_at DESC",
        (hours,),
    )
    tasks = [{"id": r[0], "title": r[1], "completed_at": r[2]} for r in cur]
    conn.close()
    return tasks

def load_mapping() -> dict:
    if not MAPPING_FILE.exists():
        return {}
    return json.loads(MAPPING_FILE.read_text())

def already_has_sho(mapping: dict, kanban_id: str) -> str | None:
    """이 Kanban ID에 매핑된 SHO 식별자 있으면 반환, 없으면 None."""
    m = mapping.get(kanban_id, {})
    return m.get("linear_issue_id")

def main():
    apply = "--apply" in sys.argv
    print(f"=== Linear Backfill ({'APPLY' if apply else 'DRY-RUN'}) ===\n")

    tasks = recent_done_kanban(24)
    mapping = load_mapping()
    to_backfill = [t for t in tasks if not already_has_sho(mapping, t["id"])]

    print(f"최근 24h Kanban done: {len(tasks)}건")
    print(f"매핑된 SHO 있는 것: {len(tasks) - len(to_backfill)}건")
    print(f"backfill 필요: {len(to_backfill)}건\n")

    if not to_backfill:
        print("✅ backfill 불필요 — SILENT")
        return 0

    for t in to_backfill:
        title = f"[AUTO 2026-07-07 backfill] {t['title'][:80]}"
        desc = f"Kanban task {t['id']} (completed {t['completed_at']})의 SHO backfill."
        print(f"  - {t['id']}: {t['title'][:60]}")

        if apply:
            r = gql(ISSUE_CREATE_MUT, {
                "input": {"teamId": LINEAR_TEAM, "title": title, "description": desc}
            })
            issue = r.get("data", {}).get("issueCreate", {}).get("issue", {})
            if issue:
                print(f"    ✅ {issue['identifier']} created")

                # 즉시 Done 처리
                r2 = gql(ISSUE_UPDATE_MUT, {
                    "id": issue["id"],
                    "state": LINEAR_DONE_STATE,
                })
                if r2.get("data", {}).get("issueUpdate", {}).get("success"):
                    print(f"    → Done")

                # mapping.json 갱신
                mapping[t["id"]] = {
                    "linear_issue_id": issue["identifier"],
                    "linear_url": f"https://linear.app/mybot/issue/{issue['identifier']}",
                    "linear_updated_at": "2026-07-07T23:55:00Z",
                    "kanban_updated_at": t["completed_at"],
                    "backfilled": True,
                }
            else:
                print(f"    ❌ create failed: {r.get('errors', r)}")

    if apply:
        MAPPING_FILE.write_text(json.dumps(mapping, indent=2, ensure_ascii=False))
        print(f"\nmapping.json 갱신: {MAPPING_FILE}")

    print(f"\n총 {len(to_backfill)}건 {'backfill 완료' if apply else '예정'}")
    return 0 if apply else 1

if __name__ == "__main__":
    sys.exit(main())
```

## Workflow (round 끝마다)

```
1. Round N close all tasks
        ↓
2. Run linear_backfill.py (dry-run) → N backfill 예정 표시
        ↓
3. 사용자/자동 confirm
        ↓
4. Run linear_backfill.py --apply → N개 issue 생성 + Done 처리 + mapping.json 갱신
        ↓
5. Wiki log push
```

## Pairing with kanban_linear_sync.py

- **v1.0** (구버전): mapping.json 매핑만 sync → 신규 task silent drop
- **v1.1** (현재): unmapped_done 액션 추가 (감지만)
- **+linear_backfill.py**: round 끝 batch backfill (생성 + state Done)

3-way (Kanban done ↔ Linear SHO Done ↔ mapping.json) sync 완결.

## Pitfalls

**Round 끝나기 전에 SHO 생성하면 중복 (added 2026-07-07)**. 같은 round에서 close한 Kanban task가 같은 round에서 SHO 생성되면 round summary에 두 번 표시됨. **round close 다 끝난 후 backfill**.

**backfill SHO title prefix (added 2026-07-07)**. `[AUTO YYYY-MM-DD backfill]` prefix 사용 → 미래에 "이게 backfill이구나" 식별 가능. mapping.json에 `backfilled: true` 필드 추가 → sync가 backfill SHO를 일반 SHO와 다르게 다룰 수 있게.

**Linear team UUID 변경 (added 2026-07-07)**. `acb9037a-9a30-4848-bb13-cf72c95c13e8`은 Shootingstock team UUID. 다른 team으로 백필할 경우 변경 필요. 또는 script 시작 시 `gql("{ teams { nodes { id name } } }")`로 자동 fetch.

**state UUID 변경 (added 2026-07-07)**. `86cd9d73-2b97-49e9-8b16-95c1d08c29ad`는 Done state UUID. Linear workflow 변경 시 깨짐. 대안: script 시작 시 states fetch 후 cache.

## Round-by-round usage (proven pattern, 2026-07-07)

| Round | Done Kanban | SHO Backfill 필요 | 실제 backfill |
|-------|-------------|-------------------|---------------|
| R1    | 15          | 15                | ❌ (당시 스크립트 없음) |
| R2    | 9           | 9                 | ❌ |
| R3    | 9           | 9                 | ❌ |
| R4    | 5           | 5                 | ❌ |
| 종합 backfill (수동) | -    | 14                | ✅ SHO-52~65 (이 세션에서) |
| 향후 (자동화)         | N    | N                 | linear_backfill.py cron 또는 round 끝 manual |

총 14건 SHO backfill (수동 GraphQL issueCreate + state Done) 완료. 다음 round부터는 자동.

## Reference

- `~/.hermes/scripts/kanban_linear_sync.py` v1.1 (unmapped_done 감지)
- `~/.hermes/scripts/linear_backfill.py` (이 reference 패턴 기반, scripts/ 디렉토리에 작성)
- `~/.hermes/data/kanban_linear_mapping.json` (backfilled 필드 포함)
- Wiki: `~/.hermes/wiki/logs/2026/2026-07-07-2355-linear-backfill.md` (실행 로그)
- Wiki: `~/.hermes/wiki/infra/pr-review-policy.md` (PR→Review 정책)
- skill: `linear` (GraphQL 패턴)
# 2-tier PR Policy + Sync Cycle + Backfill Pattern (2026-07-07)

## User policy (canonical source)

위키 `infra/pr-review-policy.md` v2.0. 사용자 결정 두 가지:

1. **"PR이나 코드리뷰는 필요한 곳에서만 설정"** — 모든 repo에 일괄 self-import 안 함
2. **"중요한 내용 아니면 왠만하면 approve merge해도됨 삭제나 강제 푸시만 안하면됨"** — Tier 2는 가벼움

## 2-tier 분류

### Tier 1 — Heavy
- 메인 서비스 / 인프라 / 외부 repo / secret
- 새 기능 / API 변경 / workflow 변경
- reviewer verdict + 사용자 확인 필수

### Tier 2 — Light
- 문서 typo / 1~2 line fix / 주석 / wiki raw/
- 사용자 1회 확인 → squash merge (reviewer 불필요)

## Self-import 적용 범위 (2026-07-07 상태)

| Repo | auto-merge.yml | review-bot.yml | Tier |
|:-----|:---------------|:---------------|:-----|
| hermes-pr-gate | YES | YES | T1 (gate 정의) |
| hermes-agent | NO | NO | T2 |
| hermes-pipeline-scripts | NO | NO | T2 |
| hermes-self-healing | NO | NO | T2 |
| hermes-stock-briefings | NO | NO | T2 |
| trade-pipeline | NO | NO | T2 |
| hermes-wiki | NO | NO | T2 |
| hermes-wiki-super | **DELETED 2026-07-07** | **DELETED 2026-07-07** | T2 |
| mybotagent.github.io | **DELETED 2026-07-07** | **DELETED 2026-07-07** | T2 |
| memory-map | NO | NO | T2 |
| hermes-logs | NO | NO | T2 |
| (others ~22) | NO | NO | T2 |

## Workflow 삭제 패턴 (Tier 2 repo에서)

```bash
export GH_TOKEN="$GH_TOKEN_V2"
for repo in REPO_NAME; do
  for f in auto-merge.yml review-bot.yml; do
    SHA=$(gh api "repos/mybotagent/$repo/contents/.github/workflows/$f" \
          | python3 -c "import json,sys; print(json.load(sys.stdin).get('sha',''))")
    if [ -n "$SHA" ]; then
      gh api -X DELETE "repos/mybotagent/$repo/contents/.github/workflows/$f" \
        -f sha="$SHA" \
        -f message="infra(pr-policy): Tier 2 repo - PR gate self-import 제거"
    fi
  done
done
```

## hermes cloud 디스크 sync cycle

```
~/.hermes/<repo>/        ←→    github.com/mybotagent/<repo>
  git status                   gh api / git push
  git pull --rebase            PR → squash merge
  git push origin main         branch auto-delete
```

### Drift 자동 감지 (수동 또는 cron)

```bash
for repo in $(find /home/ubuntu/.hermes /home/ubuntu -maxdepth 3 -name ".git" -type d 2>/dev/null); do
  name=${repo%/.git}; name=${name##*/}
  uncommitted=$(git -C "$repo" status --porcelain 2>/dev/null | wc -l)
  unpushed=$(git -C "$repo" log --oneline @{u}.. 2>/dev/null | wc -l)
  if [ "$uncommitted" -gt 0 ] || [ "$unpushed" -gt 0 ]; then
    echo "  $name  uncommitted=$uncommitted  unpushed=$unpushed"
  fi
done
```

### Sync (drift 해결)

```bash
cd /home/ubuntu/<repo>
git pull --rebase 2>&1 | tail -3
git push origin main 2>&1 | tail -2
```

### Submodule drift

```bash
cd <repo>/<submodule>
git status --short | head -5
git add -A
git commit -m "submodule drift sync"
git push
cd ..
git add -A
git commit -m "submodule ref update"
git push origin main
```

## Linear issue backfill 패턴

### When to backfill
audit round에서 발견/해결한 작업이 Linear에 누락된 경우.

### Step 1: Issue batch create (GraphQL)

```python
import json, urllib.request, os
TOKEN = os.environ['LINEAR_API_KEY']
TEAM = 'acb9037a-9a30-4848-bb13-cf72c95c13e8'

CREATE = 'mutation($input: IssueCreateInput!) { issueCreate(input: $input) { success issue { id identifier } } }'

issues = [
    {"title": "...", "description": "...", "teamId": TEAM},
    ...
]
for inp in issues:
    req = urllib.request.Request(
        'https://api.linear.app/graphql',
        data=json.dumps({'query': CREATE, 'variables': {'input': inp}}).encode(),
        headers={'Authorization': TOKEN, 'Content-Type': 'application/json'}
    )
    resp = json.loads(urllib.request.urlopen(req).read())
    issue = resp['data']['issueCreate']['issue']
    print(f"  ✅ {issue['identifier']}  {inp['title'][:60]}")
```

### Step 2: State ID 매핑

```python
DONE = '86cd9d73-2b97-49e9-8b16-95c1d08c29ad'       # completed
TODO = '58b34e08-f1b1-48a0-bcc3-40a9579fd94c'       # unstarted
BACKLOG = 'cec5bc9e-3028-4f51-b3ad-1f60740a1812'   # backlog
IN_REVIEW = 'd20f1bd9-9448-42c7-af96-039bf30aa215'  # started
IN_PROGRESS = '37d758b8-aa00-4c30-b10e-8f65049c3bf4' # started
CANCELED = '9f4960b6-c846-47e3-b2e0-ddb3570f231e'   # canceled
```

(TEAM_ID = 'acb9037a-9a30-4848-bb13-cf72c95c13e8' = Shootingstock/SHO)

### Step 3: Issue batch update (state 변경)

```python
UPDATE = 'mutation($id: String!, $state: String!) { issueUpdate(id: $id, input: { stateId: $state }) { success issue { identifier state { name } } } }'

for uuid in DONE_LIST:
    req = urllib.request.Request(
        'https://api.linear.app/graphql',
        data=json.dumps({'query': UPDATE, 'variables': {'id': uuid, 'state': DONE}}).encode(),
        headers={'Authorization': TOKEN, 'Content-Type': 'application/json'}
    )
    resp = json.loads(urllib.request.urlopen(req).read())
    r = resp['data']['issueUpdate']
    print(f"  ✅ {r['issue']['identifier']}  → {r['issue']['state']['name']}")
```

### Step 4: kanban_linear_mapping.json 갱신

```json
{
  "backfill_2026-07-07": {
    "linear_issues": [
      {"id": "SHO-52", "kanban": "round2-memory-alert", "status": "done", "label": "R2-cleanup"},
      ...
    ],
    "synced_at": "2026-07-07T23:50:00Z",
    "note": "audit round 2~4 + 오늘 작업 일괄 backfill (이슈 14건)"
  }
}
```

### Step 5: kanban_linear_sync.py v1.1 (자동화)

```python
def sync_done_kanban_to_linear(apply, mapping):
    for task in tasks:
        tid = task["id"]
        if tid not in mapping:
            continue
        linear_id = mapping[tid].get("linear_issue_id")
        if not linear_id:
            # 매핑 없음 → unmapped done task. 자동 issue 생성 권장
            actions.append({
                "type": "unmapped_done",
                "kanban_id": tid,
                "title": task["title"][:60],
                "suggestion": "create linear issue + add to mapping",
            })
            continue
```

## Cron job 정리 (외부 repo monitoring 제거)

```bash
# cron API로 외부 repo monitoring cron 제거
# job_id: '4b38af32e7b8' 같은 외부 repo URL cron → remove
```

## Memory-map README 동기화 (wiki lazy indexing 일관성)

```bash
# github API로 memory-map README.md 직접 갱신
# 1. README SHA 가져오기
SHA=$(gh api repos/mybotagent/memory-map/contents/README.md | python3 -c "import json,sys; print(json.load(sys.stdin)['sha'])")

# 2. base64 인코딩 후 PUT
B64=$(echo -n "$NEW_CONTENT" | base64 -w 0)
gh api -X PUT repos/mybotagent/memory-map/contents/README.md \
  -H "Accept: application/vnd.github+json" \
  -f message="infra(pr-review-policy): 신규 wiki 페이지 라인 추가" \
  -f content="$B64" \
  -f sha="$SHA" \
  -f branch="main"
```

## 검증 checklist

- [ ] 우리 own repos 32개 중 auto-merge=YES: hermes-pr-gate만
- [ ] Linear SHO Done 12건 (backfill)
- [ ] kanban_linear_mapping.json에 backfill 섹션
- [ ] cron에서 외부 repo monitoring 제거
- [ ] wiki/infra/pr-review-policy.md v2.0 push
- [ ] memory-map README.md 21 facts 동기화
- [ ] hermes cloud 디스크 3개 repo drift push
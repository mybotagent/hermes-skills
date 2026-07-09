# Linear / Kanban Idempotency (v1.3 — 2026-07-07 검증)

`daily-repo-orchestrator` cron이 매일 22:00 UTC (= 07:00 KST) trigger되면 같은 top-3 candidate를 다시 처리함. v1.2까지는 그대로 `issueCreate`/Kanban create를 불러 SHO-46/47/48/49... 가 누적됐고, `t_xxxxxx` Kanban 태스크가 매일 3개씩 쌓였음.

v1.3에서 둘 다 **제목 기반 dedupe** 도입. 실측 결과: SHO-49/50/51 재호출 시 SHO-52 안 만들어지고 `(reused, no id captured)` log만 박힘.

---

## Linear — GraphQL eqIgnoreCase filter

```python
mutation = """
    mutation IssueCreate($input: IssueCreateInput!) {
      issueCreate(input: $input) { success issue { identifier url } }
    }"""

def _linear_find_existing(title: str) -> dict | None:
    query = """
        query Q($title: String!) {
          issues(filter: {title: {eqIgnoreCase: $title}}, first: 1) {
            nodes { identifier url }
          }
        }"""
    req = urllib.request.Request(
        "https://api.linear.app/graphql",
        data=json.dumps({"query": query, "variables": {"title": title}}).encode(),
        headers={"Authorization": LINEAR_KEY, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        r = json.loads(urllib.request.urlopen(req, timeout=10).read())
        nodes = (r.get("data") or {}).get("issues", {}).get("nodes", [])
        return nodes[0] if nodes else None
    except Exception:
        return None


def mirror_to_linear(top):
    out = []
    for c in top:
        title = f"[AUTO {TODAY}] {c['title']}"
        # idempotency: 동일 title 사전 검색
        existing = _linear_find_existing(title)
        if existing:
            out.append({"candidate": c,
                        "linear_id": existing["identifier"],
                        "linear_url": existing["url"]})
            log_event("mirror", "linear-reuse", id=existing["identifier"])
            continue
        # ... mutation 본격 실행
```

### 함정 & 해결

| 함정 | 실증 | 해결 |
|---|---|---|
| `filter: {identifier: {eq: ...}}` GraphQL 검증 실패 | `Identifier is not defined by type IssueFilter` | `title.eqIgnoreCase` 만 가능. identifier는 검색 전용 field 아님 |
| `title` raw GraphQL String 값 vs structured search | `identifier.{in: [...]}` 같은 advanced query만 가능 | `eqIgnoreCase` 사용 권장 |
| Unicode (한글/이모지) 검색 안 됨 | SHO-49 "헤르메스 생태계 종합 감사" 정확히 매칭 | `eqIgnoreCase` 는 Unicode 안전. case-insensitive로 작동 |
| Linear 응답 캐시 (1~2초) | 같은 1분 내 2회 호출 시 stale 가능 | 1 cycle 내 동일 title 2번 이상 안 부름 (top-3 중복 불가). 또 dedupe 정확 |

### Log keywords

- `mirror/linear-reuse id=SHO-XX key=<repo>::<title>` — 재사용 시
- `mirror/linear id=SHO-XX` — 신규 생성 시
- `mirror/linear-fail err=<...>` — GraphQL 에러 (보통 token scope)

---

## Kanban — `hermes kanban list --json` 으로 set lookup

```python
def _kanban_list_existing_titles(hermes_home: Path) -> set[str]:
    try:
        res = subprocess.run(
            ["hermes", "kanban", "list", "--json"],
            capture_output=True, text=True, timeout=15,
            cwd=str(hermes_home.parent),
        )
        data = json.loads(res.stdout)
        if not isinstance(data, list):
            return set()
        today_marker = f"[Auto {TODAY}]"
        return {t.get("title", "")[:80]
                for t in data if today_marker in t.get("title", "")}
    except Exception:
        return set()


def mirror_to_kanban(top):
    existing_titles = (
        _kanban_list_existing_titles(HERMES_HOME) if not DRY_RUN_MIRROR else set()
    )
    for c in top:
        title = f"[Auto {TODAY}] {c['title'][:60]}"
        if DRY_RUN_MIRROR:
            # dry path
            ...
        if title[:80] in existing_titles:
            log_event("mirror", "kanban-reuse", title=title[:60])
            out.append({"candidate": c, "kanban_task_id": "(reused, no id captured)"})
            continue
        # real create
        ...
```

### 함정 & 해결

| 함정 | 실증 | 해결 |
|---|---|---|
| `hermes kanban create --title ... --body ...` | `unrecognized arguments: --board --title` | `--title` 옵션 없음. **positional title** 만 받음: `hermes kanban create <title> --body <body>` |
| stdout 파싱: `task_id = stdout.split()[0]` | `['', '', ...]`, 또는 `Task`/`Issue` 같은 prefix | 형식: `Created t_xxxxxxxx  (ready, assignee=-)`. ID 추출: `re.search(r"(t_[a-z0-9]+)", stdout).group(1)` |
| `--status ready --status backlog` (반복) | `error: argument --status: invalid choice: 'backlog' (choose from 'archived', 'blocked', 'done', 'ready', 'review', 'running', 'scheduled', 'todo', 'triage')` | 2회 호출 의미 없음. **하나로 부족**. 대신 `--json` 으로 전체 list 받고 Python `set` lookup |
| `kanban board` 가 default board 자동 | `--board hermes` 없이도 default 적용 | idempotency 시 board 명시 불필요. mirror_to_kanban default board 사용 시 `--board` 인자 생략 |
| archived tasks가 set에 포함됨 | `kanban list --json` 은 archived default 포함 (--archived 옵션 flag 의미 다름) | today-marker (`[Auto TODAY]`) 가 title에 있는지로만 필터. archived도 동일 ID이므로 skip 작동 |

### Log keywords

- `mirror/kanban-reuse title=<auto-today-prefix>...` — 재사용 시 (id 없음)
- `mirror/kanban task=t_xxxxxx` — 신규 생성 시

---

## 실전 cron 출력 (2026-07-07 01:42 KST)

```
[harvest] scan n=30
[harvest] candidates n=7
[prioritize] score top=[audit, epic, readme]
[mirror] linear-reuse id=SHO-49 key=mybotagent/hermes-wiki::[Audit 2026-07-03] 헤르메스 생태계 종합 감사 — 3 TODO actions
[mirror] linear-reuse id=SHO-50 key=mybotagent/trade-pipeline::...
[mirror] linear-reuse id=SHO-51 key=mybotagent/mybotagent.github.io::❗ README.md 누락
[mirror] kanban-reuse title=[Auto 2026-07-07] [Audit 2026-07-03] 헤르메스 생태계 종합 감사 — 3 TODO
[mirror] kanban-reuse title=[Auto 2026-07-07] [Epic] 2026-07-01 1차 시스템 점검 (BE + Cron 404
[mirror] kanban-reuse title=[Auto 2026-07-07] ❗ README.md 누락
MODE: PRODUCTION
  harvest=real mirror=real fix=dry email=dry
```

→ **cycle당 신규 mirror 0건** (idempotent 정상). 한 시간에 6+ 회 호출해도 reuse log만 박힘.

---

## Idempotency가 안 되는 케이스 (수동 archive 필요)

- v1.2에서 만든 SHO-46/47/48 (idempotency 도입 전 중복분) — 사용자 confirm 후 `issueArchive` mutation으로 정리. 실측 코드:

```bash
LINEAR=$(grep LINEAR_API_KEY ~/.hermes/.env | cut -d= -f2- | tr -d '"')
for id in SHO-46 SHO-47 SHO-48; do
  curl -s -X POST https://api.linear.app/graphql \
    -H "Authorization: $LINEAR" \
    -H "Content-Type: application/json" \
    -d "{\"query\":\"mutation I(\$id:String!){ issueArchive(id:\$id){ success } }\",\"variables\":{\"id\":\"$id\"}}"
done
```

→ 2026-07-07 자가 정리 완료 (`{data:{issueArchive:{success:true}}}`).

- v1.2에서 만든 `[Auto 2026-07-07]` 6개 Kanban task — 동일 패턴으로 `hermes kanban archive` 권장:
  ```bash
  hermes kanban archive t_xxxxxx  # archived status 로 이동. list --json에선 여전히 보임.
  ```

---

## Related

- `stage-flags-and-modes.md` — DRY_RUN_xxx 4개 env var 매트릭스
- Linear GraphQL reference: https://developers.linear.app/docs/graphql/working-with-the-graphql-api
- hermes kanban docs: `hermes kanban --help` + `kanban.py` source (in hermes-agent distribution)

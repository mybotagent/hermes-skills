# Post-Task Tracking Sync (Linear + Kanban + GitHub + Wiki)

작업이 끝난 후 사용자 추적 가능하도록 4개 시스템에 동시 동기화하는 워크플로. aiprofit의 "코드랑 문서 업데이트해 리니어 칸반 github까지" 요청에 대응.

## 4-way sync 순서 (멱등, 부분 실패 안전)

```
1. Linear: epic + N sub-issues 생성
2. Kanban: tasks mirror (body에 linear_id + URL)
3. mapping.json: {linear_issue_id: {kanban_task_id, ...}}
4. GitHub: epic issue 생성 + cross-link
5. Wiki: 변경 이력 페이지 갱신 + push
```

## 1) Linear: epic + sub-issues

`create-issue`에 `--parent` 옵션으로 epic-sub 관계 생성. `--state`는 지원 안 됨 → 생성 후 `update-status` 별도 호출.

```python
# 핵심: create-issue는 --state 미지원
EPIC = create_issue(team="SHO", title="Epic: ...", priority=3)
# → SHO-31

# sub-issues
for work in [work1, work2, work3, work4, work5, work6]:
    issue = create_issue(team="SHO", title=work.title, parent=EPIC['id'],
                         description=work.description, priority=work.priority)
    # 상태는 default (Backlog). Done으로 옮기려면:
    update_status(issue['identifier'], "Done")
```

**실행 패턴 (skill 100% 활용)**:
```bash
SCRIPT=$(find ~/.hermes -path '*productivity/linear/scripts/linear_api.py' | head -1)
EPIC_UUID="c2055495-..."  # create-issue 응답의 id 필드
DONE_UUID="86cd9d73-..."  # list-states --team SHO 결과의 Done type
python3 "$SCRIPT" create-issue --team SHO --title "..." --parent "$EPIC_UUID" ...
python3 "$SCRIPT" update-status SHO-XX Done
```

## 2) Kanban: tasks mirror

`~/.hermes/kanban.db`의 `tasks` 테이블에 직접 INSERT. body에 linear_id + URL + GitHub commit SHA 포함.

```sql
INSERT INTO tasks (id, title, body, assignee, status, priority, created_by, created_at, started_at, completed_at, workspace_kind, max_retries) VALUES
('t_xxxxxx', '[SHO-32] 작업명', '---
linear_id: SHO-32
linear_url: https://linear.app/shootingstock/issue/SHO-32
github_trade_pipeline: f3bd5d9
github_hermes_wiki: 209e826
---', 'hermes', 'done', 3, 'user', <epoch>, <epoch>, <epoch>, 'scratch', 0);
```

**id 생성**: `t_$(openssl rand -hex 4)` 또는 secrets.token_hex(4). 충돌 없으면 OK.

**body는 frontmatter 형식 (--- 구분자)** — 파서가 자동으로 메타데이터 추출.

## 3) mapping.json

`~/trade-pipeline/data/kanban_linear_mapping.json` (gitignore되지만 daily cron이 읽음).

```json
{
  "SHO-31": {
    "linear_issue_id": "SHO-31",
    "linear_url": "https://linear.app/shootingstock/issue/SHO-31",
    "kanban_task_id": "EPIC",
    "kanban_updated_at": 1751340000,
    "linear_updated_at": 1751340000,
    "last_synced": "2026-07-01T11:30:00Z"
  },
  "SHO-32": {
    "linear_issue_id": "SHO-32",
    "linear_url": "https://linear.app/shootingstock/issue/SHO-32",
    "kanban_task_id": "t_017a6a02",
    "kanban_updated_at": 1751340000,
    "linear_updated_at": 1751340000,
    "last_synced": "2026-07-01T11:30:00Z"
  }
}
```

daily cron (Kanban → Linear)이 이 파일을 읽어 양방향 sync. epic은 `kanban_task_id: "EPIC"`로 표시.

## 4) GitHub: epic issue

`gh` CLI로 cross-link 포함 epic issue 생성. Linear + Kanban + Wiki URL 모두 본문에 포함.

```bash
gh issue create --repo mybotagent/trade-pipeline \
  --title "[Epic] YYYY-MM-DD 작업명" \
  --body "## 🌐 Epic
- Linear: SHO-31
- Kanban mirror: data/kanban_linear_mapping.json
- Wiki: hermes-trading-log.md

### 작업 내역
| # | Linear | 작업 | Commit |"
```

**gh issue edit으로 본문 cross-link 추가** (생성 직후):
```bash
gh issue edit 1 --body "..."  # cross-link 강화
```

## 5) Wiki: 변경 이력

`~/.hermes/wiki/hermes-trading-log.md` (또는 해당 도메인 log 페이지)에 항목 추가.

```markdown
## [2026-07-01] 작업 제목

**Linear Epic**: SHO-31 (URL) — 6 sub-issues 모두 Done
**GitHub**: trade-pipeline issue #1 (URL)

### 작업 6건
| # | Linear | 작업 | Commit/Action |
| 1 | SHO-32 | ... | ... |
| ...
```

wiki는 git push 필수 (사용자 정책: "세션종료시 git push필수").

## Pitfalls (실전 교훈)

1. **`create-issue`는 `--state` 미지원** → 생성 후 `update-status` 별도 호출 필수.
2. **priority 값**: 0=None, 1=Urgent, 2=High, 3=Medium, 4=Low. 사후 등록은 3 (Medium) 권장.
3. **body에 commit SHA 필수**: 나중에 "이거 어느 commit?" 물어볼 때 추적 가능. description field + Kanban body 양쪽에.
4. **epic은 Kanban task 미생성**: `kanban_task_id: "EPIC"`으로 표시. 또는 epic summary용 1개 task 생성.
5. **`id` 충돌**: `t_xxxxxx` 형식 + `openssl rand -hex 4`면 65,536 조합. 일일 작업 6~10개라면 충돌 무시 가능.
6. **GitHub issue 본문 cross-link**: 한 번에 다 쓰지 말고 `gh issue create` → `gh issue edit` 두 단계. 생성 시점에는 Linear ID만 알 수 있고, sub-issue ID는 생성 후 받아야 함.
7. **wiki push 누락 금지**: 사용자 정책상 세션 종료 전 미푸시 commit은 위반. `git push origin main` 명시적 호출.
8. **순서**: Linear → Kanban → mapping.json → GitHub → Wiki. 역순 시 cross-link가 dangling.

## Cross-link 매트릭스 (예시: 6개 작업 + epic)

| Linear | Kanban task | GitHub | Wiki |
|:-------|:------------|:-------|:-----|
| SHO-31 (epic) | — | trade-pipeline#1 | log entry + hub |
| SHO-32 | t_017a6a02 | commit SHA | 작업별 페이지 |
| SHO-33 | t_e51590d7 | (분석 노트) | 작업별 페이지 |
| ... | ... | ... | ... |

각 시스템에서 한 곳 진입해도 다른 3곳으로 점프 가능 → 작업 추적성 100%.

## Skill class

이 워크플로는 "**post-task cross-system sync**" 클래스. 다른 영역(예: A/B 테스트 결과, 마케팅 캠페인, 코드 리뷰 후속 조치) 작업 종료 시에도 동일 패턴 적용 가능:

1. Tracking 도구 (Linear/Jira/Asana) → epic + sub-issue
2. Local task board (Kanban/Notion) → mirror
3. Version control (GitHub/GitLab) → epic issue + cross-link
4. Documentation (Wiki/Notion) → 변경 이력
5. mapping.json → 자동 sync 소스

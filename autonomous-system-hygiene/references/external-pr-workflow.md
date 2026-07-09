# PR Submission & Review Workflow — Own vs External

**Status**: PR 제출은 단계의 시작일 뿐, 끝 ❌ (user-explicit 2026-07-07). **그러나 target이 어디냐에 따라 정책이 다름**.

> "반드시 PR→Review 과정을 거쳐야함"
> "내 말은 우리 github내에서 말한거였는데?"
> — aiprofit, after external PR was opened against user intent

## Target 분기 — Own vs External (added 2026-07-07)

### Case A: mybotagent own repo PR (기본값, **사용자 의도와 일치**)

대상: `mybotagent/hermes-wiki`, `mybotagent/memory-map`, `mybotagent/hermes-agent` 등 32개 own repo.

```
[1] Branch 생성 (own repo 내에서)
    git checkout -b fix/<short-desc>
    ↓
[2] Commit + push (own repo origin)
    ↓
[3] PR 생성: gh pr create --repo mybotagent/<repo>
    ↓
[4] Reviewer 자동: hermes-pr-gate의 auto-review bot이 verdict 작성
    ↓
[5] Verdict 받기:
    - Approve → squash merge (사용자 개입 불필요)
    - Changes Requested → fix commit 추가 → verdict 재확인
    - Blocked → 사용자 결정 영역으로 escalate
    ↓
[6] Merge 후 branch 삭제 + Kanban task close
```

**핵심**: 모든 단계가 **own repo 안에서** 순환. reviewer가 우리 인프라(`hermes-pr-gate`)의 bot.

### Case B: External upstream PR (fork → upstream)

대상: `NousResearch/hermes-agent` 등 외부 upstream. **사용자 명시 OK 후에만**.

```
[1] 사용자 confirm: "외부 repo PR 만들어도 돼?"
    → OK 받기 전까지 ❌ 진행 금지
    ↓
[2] Fork: gh repo fork <upstream> --remote-name fork
    ↓
[3] Branch + commit + push + gh pr create --repo <upstream>
    ↓
[4] 외부 reviewer 대기 (1~24h+)
    ↓
[5] Reviewer comment → 자동 알림 → 코드 수정 → push
    ↓
[6] All reviewers approved → upstream maintainer가 merge 결정
```

**핵심**: 우리 정책 무관. upstream maintainer가 merge 권한. 사용자 OK 필수.

### 판단 신호 (added 2026-07-07)

자율 사이클에서 "Fix PR" 요청 받으면 **반드시 target 먼저 확인**:

| 신호 | Target |
|---|---|
| Issue가 우리 own repo에서 발견 | **Case A** (own) |
| 사용자가 "우리 github" / "내 repo" / "mybotagent" 강조 | **Case A** (own) |
| 사용자가 "외부" / "upstream" / "NousResearch" / "fork" 명시 | **Case B** (external) — **OK 먼저** |
| Issue tracker가 외부 repo (e.g. github.com/NousResearch/...) | **Case B** (external) — **OK 먼저** |
| 애매하면 | **사용자에게 clarify** |

### Pitfall — 외부 repo PR default 착각 (added 2026-07-07)

2026-07-07 자율 사이클에서 발생한 실패 패턴:
1. 사용자가 "Fix PR 하기" 명령
2. GitHub issue search → 외부 `NousResearch/hermes-agent#60258` 발견 (외부 repo라 글로벌 검색에 먼저 hit)
3. **외부 fork 생성 + fix 작성 + PR #60279 push** (autonomous mode에서 사용자 confirm 없이)
4. 사용자가 깨어나서 "내 말은 우리 github내에서 말한거였는데?" → 즉시 close + 정리

**교훈**: global GitHub search는 우리 own repo보다 upstream이 먼저 hit될 수 있음. 사용자가 "PR" 하면 **무조건 own repo부터** 탐색.

**판단 체크리스트 (PR 만들기 전)**:
- [ ] target repo가 `mybotagent/*`인가? YES → Case A 진행
- [ ] NO면 → 사용자 confirm 받기 (clarify tool)
- [ ] upstream issue가 명확한 경우만 Case B (사용자 OK 후)

### Case C — Wrong target recovery (added 2026-07-07, re-encountered)

Case B로 시작했다가 사용자 교정 시 즉시 복구 프로토콜. 사용자 재-confirm 불필요 (의도 명확).

**증상**: 사용자가 "내 말은 우리 github내서..." / "그게 아니라..." 등으로 Case B 진행 후 방향 수정 요청.

**복구 5단계 (자동 진행)**:
1. **외부 PR close** — `gh pr close <N> --repo <wrong-org>/<repo>` (실패 시 REST: `gh api -X PATCH repos/<wrong>/pulls/<N> -f state=closed`)
2. **fork 브랜치 삭제** — `gh api -X DELETE repos/mybotagent/<fork>/git/refs/heads/<branch>`
3. **hermes cloud 디스크 origin 검증** — `~/.hermes/<repo>` 또는 `~/mybotagent/<repo>`의 `git remote -v`. upstream이면 우리 fork로 변경:
   ```bash
   git remote set-url origin https://github.com/mybotagent/<repo>.git
   git fetch origin && git reset --hard origin/main
   git branch -D <stale-fix-branch>
   ```
4. **PR 모니터링 cron 정리** — 외부 PR URL monitoring하는 cron은 무의미 → `cronjob action=remove`
5. **wiki 정책 페이지에 기록** — `wiki/infra/pr-review-policy.md`에 recovery case 추가

**시간**: ~3분. **비용 교훈**: Case C 복구 = 3분. 잘못된 Case B 전체 (PR + branch + cron + monitor, 사용자 "wrong target" 후 cleanup) = 10분+. **처음부터 Case A 우선 + 애매하면 clarify가 cheaper**.

**판단 기준 (autonomous mode에서)**: PR 만들기 전 `gh repo view <owner>/<repo>`로 org 확인 → `mybotagent` 아니면 사용자 confirm 또는 작업 거부.

### Real example (2026-07-07)

1. User said "Fix PR 하기" → Agent picked upstream issue #60258 → opened PR #60279 to NousResearch/hermes-agent (Case B)
2. User: "내 말은 우리 github내서 말한거였는데?" → PR #60279 closed (Case C)
3. Origin remote on `~/.hermes/hermes-agent` switched from NousResearch → mybotagent fork
4. ~560 commit drift fast-forwarded

**Lesson**: ask "PR은 mybotagent own repo or upstream?" BEFORE creating the fork branch.

## Full workflow (Case A — own repo, 기본값)

```
[1] Branch + commit + push (own repo)
    ↓
[2] gh pr create --repo mybotagent/<repo>
    ↓
[3] Register PR in ~/.hermes/scripts/pr_review_monitor.py
        python3 ~/.hermes/scripts/pr_review_monitor.py --add <url>
    ↓
[4] Cron: 3x daily KST polling (auto-review bot verdict)
        0 0,5,10 * * 1-5 → pr_review_check.sh
        (deliver=local, 변화 시 Discord 알림)
    ↓
[5] Verdict = Approve → squash merge --delete-branch
[5b] Verdict = Changes Requested → fix commit → push → [3] 반복
```

## Pitfall — half-baked 단계 회피

사용자 교정 (2026-07-07): "더 나은 방식이 있어?" / "본질을 바꿔주고"

→ **Half-baked 단계를 거치지 말고, 사용자가 단계적으로 요구할 때 처음부터 본질(architecture-level) 변경을 제안**.

예: memory.md 압축에서
- Round 1: § 구분자 + ctx 본문 → 1,107 chars (50%) → 표면적 해결
- Round 2: KEY[]+FILE inverted index → 1,293 chars (59%) → 여전히 본문 inject
- Round 3 (본질): Tool-as-Memory → 306 chars (14%) → 진짜 해결

**3 round 동안 half-baked를 거친 후 사용자가 "본질 바꿔"라고 강제함**. 다음 회에는 처음부터 본질 변경 제안.

**판단 기준**:
- size 줄임 ≠ 본질 해결 (memory는 매 세션 inject됨)
- 압축 룰 추가는 단기 개선
- 진짜 해결 = 구조 변경 (tool-based, lazy, pointer-only)

## State persistence

`~/.hermes/pr_monitor.json`:
```json
{
  "prs": {
    "https://github.com/owner/repo/pull/123": {
      "repo": "owner/repo",
      "pr_number": 123,
      "last_check": "2026-07-07T...",
      "last_data": { "state": "open", "reviews": [...], "comments": [...] }
    }
  }
}
```

Git-ignored (state file, not part of repo).

## Token scope caveat

`gh pr view --json comments` requires `read:org` or `read:discussion` scope.
Default personal tokens only have `repo`. Workaround:
- Use only `--json state,reviews,statusCheckRollup` (works with `repo` scope)
- Trade-off: cannot detect general PR comments, only formal reviews + CI

## Cron wrapper

```bash
#!/bin/bash
# pr_review_check.sh
set -uo pipefail
OUTPUT=$(python3 ~/.hermes/scripts/pr_review_monitor.py 2>&1)
if echo "$OUTPUT" | grep -qE "\[(STATE|REVIEW|COMMENT|CI)\]"; then
  echo "📬 **PR Review Update**"
  echo "$OUTPUT"
fi
```

## Reference

- `~/.hermes/scripts/pr_review_monitor.py` (5.4KB)
- `~/.hermes/scripts/pr_review_check.sh` (647B)
- Wiki: `~/.hermes/wiki/infra/pr-review-policy.md` (own vs external 정책 명문화)
- Wiki: `~/.hermes/wiki/infra/github-pr-automation-policy.md` (claude-code-action 금지)
- hermes-pr-gate: `mybotagent/hermes-pr-gate` (CI + auto-review + auto-fix loop)
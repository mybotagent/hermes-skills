---
name: github-pr-review-pipeline
description: |
  Build / maintain an automated GitHub PR review + auto-merge gate
  pipeline using a direct LLM API call (DeepSeek V4 Flash —
  cheapest model, OpenAI-compatible) and a GitHub Actions workflow
  pair. Use when the user wants auto-review of every PR with verdict
  comments, or auto-merge only of PRs whose verdict is "Approve"
  (no 🔴/🟠), without installing the anthropics/claude-code-action
  GitHub App or any other App. Triggers: "PR 자동 리뷰", "리뷰 봇",
  "자동 머지 정책", "심각성 높은 것만 자동 머지", "verdict", or mentions
  DEEPSEEK_API_KEY + GitHub Actions together.

  As of 2026-07-07 the canonical auto-merge.yml is **v2**
  (concurrency group + newest-sha verdict polling) — replaces the v1
  worst-of polling that masked fix re-reviews for 6+ minutes. See
  Pitfall 8 (superseded) and `references/auto-merge-v2-pitfalls.md`.

  **2026-07-17: 전환 완료 — MiniMax M3 → DeepSeek V4 Flash**.
  이제 review bot은 DeepSeek V4 Flash($0.14/M input, $0.28/M output)
  을 사용한다. MiniMax 관련 설정은 모두 deprecated.
---

# GitHub PR Review Pipeline (LLM-based, no claude-code dep)

## Architecture

Two workflows, both on `pull_request_target` (NOT `pull_request` —
see Pitfall 1):

| Workflow | Trigger | Job | Purpose |
|---|---|---|---|
| `review-bot.yml` | `pull_request_target: [opened, synchronize, reopened, ready_for_review]` | `review` | Fetch diff → call LLM → post verdict comment |
| `auto-merge.yml` | `pull_request_target: [...]` (same trigger) | `auto-merge` | Poll comments for `**Verdict:**` → squash-merge if Approve |

Plus a Python script `scripts/review_pr.py` invoked by review-bot.
The script calls DeepSeek V4 Flash (OpenAI `POST /v1/chat/completions`),
the cheapest available model ($0.14/M input).

Both workflows need:
- `permissions: contents: write, pull-requests: write, issues: write`
- The default `GITHUB_TOKEN` secret is sufficient — no GitHub App install

## Repository secrets (register via API, see `references/`)

- `DEEPSEEK_API_KEY` — the LLM key. Stored as a GitHub secret via sealed box.
- `DEEPSEEK_BASE_URL` — **must** be `https://api.deepseek.com/v1`
  (OpenAI-compatible endpoint).
  - API format: `POST /v1/chat/completions` with `Authorization: Bearer <key>`
  - Model: `deepseek-v4-flash` (cheapest DeepSeek model)
  - Pricing: $0.14/M input, $0.28/M output (cache miss); $0.0028/M input (cache hit)

> **2026-07-17: MiniMax M3 → DeepSeek V4 Flash 전환 완료**
> 이전에는 `MINIMAX_API_KEY` / `MINIMAX_BASE_URL` (Anthropic-compat)를 사용했으나,
> DeepSeek V4 Flash가 약 50~70% 저렴하여 전환.
> 기존 MiniMax 설정이 남아있는 레포는 다음으로 변경: secrets 이름, workflow env, script 내 API call.

## Verdict format (LLM must return exactly this on first line)

```
**Verdict:** Approve
**Verdict:** Changes Requested
**Verdict:** Blocked
```

Severity mapping the LLM follows:

| Worst finding | Verdict |
|---|---|
| 🔴 critical ≥ 1 | **Blocked** |
| 🟠 major ≥ 1, no 🔴 | **Changes Requested** |
| only 🟡/⚪, or none | **Approve** |

Auto-merge policy:
- `Approve` AND `mergeable_state ∈ {clean, unstable, behind}` → squash-merge
- Anything else → post comment explaining why + leave PR open for human

## Implementation order

1. Add `scripts/review_pr.py` (drop-in template under `scripts/`).
2. Add `.github/workflows/review-bot.yml` (single job, calls the script).
3. Add `.github/workflows/auto-merge.yml` (smoke + verdict wait + merge step).
4. Register the 2 secrets via API (`references/secret-registration.md`).
5. Validate end-to-end with one clean PR (expect auto-merge) and one
   PR with intentional 🔴/🟠 findings (expect verdict ≠ Approve + no merge).

## Pitfalls (read before building)

### 1. `pull_request` does NOT fire for same-repo PRs

Same-repo PRs trigger `push` on the target branch but NOT `pull_request`
(that's reserved for external forks). Use `pull_request_target`:

```yaml
on:
  pull_request_target:
    types: [opened, synchronize, reopened, ready_for_review]
```

### 2. Workflow trigger cache survives file edits

If edits to `on:` don't take effect: bump the `name:` field, add a
no-op comment + repush (forces new SHA), or — most reliably — rename
the workflow file (e.g. `merge-gate.yml` → `pr-merge-gate.yml`).

### 3. Step `id:` is REQUIRED to read outputs downstream

```yaml
- name: Wait for verdict
  id: wait          # ← without this, ${{ steps.wait.outputs.VERDICT }} is empty
  env:
    PR_NUMBER: ${{ steps.pr.outputs.number }}
  run: ...
```

Omitting `id:` makes `${{ steps.X.outputs.Y }}` silently return empty.

### 4. `GITHUB_TOKEN` cannot approve its own PRs, but CAN merge them

`POST /pulls/{n}/reviews` with `event=APPROVE` returns 422 ("GitHub
Actions is not permitted to approve pull requests"). Skip the approve;
call `PUT /pulls/{n}/merge` directly — admin tokens on the repo can
merge.

### 5. `DEEPSEEK_API_KEY` / `DEEPSEEK_BASE_URL` secret values

Two valid `BASE_URL` forms:
- `https://api.deepseek.com/v1` → script appends `/chat/completions`
- `https://api.deepseek.com` → script appends `/v1/chat/completions`

The script normalizes either at `call_deepseek()`. Model must be
`deepseek-v4-flash` (cheapest). Auth header is `Authorization: Bearer`.

**MiniMax → DeepSeek migration (2026-07-17)**: If a repo still has
the old `MINIMAX_API_KEY` / `MINIMAX_BASE_URL` secrets and
MiniMax-formatted workflows, convert them:
1. Rename secrets to `DEEPSEEK_API_KEY` / `DEEPSEEK_BASE_URL`
2. Update `review-bot.yml` and `review-bot-reusable.yml` env vars
3. Replace `scripts/review_pr.py` with the DeepSeek version
4. Change model from `MiniMax-M3` to `deepseek-v4-flash`
5. Change API header from `x-api-key` + `anthropic-version` to `Authorization: Bearer`
6. Change endpoint from `/v1/messages` to `/v1/chat/completions`

**⚠️ CRITICAL: After migration, register the new secrets via `gh secret set` —
the workflow references `secrets.DEEPSEEK_API_KEY` but the repo still only has
`MINIMAX_*`. This is easy to miss because the workflow shows no error until
it actually runs.** 실측: 2026-07-20, review-bot 3일간 Broken 상태였음.
```bash
# After updating YAML + script, also:
gh secret set DEEPSEEK_API_KEY -r mybotagent/REPO < ~/.hermes/.env.d/keys
gh secret set DEEPSEEK_BASE_URL -r mybotagent/REPO <<< "https://api.deepseek.com/v1"
```

### 6. `gh api -f` sends strings; `-F` sends typed values

```bash
# WRONG — squash=true arrives as the string "true"
gh api -X PUT ... -f commit_title="x" -f squash=true

# RIGHT — squash arrives as JSON boolean true
gh api -X PUT ... -F commit_title="x" -F squash=true
```

If you see 422 "true is not a boolean", switch `-f` → `-F`.

### 7. `gh pr comment` requires git context

If a step `cd`'d away from the checkout, `gh pr comment` fails with
`fatal: not a git repository`. Either `actions/checkout@v4` first, or
use the API directly:

```bash
curl -sS -X POST -H "Authorization: Bearer ${GH_TOKEN}" \
     -H "Content-Type: application/json" \
     "https://api.github.com/repos/${REPO}/issues/${N}/comments" \
     -d "$(printf '{"body": "%s"}' "$msg")"
```

### 8. (superseded 2026-07-07 — see v2 in Pitfall 11 + `references/auto-merge-v2-pitfalls.md`)

The original worst-of verdict polling was the **wrong** heuristic for
fix-then-merge PRs. After fixing a Changes Requested PR, the new
review writes `**Verdict:** Approve`, but worst-of over the FULL
timeline still picks the stale `Blocked` from the first round. v1's
fix-reviews never had a chance to clear.

**v2 verdict polling** (now in `templates/auto-merge.yml`):
1. Prefer comment whose body contains `<!-- sha: <HEAD_SHA> -->`
   (`review_pr.py` should write this marker — verify by reading the
   comment body of any existing review-bot output).
2. Fall back to the latest verdict line from ANY
   `github-actions[bot]` comment (`tail -1` over all of them).
3. Anything else → `<timeout>`.

The boundary case ("🟠 in v1 then Approve in v2 should silently
auto-merge") is now the user's call: a fix push is intentional, the
new verdict is what they want. The "stale Blocked masks the fix"
direction was the production-killing bug.

If you must keep worst-of semantics, scope it to comments with the
**same HEAD SHA** as the current PR head, not the whole timeline.

Also needed for a complete auto-merge hardener — see Pitfall 11
(concurrency group + head_sha live fetch).

### 9. Use bounded polling (6 min, not 12)

A 12-min polling loop with no timeout on the inner API call can hang
forever on rate-limit or stalled runners. Use 24 iterations × 15s =
**6 min max** with `timeout 30 curl …` on external calls.

### 10. Workflow name shown as file path

`GET /actions/workflows` sometimes lists a workflow by its file path
(e.g. `.github/workflows/merge-gate.yml`) instead of the `name:` field.
Usually fixable by renaming the file + repushing.

### 11. Race condition: multiple concurrent runs (실측 2026-07-07)

`pull_request_target` 트리거(`synchronize` 등)마다 workflow run이 새로 시작됨.
review-bot이 다회 verdict 코멘트를 박으면 (`verdict-analyzer` 의함이든
자가 재시도의 함정이든) 그때마다 새 trigger가 발동해 **auto-merge run이
N개 동시 시작**되고, 첫 run의 `wait` step이 끝나기 전에 후속 run이 같은 PR
comment를 polling 하느라 6분+ in_progress 후 timeout.

증상: PR #1에서 17:57 ~ 17:58 사이에 auto-merge run 3~4개 in_progress,
verdict=Approve 코멘트가 박혔는데도 모든 run이 timeout.

**Fix (두 가지 모두 권장)**:
```yaml
# auto-merge.yml 상단
concurrency:
  group: auto-merge-${{ github.event.pull_request.number }}
  cancel-in-progress: true
```
- 그 결과: 새 push마다 이전 run이 cancel되고 새 run 1개만 활성
- 부수효과: 같은 PR 동시 머지 race 완전 차단

또는 **버스트성 run을 manual merge로 fallback** (Pitfall 12).

### 12. Verdict가 ✅ Approve여도 run이 timeout이면 manual squash merge (실측 2026-07-07)

`PUT /pulls/{n}/merge` 직접 호출 (admin 권한 token 사용). review 봇
self-approve 불가능 (Pitfall 4)이지만 **merge**는 가능. 실측 작업:

```bash
GH_TOKEN=$(grep '^GITHUB_TOKEN' ~/.hermes/.env | cut -d= -f2- | tr -d '"')
# 1) in-progress auto-merge run 일괄 cancel
gh run list --repo OWN/REPO --workflow 'auto-merge' \
  --json databaseId,status --jq '.[] | select(.status=="in_progress") | .databaseId' \
  | while read rid; do gh run cancel $rid --repo OWN/REPO; done
# 2) PR state 검사: same-repo + mergeable=MERGEABLE
gh pr view $N --repo OWN/REPO --json mergeable,isCrossRepository
# 3) 직접 squash merge
curl -sX PUT -H "Authorization: token $GH_TOKEN" -H "Content-Type: application/json" \
  "https://api.github.com/repos/OWN/REPO/pulls/$N/merge" \
  -d '{"commit_title":"...","commit_message":"...","merge_method":"squash"}'
```

Pitfall 11 fix를 적용했다면 이 fallback은 안 쓰여도 됨. 단, **사용자가
"PR들 전부 확인해서 approve 아니면 close"라고 할 때 이미 race가 시작된
경우**는 fallback 필요.

### 13. PR 내용 직접 fix — clone 없이 GitHub Contents API (실측 2026-07-07)

verdict=Changes Requested / Blocked라도 fix 가능한 손상만 있으면 close
대신 fix commit push → review 재 trigger → squash merge. git clone 없이
API로 파일 단위로 수정 가능:

```bash
GH_TOKEN=$(grep '^GITHUB_TOKEN' ~/.hermes/.env | cut -d= -f2- | tr -d '"')
B64=$(base64 -w0 /tmp/fixed-file.md)
OLD_SHA=$(curl -sH "Authorization: token $GH_TOKEN" \
  "https://api.github.com/repos/OWN/REPO/contents/path/to/file.md?ref=BRANCH" \
  | grep -o '"sha": *"[^"]*"' | head -1 | cut -d'"' -f4)
curl -sX PUT -H "Authorization: token $GH_TOKEN" -H "Content-Type: application/json" \
  "https://api.github.com/repos/OWN/REPO/contents/path/to/file.md" \
  -d "{\"message\":\"fix(file): ...\",\"content\":\"$B64\",\"sha\":\"$OLD_SHA\",\"branch\":\"BRANCH\"}"
```

여러 파일 동시 fix 시 각 PUT이 별도 commit이 됨 (3 파일 → 3 commits).
중간에 push된 commit이 review-bot 재 trigger → verdict=Approve → squash.
자주 같이 쓰는 패턴:
- forward-reference 라인 삭제 (CHANGELOG.md line 9 류)
- retrigger 주석 (`<!-- retrigger ... -->`) 정리
- 404 placeholder → 정상 entry 교체
- "Apple blue/white" 같은 trademark 혼동 표현 → "Apple-style"

### 14. Verdict 분석으로 자가개선 (실측 2026-07-07)

`scripts/verdict_analyzer.py` (drop-in, read-only):
- mybotagent/* PR 코멘트의 `**Verdict:** X` + 🔴/🟠/🟡/⚪ 카운트
- 반복 지적 패턴 top-N keyword (예: workflow, secret, review)
- JSON dump → wiki logs/에 누적

주 1회 cron 예제: schedule `0 12 * * 0` (=매주 일 21:00 KST),
script `verdict_analyzer_weekly.sh`, deliver=origin. read-only라 안전.
자가개선 루프의 기초 자료로 활용 → `self-improvement-loop` skill 참조.

### 15. Linear GraphQL query 이름 정확히 사용 (실측 2026-07-07)

Linear API에서 issue 조회 시 흔히 쓰는 실수:
- ❌ `issueByIdentifier(identifier: "SHO-52")` — 이 필드 없음
- ✅ `issues(filter: { team: { id: { eq: "..." } } }, first: N)` + 클라이언트 필터

또는 identifier로 직접 조회하려면:
```graphql
query GetIssue($id: String!) {
  issue(id: $id) { id identifier state { name } }
}
```
그리고 UUID를 알아야 함. UUID 모르면 위 filter로 N개 가져온 뒤 클라이언트에서 identifier 매칭.

또는 모든 이슈 한 번에:
```graphql
query { issues(first: 100, orderBy: updatedAt) { nodes { identifier id title state { id name type } } } }
```

### 16. hermes cloud 디스크 ↔ github repo sync cycle (실측 2026-07-07)

`~/.hermes/<repo>/`는 hermes cloud 디스크 안의 git clone. github repo와 sync가 깨지면 drift 발생.

**Drift 감지** (자주 실행, 모든 our own repo 대상):
```bash
for repo in $(find ~/.hermes -maxdepth 3 -name ".git" -type d); do
  name=${repo%/.git}; name=${name##*/}
  uncommitted=$(git -C "$repo" status --porcelain | wc -l)
  if [ "$uncommitted" -gt 0 ]; then echo "  $name  uncommitted=$uncommitted"; fi
done
```

**Sync 패턴**:
```bash
cd /home/ubuntu/hermes-wiki-super
git pull --rebase 2>&1 | tail -3       # conflict 방지
git push origin main 2>&1 | tail -2
```

**hermes-agent fork 관리 (Pitfall 17과 연결)**:
- `~/.hermes/hermes-agent`의 origin이 **NousResearch** (외부 repo)면 위험
- 우리 own repo `mybotagent/hermes-agent`가 fork이므로 origin 변경:
  ```bash
  cd ~/.hermes/hermes-agent
  git remote set-url origin https://github.com/mybotagent/hermes-agent.git
  git fetch origin
  git reset --hard origin/main
  git branch -D fix/skills-external-dirs-cache-fingerprint  # 잔여 branch 정리
  ```

### 17. 외부 repo PR 즉시 close 패턴 (실측 2026-07-07)

우리 정책과 무관한 외부 repo PR은 close + fork branch 정리:
```bash
# 1. 외부 PR close
gh pr close 60279 --repo NousResearch/hermes-agent
# 또는 GraphQL PATCH (addComment 권한 부족 시)
gh api -X PATCH repos/NousResearch/hermes-agent/pulls/60279 -f state=closed

# 2. fork 잔여 branch 삭제
gh api -X DELETE repos/mybotagent/hermes-agent/git/refs/heads/BRANCH_NAME

# 3. cron 모니터링 제거 (외부 repo 모니터링 무의미)
# cron id '4b38af32e7b8' 같은 외부 repo URL cron → remove

# 4. hermes cloud 디스크의 branch 정리
cd ~/.hermes/hermes-agent
git reset --hard origin/main
git branch -D BRANCH_NAME
```

### 18. Linear issue backfill 패턴 (실측 2026-07-07)

audit round에서 발견/해결한 작업이 Linear에 누락되면 backfill:
1. **14건 issue 일괄 생성** (GraphQL `issueCreate`):
   ```python
   for title, desc in ISSUES:
       issueCreate(teamId=TEAM, title=title, description=desc)
   ```
2. **state ID 매핑** (`86cd9d73-2b97-49e9-8b16-95c1d08c29ad` = Done, `58b34e08-f1b1-48a0-bcc3-40a9579fd94c` = Todo, `cec5bc9e-3028-4f51-b3ad-1f60740a1812` = Backlog)
3. **완료된 건 일괄 Done** (`issueUpdate`):
   ```python
   for uuid in DONE_LIST:
       issueUpdate(id=uuid, stateId=DONE)
   ```
4. **drift 해결 후 SHO-62 (drift 추적 issue) Done**
5. **`kanban_linear_mapping.json`**에 `backfill_2026-07-07` 섹션 추가 (idempotent 추적)
6. **`kanban_linear_sync.py` v1.1** — unmapped done task 발견 시 자동 권장 action 추가

Pitfall은 아니지만 패턴 자체가 자주 씀. 위키 `infra/pr-review-policy.md` v2.0과 짝꿍.

### 19. external repo PR은 사용자 명시 OK 후에만 (실측 2026-07-07)

사용자 의도: "내 말은 우리 github내에서 말한거였는데?" — 외부 repo PR은 사용자 명시 OK 시에만.

**체크리스트 (PR 만들기 전)**:
1. 사용자가 "PR 해"라고 했는가? → OK
2. PR 대상이 our own repo인가? → OK
3. 외부 repo (NousResearch 등)면 → ❌ 사용자에게 "외부 repo PR OK?" 확인
4. 사용자가 "OK" 또는 "직접 해"라고 명시 → 진행
5. 명시 없으면 → ⛔ 외부 PR 만들지 말 것

**Self-check 질문** (PR 만들기 전 스스로에게):
> "이 PR은 사용자가 의도한 범위 안인가?"

예: 사용자 "Fix PR 하기"라고 했을 때:
- ✅ 우리 own repo의 bug → OK
- ⚠️ NousResearch/hermes-agent 같은 외부 repo → 명시 OK 필요
- ❌ "Fix PR"이 외부 repo 의도였으면 사용자 명시 OK 받은 후 진행

### 20. HEAD_SHA marker는 3개 파일 동시 수정 필요 (실측 2026-07-20)

auto-merge v2의 정밀 verdict 매칭을 위해서는 `<!-- sha: {HEAD_SHA} -->` 마커가
**3개 파일 모두에 일관되게 적용되어야 한다**. 하나라도 빠지면 SHA 마커가 작동 안 하고
fallback(최신 bot comment)으로만 동작한다:

| 파일 | 필요한 변경 |
|---|---|
| `scripts/review_pr.py` | `HEAD_SHA` env 읽기 → `post_comment()`에 `head_sha` 파라미터 전달 |
| `.github/workflows/review-bot.yml` | Resolve PR 단계에서 head_sha 추출 → script env에 `HEAD_SHA` 전달 |
| `.github/workflows/review-bot-reusable.yml` | review-bot.yml과 동일 |

**빠진 증상 2가지**:
- **review_pr.py만 수정**: workflow에서 HEAD_SHA를 env로 안 넘겨주면 script가 빈 문자열 받음 → 마커 생성 안 됨
- **review-bot.yml만 수정**: review_pr.py가 head_sha 파라미터를 받지 않으면 post_comment()가 마커 무시

**검증 방법**: PR의 review-bot comment body에 `<!-- sha: ... -->` 가 포함되었는지 확인:
```bash
gh pr view $N -R OWN/REPO --json comments --jq '.comments[] | select(.author.login=="github-actions[bot]") | .body' | grep -o '<!-- sha:' || echo "MISSING"
```

### 21. Workflow 파일 수정 PR push는 `workflow` scope token 필요 (실측 2026-07-20)

`.github/workflows/*.yml` 파일을 수정한 branch를 push할 때, 일반 `GITHUB_TOKEN`
(classic PAT with `repo` scope)만 있으면 **push가 reject**된다:

```
remote: refusing to allow a Personal Access Token to create or update
workflow `.github/workflows/review-bot.yml` without `workflow` scope
```

**해결**: `workflow` scope이 포함된 token 사용 (예: `GH_TOKEN_V2` 환경변수):
```bash
# 실측 패턴
git remote set-url origin "https://mybotagent:${GH_TOKEN_V2}@github.com/mybotagent/REPO.git"
git push origin BRANCH
```

또는 fine-grained token에 **Contents: Read and write** + **Workflows: Read and write**
권한을 부여한다. `gh secret set`으로 workflow file을 우회하거나, GitHub UI에서 직접
PR을 생성할 수도 있다 (workflow 파일 제외 push → UI에서 별도 commit으로 추가).

## Cross-references

- `references/deepseek-openai-compat.md` — 🆕 DeepSeek V4 Flash API: endpoint,
  headers, model, pricing, auth format. Use instead of deprecated
  `minimax-anthropic-compat.md`.
- `references/auto-merge-v2-pitfalls.md` — worst-of regression, why v2 picks newest-sha, "stuck auto-merge" triage flowchart
- `references/minimax-anthropic-compat.md` — ⚠️ **DEPRECATED 2026-07-17**. Kept for repos that haven't migrated yet. New deployments use DeepSeek.
- `references/github-actions-quirks.md` — each pitfall with reproduction.
- `references/secret-registration.md` — sealed-box secret PUT.
- `scripts/review_pr.py` — drop-in DeepSeek V4 Flash LLM call template.
- `scripts/verdict_analyzer.py` — read-only 주간 PR verdict 분석 (자가개선 기초)
- `templates/review-bot.yml` — drop-in workflow (DeepSeek V4 Flash version).
- `templates/review-bot-reusable.yml` — 🆕 reusable workflow for other repos.
- `templates/auto-merge.yml` — v2 (race-hardened 2026-07-07; replace any old v1 worst-of with this).

## User preference (carry across sessions)

When this user asks for GitHub PR automation, **do not propose
`anthropics/claude-code-action@v1`** — they have explicitly stated:

> "hermes는 claude 연결을 안할 계획이야 복잡해질거 같으니"

Default to the direct-LLM-API architecture above. Same answer for
`claude -p` in workflows (no Claude Code CLI on the runner).

## Operational policy (사용자 확정, 2026-07-07)

**Auto-merge 정책 (사용자 확정**): verdict=Approve면 squash merge, 그 외면
코멘트만 + 사용자 위임. 별도 confirm 안 물음 (PR 단위 자동 판단).

**PR fix vs close 정책 (사용자 확정, 2026-07-07)**: "PR들 전부 확인해서
approve 아니면 끝까지 approve 되거나 해결불가/방해/필요없으면 close" —

- verdict=Changes Requested 또는 Blocked라도 **fix 가능한 손상**(typo,
  forward-reference, copyright mismatch, README style) → 새 commit push →
  review 재 trigger → manual squash merge (Pitfall 12 fallback)
- **해결불가**(자동화 한계, 권한 부족) → close 이유 코멘트 + close
- **방해/충돌**(인증 문제, branch conflict) → close
- **불필요**(테스트용 smoke PR, retrigger artifact만) → close

**Risk-tier decision**: 봇이 같은 repo의 본인 PR에 push/squash merge 가능
(`GITHUB_TOKEN classic + repo scope`). Pitfall 12의 manual merge는
**사용자 의도 범위 내** — 추가 confirm 불필요.

## Trust-based 2-tier PR policy (사용자 확정, 2026-07-07 v2)

사용자 명시: *"PR이나 코드리뷰는 필요한 곳에서만 설정"*, *"중요한 내용
아니면 왠만하면 approve merge해도됨 삭제나 강제 푸시만 안하면됨"*.

| Tier | 대상 | Workflow | reviewer |
|:-----|:-----|:---------|:---------|
| **Tier 1 — Heavy** | 메인 서비스, 인프라, secret, 외부 repo, wiki 정책 페이지 | auto-merge + review-bot 둘 다 | review-bot verdict + 사용자 확인 |
| **Tier 2 — Light** | 문서 typo, 1~2 line fix, 주석, wiki raw/, README 다듬기 | **둘 다 OFF** (직접 squash merge) | 사용자 1회 확인 → squash merge |

### Sprint 분류 기준 (어느 tier인가?)
- 새 기능 추가 / API 변경 / 인프라 변경 / workflow/secret/.env 변경 → **Tier 1**
- 1~2 line fix / typo / 주석 / wiki raw/ 단순 추가 → **Tier 2**

### 절대 금지 (모든 tier 공통)
- ❌ **force push** — history 손상. `git push --force-with-lease` 사용 ❌
- ❌ **main/master 직접 push** — Tier 1/2 모두 PR 경유
- ❌ **의미 있는 코드 삭제 commit** — git history에서 지우기 ❌
- ❌ **secret/API 키 커밋** — `.env` / `config.yaml` 직접 편집 ❌
- ❌ **외부 repo force push** — upstream 권한 ❌

### hermes-pr-gate self-import 적용 범위 (2026-07-07)
**모든 repo에 일괄 self-import 안 함**. 현재 self-import 적용:
- `mybotagent/hermes-pr-gate` — 자기 자신만 (gate 정의 변경 = Tier 1)

다른 32개 own repos는 Tier 2 (auto-merge.yml + review-bot.yml 미설치).
Tier 2 repo에 잘못 self-import 되어 있으면 삭제:
- `hermes-wiki-super` (auto-merge.yml + review-bot.yml 삭제, 2026-07-07)
- `mybotagent.github.io` (auto-merge.yml + review-bot.yml 삭제, 2026-07-07)

### Force push / main push 절대 금지 — pre-commit 가드
PR 자동 머지 workflow에 다음 gate를 추가하면 2-tier 정책 자동 강제:
```yaml
- name: Block force push history
  run: |
    if git log --oneline origin/${{ github.event.pull_request.base.ref }}..${{ github.event.pull_request.head.sha }} | grep -qi 'force\|--force'; then
      echo "❌ Force push detected. Rejecting merge."
      exit 1
    fi
```

(자세한 적용 패턴은 `references/2-tier-policy-patterns.md` 참조)

## Cross-references 추가 (v1.1)

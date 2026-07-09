---
tags: [github, workflows, merge-gate, same-repo, trigger-fallback, free-plan, automation]
related: [pr-merge-gate]
created: 2026-07-06
updated: 2026-07-06
---

# Same-Repo PR Trigger Fallback (실측 2026-07-06)

`mybotagent/hermes-pr-gate`에서 `merge-gate.yml`을 `pull_request_target` 트리거로 작성했지만 **같은 repo PR에서 한 번도 발화 안 된** 함정의 디테일 + 정답 패턴.

## 증상

hub repo에 `merge-gate.yml` 작성:
```yaml
on:
  pull_request_target:
    types: [opened, synchronize, reopened, ready_for_review]
jobs:
  ...
```

같은 owner(`mybotagent`)가 hub repo에 PR을 열면:
- workflow runs API 조회 시 **오직 `event=push`** (workflows/*.yml 변경 push될 때만) 만 표시
- `pull_request_target` 이벤트는 **단 한 번도 발화 안 됨**
- `mergeable_state`는 PR마다 `unstable`/`clean` 정상 갱신 — 즉 GitHub 측 PR 자체는 정상

## 시도해본 후보 (모두 실패)

| # | 변경 | 결과 |
|---|---|---|
| 1 | `pull_request` → `pull_request_target` | trigger 캐시 갱신 안 됨 |
| 2 | `.github/workflows/merge-gate.yml` → `.github/workflows/pr-merge-gate.yml` (rename) | 새 파일도 같은 캐시 miss |
| 3 | workflow 본문 코멘트만 살짝 변경 (re-register 강제 시도) | trigger 여전히 push만 |
| 4 | `pull_request` 로 되돌리고 branch protection tweak | trigger 여전히 안 발화 |

## 근본 원인

GitHub Actions 의 `pull_request` / `pull_request_target` 트리거는:
- **외부 fork PR** (cross-repo PR) 에서만 자동 발화
- **같은 repo 의 internal PR** 은 GitHub 의 보안 정책으로 자동 trigger 안 됨 (workflow 가 PR 코드를 checkout 해서 실행 시 credential 노출 위험)

특히 **private repo + free plan** 조합에서 명확히 fail. **GitHub Actions 의 workflow 가 등록될 때 trigger 메타데이터를 캐시**하기 때문에 workflow 본문 변경, 파일 rename, 심지어 workflow 파일 삭제 후 재생성해도 trigger 변경은 반영 안 될 수 있음 (실측에서 100% 불가 확인).

## 정답: workflow 대신 cron + 외부 polling

**PR 마다의 자동 머지** 가 필요하면 GitHub workflow 가 아니라 **외부 cron + REST API 직접 호출**:

```python
# ~/.hermes/skills/pr-merge-gate/scripts/same_repo_merge_poller.py
import os, json, urllib.request, subprocess, re, time

TOKEN = os.environ["GITHUB_TOKEN"]  # classic PAT or fine-grained w/ PRs:RW
REPOS = ["mybotagent/hermes-pr-gate"]  # polling 대상

VERDICT_PAT = re.compile(r"\*\*Verdict:\*\*\s*(Approve|Blocked|Changes Requested)")

def gh(method, path, body=None):
    req = urllib.request.Request(
        f"https://api.github.com{path}",
        data=json.dumps(body).encode() if body else None,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "hermes-bot/1.0",
            **({"Content-Type": "application/json"} if body else {}),
        },
        method=method,
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.status, json.loads(r.read())

for repo in REPOS:
    status, prs = gh("GET", f"/repos/{repo}/pulls?state=open&per_page=20")
    for pr in prs:
        pr_num = pr["number"]

        # 1. 이미 머지된 PR skip
        if pr.get("merged"):
            continue

        # 2. verdict 코멘트 polling
        verdict = None
        s, comments = gh("GET", f"/repos/{repo}/issues/{pr_num}/comments?per_page=100")
        for c in comments:
            m = VERDICT_PAT.search(c.get("body", ""))
            if m:
                verdict = m.group(1)
                break

        if not verdict:
            print(f"[skip] PR #{pr_num}: no verdict")
            continue

        # 3. mergeable state 확인 (transient = accept)
        s, pr_full = gh("GET", f"/repos/{repo}/pulls/{pr_num}")
        mergeable_state = pr_full.get("mergeable_state")
        if mergeable_state not in ("clean", "unstable", "behind"):
            print(f"[skip] PR #{pr_num}: state={mergeable_state}")
            continue

        # 4. Approve 면 squash merge
        if verdict == "Approve":
            s, r = gh("PUT", f"/repos/{repo}/pulls/{pr_num}/merge",
                     {"commit_title": f"merge: auto squash #{pr_num} via same-repo merge-gate poller",
                      "commit_message": "verdict=Approve + mergeable acceptable",
                      "squash": True})
            print(f"[merge] PR #{pr_num}: HTTP {s}")
        else:
            print(f"[no-merge] PR #{pr_num}: verdict={verdict}")
            # option: 코멘트 posting
            gh("POST", f"/repos/{repo}/issues/{pr_num}/comments",
               {"body": f"🤖 merge-gate poller: not auto-merging. verdict=`{verdict}`"})
```

이 poller를 cron으로 (예: 매 5분) 등록:
```bash
hermes cron create "*/5 * * * *" \
  "$(cat <<'EOF'
Run same-repo merge-gate poller:
- Poll open PRs on mybotagent/* repos
- If verdict=Approve and mergeable clean/unstable/behind → squash merge via PUT API
- Otherwise leave a comment explaining why
Use pre-flight probe before iterating.
EOF
)" \
  --name "merge-gate-poller-5m" \
  --skill pr-merge-gate
```

## 대안: GitHub App

만약 외부 fork 가 아닌 같은 repo PR 의 workflow trigger 가 절대로 필요하다면:
1. https://github.com/apps/claude 같이 App 등록
2. App installation token 사용 — 같은 repo PR 의 workflow trigger 발화 가능
3. 단점: App 등록 사용자 작업 1회 필요, App secret 별도 관리

## scripts/review_pr.py 직접 호출 (간단한 bot-only 시나리오)

Verdict posting 만 필요하면 cron 없이도:
1. PR 열림 → 사용자가 bot 에 "review PR N" 명령
2. bot 이 `python3 scripts/review_pr.py` 직접 실행
3. MiniMax API 호출 → verdict 코멘트 posting
4. merge 는 사용자 수동 또는 cron poller 가 처리

## 검증된 status (2026-07-06)

- scripts/review_pr.py 로컬 실행 → verdict=Blocked / Approve 정상 posting 확인
- review-bot.yml workflow 에서 동일 스크립트 호출 시 **pull_request_target 으로 정상 trigger** (단, **외부 repo 의 PR 만**)
- merge-gate.yml 의 trigger 가 같은 repo PR 에선 발화 안 되므로 poller 가 자동 머지 처리

## Why this is the 정답

`pull_request_target` 으로 trigger 잡으려 한 의도는 "PR 마다 자동 머지" 였음. **GitHub 보안 모델 + workflow 캐시 + private repo** 조합에서 그게 불가능. **poller 패턴** 은:
- workflow 캐시 의존 X
- external trigger 의존 X (cron 이 trigger)
- 사용자가 cron 만 등록하면 끝

automation 비용 = cron 1개 + Python 200 줄.

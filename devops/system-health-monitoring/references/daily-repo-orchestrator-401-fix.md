# daily-repo-orchestrator 401 Unauthorized Fix

**File:** `~/.hermes/scripts/daily_repo_orchestrator_mirror.sh`  
**Job ID:** `a79d072b2447`  
**Symptom:** HTTP 401 on `GET /user/repos` — "Bad credentials"

## 원인

```python
# daily_repo_orchestrator.py line ~111
gh("/user/repos?per_page=30&sort=pushed&affiliation=owner")
```

GitHub PAT (`.env`의 `GITHUB_TOKEN`)이 만료되었거나无效。

```bash
# 증상 확인
source ~/.hermes/.env
curl -s -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user
# → {"message": "Bad credentials", ...}
```

## Fix 절차

1. GitHub → Settings → Developer settings → Personal access tokens (Fine-grained)
2. 새 토큰 생성 — 필요 scope: `repo` (모든 repo 읽기/쓰기)
3. 새 토큰으로 `.env` 업데이트:

```bash
sed -i 's/GITHUB_TOKEN=.*/GITHUB_TOKEN=ghp_NEW_TOKEN_HERE/' ~/.hermes/.env
```

4. 검증:

```bash
source ~/.hermes/.env
curl -s -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('login', d))"
```

5. 수동 트리거: `hermes cron run a79d072b2447`

## ⚠ 401 ≠ "GitHub 업데이트가 안 된다"

토큰 만료를 발견했다고 곧바로 "저장소가 구버전이라 문제"라고 진단하면 틀린다.
인증 소스가 여러 개라 **어느 것이 실제 push에 쓰이는지** 먼저 확인한다.

```bash
# credential store에 유효한 토큰이 있는지 (값은 절대 출력하지 말 것 — 접두/길이만)
git credential fill <<< "protocol=https
host=github.com" | sed 's/^password=.*/password=<present>/'

# 실제 push 경로 생존 여부 — 이것이 되면 저장소는 정상
cd <repo> && git ls-remote origin HEAD
```

**판정 기준**:
| `.env` 토큰 | `git ls-remote` | 결론 |
|---|---|---|
| 401 | 성공 | 저장소·push 정상. 실패한 것은 그 토큰으로 API를 직접 호출하는 **cron 잡**뿐 |
| 401 | 실패 | credential store까지 정리 필요 |

즉 "배포/표시 계층(예: Vercel 사이트)이 안 갱신된다"는 complaint가 별도로 있다면
**token 문제가 아니라 배포 단계를 먼저 의심**한다.

## 재발 방지

`hermes-config-sync` cron (job `91059d1e3d31`, KST 22:30)이 `.env` 변경을 감지하면 GitHub token 유효성 검증 단계 추가 권장.

## 관련 로그

```
~/.hermes/scripts/logs/orchestrator-YYYYMMDD-HHMMSS.log
```

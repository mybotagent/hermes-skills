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

## 재발 방지

`hermes-config-sync` cron (job `91059d1e3d31`, KST 22:30)이 `.env` 변경을 감지하면 GitHub token 유효성 검증 단계 추가 권장.

## 관련 로그

```
~/.hermes/scripts/logs/orchestrator-YYYYMMDD-HHMMSS.log
```

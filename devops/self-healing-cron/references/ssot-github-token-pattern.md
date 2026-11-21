# SSOT GitHub Token Pattern (2026-09-16)

## Rule
`.env` is the **single source of truth** for all GitHub PATs. Every script reads from `.env`. No hardcoding, no separate token files.

## Token Priority (SSOT order)
```
GH_TOKEN  →  GITHUB_TOKEN  (classic PAT, ghp_ prefix)
```
- `GH_TOKEN_V2` (fine-grained PAT, `github_pat_` prefix) is **not active** — expired 2026-09-16. Comment out with `# ` (hash + space).
- `GH_TOKEN` = primary. `GITHUB_TOKEN` = fallback only.

## Python: `get_env_var` cascade
```python
GITHUB_TOKEN = (
    get_env_var("GH_TOKEN")
    or get_env_var("GITHUB_TOKEN")
)
```
**Never** put an expired token first — Python `or` short-circuits on any truthy value, including expired PATs.

## Shell: cascade in assignment
```bash
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
```
Or 2-line cascade:
```bash
TOKEN=$(grep ^GH_TOKEN= "${HERMES_HOME}/.env" 2>/dev/null | cut -d= -f2- | tr -d '"' | tr -d "'" || true)
if [ -z "${TOKEN:-}" ]; then
  TOKEN=$(grep ^GITHUB_TOKEN= "${HERMES_HOME}/.env" 2>/dev/null | cut -d= -f2- | tr -d '"' || true)
fi
```

## Commenting out expired tokens in `.env`
**Must use `# ` (hash + space)**. Without space, `re.match(rf'^{name}=(.*)$', line.strip())` strips `#` and matches commented lines:
```
#GH_TOKEN_V2=...   ← .strip() removes '#', regex matches
# GH_TOKEN_V2=...  ← regex does NOT match
```

## Files using this pattern (updated 2026-09-16)
| File | Pattern |
|------|---------|
| `skills/daily-repo-orchestrator/scripts/daily_repo_orchestrator.py` | `get_env_var` cascade |
| `skills/pr-merge-gate/scripts/verdict_analyzer.py` | `get_env_var` cascade |
| `skills/devops/github-pr-review-pipeline/scripts/verdict_analyzer.py` | `get_env_var` cascade |
| `scripts/dev_harness_daily_review.sh` | bash `${GH_TOKEN:-${GITHUB_TOKEN:-}}` |
| `scripts/hermes_config_sync.sh` | grep cascade with fallback |
| `scripts/trigger_backlog_swipper.py` | re.search cascade with fallback |
| `scripts/pr_review_monitor.py` | loop + `#`-skip + cascade |
| `scripts/paper_tracker_daily.sh` | grep -oP cascade with fallback |

## Token validity (2026-11-21 갱신)
| Token | Prefix | Status |
|-------|--------|--------|
| `GH_TOKEN` | `ghp_HhaB...` | ✅ 200 OK, login=mybotagent, scope=`repo` |
| `GITHUB_TOKEN` | `ghp_HhaB...` | ✅ 200 OK (fallback, 동일 값) |
| `GH_TOKEN_V2` | `github_pat_11BWOAV5A...` | ❌ 만료 — `# ` (hash+space)로 주석 처리 유지 |

**gh CLI 인증**: `gh auth login --with-token`는 `read:org` scope가 없어 실패. 대신 `~/.bashrc`에서 `.env`를 읽어 `GH_TOKEN`/`GITHUB_TOKEN`을 export → `gh api` 정상 동작.

**Token 갱신 SOP** (순서 중요):
1. **유효성 선검증** — 쓰기 전에 `curl -sI -H "Authorization: token <NEW>" https://api.github.com/user` 로 200 + scope 확인. 응답 없으면 여기서 중단.
2. `.env`의 `GH_TOKEN=` **그리고** `GITHUB_TOKEN=` 둘 다 새 값으로 치환 (fallback을 옛값으로 남기면 만료 토큰으로 되돌아간다).
3. `~/.git-credentials`의 `ghp_[A-Za-z0-9]+` regex 치환.
4. 검증 3종 (전부 실측): API HTTP 200 / `GIT_TERMINAL_PROMPT=0 git ls-remote https://github.com/mybotagent/<repo>.git HEAD` / `gh api user`.

## gh CLI는 `gh auth login` 없이 env로 인증된다
`gh auth login --with-token`은 classic PAT에 `read:org` scope가 없으면 `error validating token: missing required scope 'read:org'` 로 실패한다 — 토큰 불량이 아니라 gh CLI 요구 scope 문제. 해결은 토큰 범위 확대가 아니라 **`~/.bashrc`에서 `.env`를 읽어 `GH_TOKEN`/`GITHUB_TOKEN`을 export** 하는 것 (`gh`는 env 토큰이 있으면 login 없이 동작).

### ⚠️ shell rc 블록의 두 함정
- **heredoc(`cat >> ~/.bashrc <<'EOF'`)으로 넣지 말 것** — `$(...)`/`${...}` 포함 블록이 리터럴로 보존되지 않아 깨진 export가 남을 수 있다. `write_file`/파일 편집 도구로 쓰고 넣은 뒤 `bash -n ~/.bashrc`로 문법 확인.
- **검증은 `bash -lc`가 아니라 `bash -ic`** — `.bashrc`는 interactive 전용이라 non-interactive login shell에서는 블록이 아예 실행되지 않는다. `bash -lc`로 테스트하면 "설정이 안 먹었다"는 잘못된 결론이 난다.

### 보고 시 포함할 것
갱신한 저장소 3곳 + 실측 검증 결과 + **토큰이 채팅에 평문으로 노출됐다는 경고**(revoke 후 재발급 권고).

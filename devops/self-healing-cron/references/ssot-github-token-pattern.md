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

## Token validity (2026-09-16)
| Token | Prefix | Status |
|-------|--------|--------|
| `GH_TOKEN` | `ghp_Bj1l...` | ✅ 200 OK, login=mybotagent |
| `GH_TOKEN_V2` | `github_pat_11BWOAV5A...` | ❌ 401 Bad credentials |
| `GITHUB_TOKEN` | `ghp_IHHQ...` | ❌ 401 Bad credentials |

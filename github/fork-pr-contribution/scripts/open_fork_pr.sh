#!/usr/bin/env bash
# open_fork_pr.sh — PR open from fork branch → upstream repo (cross-repo head)
# Generalized from dev_harness_create_pr.sh (실측 2026-08-11).
# Usage: open_fork_pr.sh <repo-dir> <upstream-owner> <branch> <pr-title>
#   repo-dir: local clone path (used to derive bot-user + repo name from origin)
#   upstream-owner: original owner (e.g. sh-ai-x)
#   branch: the fork branch to propose (head becomes <bot-user>:<branch>)
#   pr-title: PR title (conventional commit message)
# PR body comes from stdin (heredoc). Token loaded from ~/.hermes/.env — never from args.
set -uo pipefail

REPO_DIR="${1:?usage: open_fork_pr.sh <repo-dir> <upstream-owner> <branch> <pr-title>}"
UPSTREAM_OWNER="${2:?usage: open_fork_pr.sh <repo-dir> <upstream-owner> <branch> <pr-title>}"
BRANCH="${3:?usage: open_fork_pr.sh <repo-dir> <upstream-owner> <branch> <pr-title>}"
TITLE="${4:?usage: open_fork_pr.sh <repo-dir> <upstream-owner> <branch> <pr-title>}"
ENV_FILE="$HOME/.hermes/.env"

if [ -f "$ENV_FILE" ]; then set -a; source "$ENV_FILE"; set +a; fi
TOKEN="${GITHUB_TOKEN:-}"
[ -z "$TOKEN" ] && { echo "❌ GITHUB_TOKEN 없음"; exit 1; }

# derive bot-user + repo name from origin URL (https://<user>:token@github.com/<user>/<repo>.git)
ORIGIN_URL=$(git -C "$REPO_DIR" remote get-url origin)
REPO_NAME=$(basename "$ORIGIN_URL" .git)
BOT_USER=$(echo "$ORIGIN_URL" | sed -E 's#https://[^@]*@github.com/([^/]+)/.*#\1#')
BODY="$(cat)"

python3 - "$TOKEN" "$UPSTREAM_OWNER" "$REPO_NAME" "$BOT_USER" "$BRANCH" "$TITLE" "$BODY" <<'PYEOF'
import json, sys, urllib.request

token, owner, repo, bot, branch, title, body = sys.argv[1:8]
payload = {
    "title": title,
    "head": f"{bot}:{branch}",
    "base": "main",
    "body": body,
}
req = urllib.request.Request(
    f"https://api.github.com/repos/{owner}/{repo}/pulls",
    data=json.dumps(payload).encode(),
    headers={"Authorization": f"token {token}", "Accept": "application/vnd.github+json",
             "Content-Type": "application/json"},
    method="POST",
)
try:
    with urllib.request.urlopen(req, timeout=20) as r:
        d = json.loads(r.read())
        print(f"✅ PR 생성: #{d.get('number')} {d.get('html_url')}")
        print(f"   제목: {d.get('title')}")
except urllib.error.HTTPError as e:
    body = e.read().decode()[:500]
    print(f"❌ PR 생성 실패 ({e.code}): {body}")
    sys.exit(1)
PYEOF

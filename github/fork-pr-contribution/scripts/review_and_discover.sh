#!/usr/bin/env bash
# review_and_discover.sh — fork sync (ff-only) + candidate checklist a–f (read-only)
# Generalized from dev_harness_daily_review.sh (실측 2026-08-11).
# Usage: review_and_discover.sh <repo-dir> <upstream-owner>
#   repo-dir: local clone path (origin=fork, upstream=original)
#   upstream-owner: original owner for the open-PR dedupe probe (e.g. sh-ai-x)
# Output: sync result + candidate list on stdout — agent picks 1, then implements.
set -uo pipefail

REPO_DIR="${1:?usage: review_and_discover.sh <repo-dir> <upstream-owner>}"
UPSTREAM_OWNER="${2:?usage: review_and_discover.sh <repo-dir> <upstream-owner>}"
ENV_FILE="$HOME/.hermes/.env"
LOG_FILE="$HOME/.hermes/cron/output/fork-pr-review.log"
mkdir -p "$(dirname "$LOG_FILE")"
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"; }

if [ -f "$ENV_FILE" ]; then set -a; source "$ENV_FILE"; set +a; fi
TOKEN="${GITHUB_TOKEN:-}"

echo "=== ① fork 동기화 (ff-only) ==="
cd "$REPO_DIR" || { log "REPO_DIR 없음"; echo "❌ $REPO_DIR 없음"; exit 1; }
git fetch upstream main 2>&1 | tail -1
git checkout main 2>&1 | tail -1
git merge --ff-only upstream/main 2>&1 | tail -2 || { log "ff-only merge 실패"; echo "⚠️ fast-forward merge 실패 (수동 확인 필요)"; }
git push origin main 2>&1 | tail -1

echo ""
echo "=== ② 최근 커밋 ==="
git log --oneline -8 origin/main

echo ""
echo "=== ③ 개선 후보 탐색 (read-only) ==="

# a. skills/ 있는데 docs/skills/ 없는 스킬 (docs-heavy 레포용)
echo "--- [a] skills/ ↔ docs/skills/ 불일치 ---"
for s in skills/*/; do
  name=$(basename "$s")
  [ "$name" = "_acp" ] && continue
  if [ ! -f "docs/skills/${name}.md" ]; then
    echo "  docs 누락: $name (skills/ 있음, docs/skills/${name}.md 없음)"
  fi
done

# b. 영어 docs 있는데 .ko.md 없는 스킬
echo "--- [b] .ko.md 누락 ---"
for f in docs/skills/*.md; do
  base=$(basename "$f" .md)
  case "$base" in *.ko) continue;; esac
  if [ ! -f "docs/skills/${base}.ko.md" ]; then
    echo "  ko 누락: $base (docs/skills/${base}.ko.md 없음)"
  fi
done

# c. README.md 링크 끊김
echo "--- [c] README 링크 끊김 ---"
grep -oE 'docs/skills/[a-z0-9-]+\.md' README.md 2>/dev/null | sort -u | while read -r link; do
  [ -f "$link" ] || echo "  broken link: $link"
done

# d. TODO/FIXME (간단 해결 가능한 것만)
echo "--- [d] TODO/FIXME (코드) ---"
grep -rn "TODO\|FIXME" --include="*.py" --include="*.sh" --include="*.js" --include="*.ts" . 2>/dev/null \
  | grep -v ".git/" | grep -v "logs/" | grep -v "node_modules" | head -8

# e. CHANGELOG 최신 엔트리
echo "--- [e] CHANGELOG 최신 엔트리 ---"
head -20 CHANGELOG.md 2>/dev/null | grep -E "^## |^# " | head -3

# f. 열린 PR (중복 방지 — dedupe guard)
echo "--- [f] 열린 PR (${UPSTREAM_OWNER}) ---"
if [ -n "$TOKEN" ]; then
  curl -s -H "Authorization: token $TOKEN" \
    "https://api.github.com/repos/${UPSTREAM_OWNER}/$(basename "$REPO_DIR")/pulls?state=open&per_page=10" \
    | python3 -c "
import json,sys
try:
    d=json.load(sys.stdin)
    if isinstance(d,list):
        if not d: print('  (없음)')
        for p in d: print(f\"  #{p['number']} {p['title'][:60]}\")
    else: print('  ERR:', d.get('message','?')[:80])
except Exception as e: print('  parse err:', e)"
else
  echo "  (GITHUB_TOKEN 없음)"
fi

log "review done"
echo ""
echo "=== done ==="

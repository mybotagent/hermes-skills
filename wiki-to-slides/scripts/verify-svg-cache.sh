#!/usr/bin/env bash
# verify-svg-cache.sh — Verify all SVG assets in a deck are served correctly
# Usage: ./verify-svg-cache.sh <org> <repo> <path-to-deck>
# Example: ./verify-svg-cache.sh mybotagent hermes-architecture-deck decks/hermes-architecture

set -e

ORG="${1:-mybotagent}"
REPO="${2:-hermes-architecture-deck}"
DECK_PATH="${3:-decks/hermes-architecture}"
BASE="https://${ORG}.github.io/${REPO}"

echo "=== Checking SVGs at ${BASE}/${DECK_PATH}/assets/img/ ==="
echo ""

# Find all SVGs in local deck
LOCAL_SVGS=$(find "${DECK_PATH}/assets/img" -name "*.svg" 2>/dev/null | sort)
if [ -z "$LOCAL_SVGS" ]; then
  echo "No SVGs found locally at ${DECK_PATH}/assets/img/"
  exit 1
fi

# Audit each SVG for viewBox overflow / overlap (Pitfall: position arithmetic).
# Runs BEFORE the git/http checks so layout problems are caught at write-time,
# not after a push. Uses the companion script in scripts/audit-svg-bounds.py.
echo "--- viewBox bounds audit (catches overflow + overlap) ---"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "${SCRIPT_DIR}/audit-svg-bounds.py" $LOCAL_SVGS
echo ""

# Verify each is in git
echo "--- git ls-files check (must show all files below) ---"
cd "$(dirname "$0")/.." 2>/dev/null || cd .
git ls-files "$DECK_PATH/assets/img/" | sort
echo ""

# Verify each is served by GitHub Pages
echo "--- HTTP fetch check ---"
echo "$LOCAL_SVGS" | while read -r svg; do
  url="${BASE}/${svg}"
  http_code=$(curl -s -o /dev/null -w "%{http_code}" "$url")
  size=$(curl -s -o /dev/null -w "%{size_download}" "$url")
  if [ "$http_code" = "200" ]; then
    printf "  \033[32m✓\033[0m %-40s %s %sB\n" "$svg" "$http_code" "$size"
  else
    printf "  \033[31m✗\033[0m %-40s %s\n" "$svg" "$http_code"
  fi
done

echo ""
echo "--- Cache state of all-slides.md ---"
md_url="${BASE}/${DECK_PATH}/slides/all-slides.md"
curl -sI "$md_url" | grep -iE "last-mod|cache|content-type" | head -3

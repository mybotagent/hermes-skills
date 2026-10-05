#!/bin/bash
# ~/.hermes/scripts/wiki_reindex.sh
# Wraps: submodule HEAD sync + Neo4j incremental reindex.
#
# Use case: after pushing a new page to hermes-wiki (or any wiki submodule)
# from a standalone clone, the Neo4j indexer does NOT see the new commit
# because the submodule's local HEAD is still pointing at the pre-push commit.
# This script does the submodule reset first, then runs the incremental indexer.
#
# Usage:
#   ~/.hermes/scripts/wiki_reindex.sh              # default: incremental reindex
#   ~/.hermes/scripts/wiki_reindex.sh --all        # full reindex (--force) across all repos
#   ~/.hermes/scripts/wiki_reindex.sh --status     # just show current index state, no sync
#
# Cron:
#   0 20 * * * /home/ubuntu/.hermes/scripts/wiki_reindex.sh >> /home/ubuntu/.hermes/logs/wiki-reindex.log 2>&1
#
# Created 2026-07-02 after submodule HEAD stale bug surfaced during 4-Layer validate.
set -e
SUBMODULE_DIR=~/hermes-wiki-super/wiki/hermes-wiki
METAGRAPH=~/hermes-wiki-super/.metagraph

if [ "$1" = "--status" ]; then
  cd ~/hermes-wiki-super
  python3 "$METAGRAPH/index_incremental.py" --status
  exit 0
fi

if [ "$1" = "--all" ]; then
  cd ~/hermes-wiki-super
  python3 "$METAGRAPH/index_incremental.py" --force
  exit 0
fi

# Default: sync submodule + incremental reindex (most common case)
if [ -d "$SUBMODULE_DIR" ]; then
  cd "$SUBMODULE_DIR"
  git fetch origin 2>&1 | tail -2 || true
  git reset --hard origin/main 2>&1 | tail -2
fi

cd ~/hermes-wiki-super
python3 "$METAGRAPH/index_incremental.py"

echo "DONE wiki reindex complete"

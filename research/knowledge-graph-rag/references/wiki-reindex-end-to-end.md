# Wiki Reindex End-to-End Pattern

**Discovered 2026-07-02 during Hermes Memory Pipeline (4-Layer) validation.**

## Why this exists

After pushing a new page to `hermes-wiki` (or any wiki repo in `hermes-wiki-super`),
`query.py` does NOT see the new page. Running `index_incremental.py` reports
`All 14 repos unchanged. Nothing to index.` This is a silent failure — the script
exits 0, no error, but the page is invisible to all future searches.

## Root cause (one paragraph)

The Hermes box has TWO working trees for `hermes-wiki`:

1. **Standalone clone** at `~/hermes-wiki/` — what `wiki-save` and `memory_sync.sh` push from
2. **Submodule working tree** at `~/hermes-wiki-super/wiki/hermes-wiki/` — what the indexer reads

Both point to the same GitHub remote, but they have different local `HEAD`s.
`wiki-save` updates the remote and the standalone clone's HEAD, but the submodule
working tree's HEAD is only updated when someone does
`cd ~/hermes-wiki-super && git submodule update --remote hermes-wiki` (or equivalent).

The indexer tracks per-repo HEAD in `~/hermes-wiki-super/.metagraph/.index_state.json`.
On each run it compares that stored HEAD against the submodule's CURRENT local HEAD.
If they match, the indexer thinks nothing changed. Since the submodule's local HEAD
is still pointing at the pre-push commit, the indexer never re-indexes.

## Working pattern (verified 2026-07-02)

```bash
#!/bin/bash
# ~/.hermes/scripts/wiki_reindex.sh
# Wraps: submodule HEAD sync + Neo4j incremental reindex.
# Use this any time you want freshly-pushed wiki content to be searchable.
set -e
SUBMODULE_DIR=~/hermes-wiki-super/wiki/hermes-wiki
METAGRAPH=~/hermes-wiki-super/.metagraph

# 1. Sync the submodule working tree to remote
cd "$SUBMODULE_DIR"
git fetch origin 2>&1 | tail -2 || true
git reset --hard origin/main 2>&1 | tail -2

# 2. Run incremental indexer (only re-indexes changed repos)
cd ~/hermes-wiki-super
python3 "$METAGRAPH/index_incremental.py"
```

**Runtime**: ~12-15 seconds for a single-repo change (hermes-wiki), ~30-45s for full reindex across all 14 repos.

**When to use**:
- After any `wiki-save` or `memory_sync.sh` push, if you need the new content searchable immediately
- Scheduled via cron (registered: `0 20 * * *` daily 21:00 KST, `>> logs/wiki-reindex.log 2>&1`)
- Manual: `~/.hermes/scripts/wiki_reindex.sh`

## Verification

After running, verify the new page is searchable via two independent paths:

**Path 1: Direct Neo4j query** (catches indexer pipeline failures)
```python
from neo4j import GraphDatabase
driver = GraphDatabase.driver('bolt://localhost:7687')
with driver.session() as session:
    r = session.run('MATCH (p:Page) WHERE p.repo="hermes-wiki" AND p.path CONTAINS "architecture" RETURN p.path')
    for x in r: print(x['p.path'])
```

**Path 2: End-user query** (catches embedding/similarity issues)
```bash
python3 ~/.hermes/skills/research/wiki-knowledge-search/scripts/query.py "memory pipeline 4 layer" --top-k 3
```

Expected: new page appears as result #1 with high similarity score (0.7+).

## Failure modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| `All 14 repos unchanged` despite fresh push | Submodule HEAD stale (root cause above) | `cd ~/hermes-wiki-super/wiki/hermes-wiki && git fetch && git reset --hard origin/main` |
| New page visible in Neo4j but NOT in `query.py` top results | Embedding model or vector index mismatch | Check `embed.py` model version matches what was used at index time; re-run `indexer.py --force` |
| Neo4j query works but `index_incremental.py` doesn't run (Python error) | venv missing — needs `~/.venv-neo4j/bin/python3` | `python3 -m venv ~/.venv-neo4j && ~/.venv-neo4j/bin/pip install neo4j fastembed` |
| New page in same-named subdirectory (e.g. `architecture/memory-snapshots/`) not indexed | Some indexer.py versions don't recurse into nested subdirs | Run `indexer.py --force` (full reindex) instead of incremental |

## Two `indexer.py` scripts (CONFUSION HAZARD)

There are TWO scripts both named `indexer.py` in this environment. They are different.

| Path | Capabilities | Use for |
|------|-------------|---------|
| `~/.hermes/skills/research/wiki-knowledge-search/scripts/indexer.py` | Single `--repo` only, no `--force` | **Not for production** — leave alone |
| `~/hermes-wiki-super/.metagraph/indexer.py` | Multiple `--repo`, has `--force`, called by `index_incremental.py` | **Production reindex** |

Use the second one (always via `index_incremental.py` for incremental, or directly
with `--force` for full reindex).

## Integration with `memory_sync.sh`

`memory_sync.sh` calls `wiki_reindex.sh` automatically at the end of every push:

```bash
# ~/.hermes/scripts/memory_sync.sh (excerpt)
echo "Step 4: wiki_reindex.sh (submodule sync + Neo4j reindex)..."
"$HOME/.hermes/scripts/wiki_reindex.sh" 2>&1 | tail -5 || echo "  (wiki_reindex.sh failed, ignorable)"
```

This means: calling `memory_sync.sh "TITLE" "BODY"` does the full
memory → wiki → Neo4j pipeline in one shot, ~15-20 seconds total.

## Cron registration (production)

```bash
# crontab -l
0 20 * * * /home/ubuntu/.hermes/scripts/wiki_reindex.sh >> /home/ubuntu/.hermes/logs/wiki-reindex.log 2>&1
```

Schedule: 21:00 KST (= 20:00 UTC+8 = `0 20`) — aligns with existing
`wiki-auto-refresh` cron so the wiki-save/refresh cycle and reindex stay in sync.

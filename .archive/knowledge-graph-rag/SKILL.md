---
name: knowledge-graph-rag
description: "Build and operate a Neo4j-based GraphRAG knowledge search system on top of Karpathy-style markdown wikis. Covers auto-discovery, vector embeddings, universal query routing, incremental indexing, and operations."
version: 1.0.0
author: Hermes Agent
platforms: [linux]
prerequisites:
  commands: [java, curl, systemctl]
  env_vars: [NEO4J_URI]
metadata:
  hermes:
    tags: [GraphRAG, Neo4j, Knowledge Graph, Vector Search, Wiki]
    related: [llm-wiki, wiki-architecture, wiki-save]
---

# Knowledge Graph RAG — Neo4j-based Wiki Search

Build a vector + graph search system on top of Karpathy-style markdown wiki repos. Zero hardcoded assumptions about repos, keywords, or domains.

## Architecture

```
.gitmodules → discover.py (auto-detect repos + namespace)
     ↓
indexer.py → Neo4j (nodes=pages, edges=wikilinks, vectors=embeddings)
     ↓
query.py → universal_search(vector × graph, zero keywords)
     ↓
synthesize.py → natural language response
```

## Key Components

### 1. Auto-Discovery (`discover.py`)
Reads `.gitmodules` to find ALL submodules (initialized and uninitialized), auto-generates compact 2-char namespaces, and detects new/removed repos.

```python
# Usage
from discover import discover_repos, get_namespace_map, init_new_repos

repos = discover_repos()           # {name: {path, namespace, initialized, status}}
ns_map = get_namespace_map()       # {repo_name: "hw", "tp", "cc", ...}
init_new_repos()                   # git submodule update --init for new ones

# CLI
python3 discover.py                # list all
python3 discover.py --check        # exit 1 if new/removed repos
python3 discover.py --init-new     # init uninitialized submodules
python3 discover.py --json         # machine-readable
```

**Namespace rules**: 
- Known mappings preserved for backward compat (hermes-wiki=hw, trade-pipeline=tp, ...)
- New repos: initials of meaningful words, max 2 chars
- Collision → append digit: hw → hw2 → hw3

### 2. Indexer (`indexer.py`)
- Reads wiki markdown files, extracts frontmatter + [[wikilinks]]
- Generates bge-m3 embeddings (384d) via `embed.py`
- MERGEs into Neo4j: `(:Page {id, repo, path, title, tags, summary, embedding})`
- Creates `[:LINKS {type: "wikilink"|"related"}]` relationships
- Two-pass: dry-run for cross-repo registry → real write

```bash
python3 indexer.py                     # index all repos
python3 indexer.py --repo hermes-wiki  # single repo
python3 indexer.py --dry-run           # preview only
```

### 3. Universal Query Router (`query.py`)
**Zero hardcoded keywords, zero tag assumptions, zero domain bias.**

```python
def universal_search(query):
    # Step 1: Vector search (works on any language/domain)
    vec_results = vector_search(query)
    
    # Step 2: Graph expand top results (find connected pages)
    for r in vec_results[:3]:
        r["neighbors"] = get_neighbors(r["id"])
    
    # Step 3: Fuse with connectivity-matched results
    conn_results = get_connected_pages(query)  # title/summary CONTAINS
    return fused_ranked_results
```

```bash
python3 skill/query.py "클로드 코드 활용법"     # any language
python3 skill/query.py "cron jobs" --top-k 10   # any domain
```

### 4. Incremental Indexer (`index_incremental.py`)
- Tracks git HEAD per repo in `.index_state.json`
- Only re-indexes repos whose HEAD changed
- Auto-detects new repos via `discover.py`

```bash
python3 index_incremental.py            # incremental
python3 index_incremental.py --force    # full reindex
python3 index_incremental.py --status   # show state
```

### 5. Operations

**Neo4j systemd service**: `/etc/systemd/system/neo4j.service`
- Boot auto-start: `sudo systemctl enable neo4j.service`
- Status: `sudo systemctl status neo4j.service`
- Memory: 256MB heap + 256MB page cache (1.9GB RAM server)

**Health check**: `check_health.py`
- Verifies: process → port(7687) → database(nodes/edges) → vector index → memory
- Auto-repair: `--repair` flag runs `systemctl start` on failure
- Cron: silent when healthy, alert on failure

## Pitfalls

1. **Systemd vs manual Neo4j**: Never run `neo4j start` manually if systemd is enabled. Kill orphan processes with `sudo pkill -f org.neo4j` then `sudo systemctl restart neo4j.service`.
2. **Submodule .git is a file**: For submodules, `.git` is a file (not directory) containing gitdir pointer. Use `.exists()` not `.is_dir()`.
3. **Cypher SHOW INDEXES**: In Neo4j 5.26, `CALL db.indexes()` is deprecated. Use `SHOW INDEXES WHERE name = 'page_emb'` instead.
7. **bge-m3 first load slow**: First call to `embed_batch()` loads model from HuggingFace (~2min, ~500MB download).
8. **wiki-knowledge-search v0.2.0 `indexer.py --repo` is not incremental** — reads submodule HEAD snapshot, not git push deltas. After `git push origin main`, Neo4j is NOT updated automatically.
   - Solution: `cd ~/hermes-wiki-super/wiki/hermes-wiki && git fetch origin && git pull --ff-only origin main` (refuse on diverged) → then `python3 ~/hermes-wiki-super/.metagraph/index_incremental.py`
   - Wrap in shell script: `~/.hermes/scripts/wiki_reindex.sh` (persisted: `mybotagent/hermes-pipeline-scripts`)
   - Cron: `0 20 * * *` for daily auto-sync
   - Discovered 2026-07-02 (architecture/hermes-memory-pipeline.md pushed but query returned no match)
9. **Submodule reference update** — `hermes-wiki` push from its own working tree updates origin, but `hermes-wiki-super` submodule ref is stale. For super repo consumers, manual sync: `cd hermes-wiki-super/wiki/hermes-wiki && git reset --hard origin/main` (or use wiki_reindex.sh wrapper).
10. **fastembed multilingual MiniLM warning** — `mean pooling instead of CLS embedding` (warning only, behavior OK). Pin fastembed 0.5.1 or use `add_custom_model` to preserve CLS behavior.
5. **Vector index dimension**: Must match embedding model output (384 for bge-m3, 768 for all-MiniLM-L12-v2, etc.)
6. **Memory budget**: Neo4j + Java + page cache = ~900MB on 1.9GB server. Don't exceed 512MB heap.
7. **Cross-repo wikilinks**: `[[page]]` syntax only matches within same repo. Cross-repo resolution requires namespace prefix or post-processing.
8. **🔴 Submodule HEAD stale = silent indexing failure (CRITICAL — 2026-07-02)**: when a `hermes-wiki` page is pushed from a **standalone clone** (`~/hermes-wiki/`) rather than from the submodule working tree (`~/hermes-wiki-super/wiki/hermes-wiki/`), the indexer's stored HEAD in `.metagraph/.index_state.json` does NOT see the new commit. `index_incremental.py` reports `All 14 repos unchanged. Nothing to index.` despite a fresh push. Always `git fetch origin && git reset --hard origin/main` in the submodule working tree **before** running `index_incremental.py`. Use the `wiki_reindex.sh` wrapper (see "End-to-End Sync Pattern" below) — it does this automatically.
9. **🔴 Two `indexer.py` scripts exist (CONFUSION HAZARD)**: `~/.hermes/skills/research/wiki-knowledge-search/scripts/indexer.py` (single `--repo` only, no `--force`, runs but may not pick up new pages in nested subdirs) vs `~/hermes-wiki-super/.metagraph/indexer.py` (accepts multiple `--repo`, has `--force`, called by `index_incremental.py` — this is the production one). Always use the second via `index_incremental.py` for production reindex.

## End-to-End Wiki → Neo4j Sync Pattern (verified 2026-07-02)

The Hermes Memory Pipeline (4-Layer) needs `wiki-save` push → Neo4j query visibility. The working flow:

```
memory_sync.sh                  wiki_reindex.sh
  (Layer 0 → Layer 1)             (Layer 1 → Layer 2)
       │                              │
       │ 1. raw + page 동시 저장         │ 1. cd submodule
       │ 2. git commit + push           │ 2. git fetch + reset --hard origin/main
       │ (hermes-wiki origin)            │ 3. cd back to super
       │                              │ 4. python3 .metagraph/index_incremental.py
       │                              │ 5. Neo4j auto-merge (12-15s)
       │                              │
       └──── memory_sync.sh 끝에 wiki_reindex.sh 자동 호출 ────┘
```

**Reference wrapper**: `~/.hermes/scripts/wiki_reindex.sh` (~990 bytes) — wraps submodule reset + incremental reindex in one command. Cron-registered: `0 20 * * *` (every 21:00 KST = `0 20` UTC+8, aligns with `wiki-auto-refresh`).

**Verification recipe** (after any sync):
```bash
# 1. Check Neo4j has the new page
python3 -c "
from neo4j import GraphDatabase
driver = GraphDatabase.driver('bolt://localhost:7687')
with driver.session() as session:
    r = session.run('MATCH (p:Page) WHERE p.repo=\"hermes-wiki\" AND p.path CONTAINS \"architecture\" RETURN p.path')
    for x in r: print(x['p.path'])
"

# 2. Check query.py surfaces it as top result
python3 ~/.hermes/skills/research/wiki-knowledge-search/scripts/query.py "memory pipeline 4 layer" --top-k 3
```

If step 1 misses pages but step 2 returns them: indexer wrote to Neo4j but state file is stale (cosmetic; query still works). If step 1 shows them but step 2 doesn't: embedding similarity issue (raise top-k, check embedding model match). If both miss: submodule HEAD reset not applied — re-run `wiki_reindex.sh` from the top.

## Files Created in `.metagraph/`

| File | Purpose |
|------|---------|
| `discover.py` | Auto-discovery from .gitmodules |
| `indexer.py` | Full wiki → Neo4j indexer |
| `index_incremental.py` | Git HEAD-based incremental indexer |
| `embed.py` | bge-m3 embedding generator (384d) |
| `create_schema.py` | Neo4j schema + vector index init |
| `link_cross_repo.py` | Cross-repo wikilink resolver |
| `check_health.py` | Health check + auto-repair |
| `skill/query.py` | Universal query router (zero keywords) |
| `skill/synthesize.py` | Result → natural language |
| `.index_state.json` | Per-repo HEAD tracking state |

## Support Files (this skill ships with)

| Path | Purpose |
|------|---------|
| `references/wiki-reindex-end-to-end.md` | Full write-up of the wiki-push → query-visible flow, including the submodule HEAD stale gotcha, two-`indexer.py` confusion, verification recipe, failure modes |
| `templates/wiki_reindex.sh` | Copy-paste wrapper that does submodule reset + incremental reindex in one call (cron-registered at `0 20 * * *`) |

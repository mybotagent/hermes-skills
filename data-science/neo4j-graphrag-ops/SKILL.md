---
name: neo4j-graphrag-ops
description: Build and operate a Neo4j-based GraphRAG knowledge graph on low-RAM servers (1.9GB) — embedding, indexing, query routing, systemd, health monitoring.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux]
prerequisites:
  commands: [java, neo4j, systemctl]
metadata:
  hermes:
    tags: [graphrag, neo4j, knowledge-graph, vector-search, embedding, infrastructure]
    related_skills: [wiki-architecture, system-health-monitoring, self-healing-cron]
---

# Neo4j GraphRAG Operations

Set up and operate a Neo4j Community knowledge graph with vector search for wiki/knowledge-base content. Optimized for low-RAM servers (~1.9GB RAM, 2 cores).

## Architecture

```
Wiki Repos (N repos via submodules)
        │ git diff HEAD
        ▼
Indexer (full or incremental)
        │ MERGE (create/update)
        ▼
┌──────────────────────────────────────┐
│ Neo4j Community 5.26.x               │
│ ┌──────────┐ ┌───────────────┐      │
│ │  :Page   │ │ :Page-[LINKS] │      │
│ │  nodes   │ │   →:Page     │      │
│ │  (vec)   │ │ relationships │      │
│ └──────────┘ └───────────────┘      │
│ Vector Index: page_emb (384d cosine) │
│ Bolt: localhost:7687                 │
│ systemd: enabled (boot auto-start)   │
└──────────────────────────────────────┘
        │ query
        ▼
Query Router (auto-detect mode)
  semantic ──→ vector similarity search
  structural → graph traversal + tags
  hybrid    → fused + deduplicated
        │
        ▼
Synthesize → natural language response
```

## Recommended Setup (1.9GB RAM)

### Neo4j Config
```bash
# Heap sizing — critical for low-RAM
echo "dbms.memory.heap.initial_size=256m" >> /usr/local/neo4j/conf/neo4j.conf
echo "dbms.memory.heap.max_size=512m"     >> /usr/local/neo4j/conf/neo4j.conf
echo "dbms.memory.pagecache.size=256m"    >> /usr/local/neo4j/conf/neo4j.conf
echo "dbms.security.auth_enabled=false"   >> /usr/local/neo4j/conf/neo4j.conf  # local only
```

### Memory Budget
| Component | Usage |
|-----------|-------|
| Neo4j Heap | ~512MB |
| Page Cache | ~256MB |
| JVM overhead | ~100MB |
| Embedding model (bge-m3) | ~500MB peak |
| **Total** | ~1.4GB (swap-safe) |

## systemd Service

```bash
# /etc/systemd/system/neo4j.service
[Unit]
Description=Neo4j Graph Database (Community, Local KB)
After=network.target

[Service]
Type=forking
ExecStart=/usr/local/neo4j/bin/neo4j start
ExecStop=/usr/local/neo4j/bin/neo4j stop
ExecReload=/usr/local/neo4j/bin/neo4j restart
User=ubuntu
Group=ubuntu
PIDFile=/usr/local/neo4j/run/neo4j.pid
Restart=on-failure
RestartSec=10
LimitNOFILE=40000
TimeoutStartSec=120

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable neo4j.service  # boot auto-start
sudo systemctl start neo4j.service    # immediate start
```

## Smart Query Router (Rule-Based)

Auto-detect query mode from natural language — NO LLM call needed:

```python
def detect_mode(query: str) -> str:
    q = query.lower()
    if any(w in q for w in ["연결", "관계", "관련", "링크", "연관"]):
        return "structural"   # graph traversal
    if any(w in q for w in ["뭐", "무엇", "방법", "설명", "알려줘"]):
        return "semantic"     # vector similarity
    return "hybrid"           # fused both
```

Three query modes:
1. **semantic** — vector similarity search via `db.index.vector.queryNodes()`
2. **structural** — graph traversal with tag filters, returns most-connected pages
3. **hybrid** — fuse vector + graph results, deduplicate, interleave

## Scripts

### indexer.py — Full Index
Scans all repos, extracts frontmatter + wikilinks, generates embeddings, MERGEs into Neo4j.
```bash
source ~/.venv-neo4j/bin/activate
python3 indexer.py                    # all repos
python3 indexer.py --repo hermes-wiki # single repo
python3 indexer.py --dry-run           # dry run
```

### index_incremental.py — Incremental Index
Only re-indexes repos whose git HEAD changed since last run.
```bash
python3 index_incremental.py           # incremental
python3 index_incremental.py --force   # full reindex
python3 index_incremental.py --status  # show state
```

State stored in `.index_state.json` (per-repo HEAD SHA + indexed timestamp).

### check_health.py — Health Check
Verifies: process → port → database → vector index → memory.
```bash
python3 check_health.py --verbose   # human-readable
python3 check_health.py --json      # machine-readable
python3 check_health.py --repair    # auto-fix (systemctl start)
```

### query.py — Query Router (Hermes Skill)
```bash
python3 skill/query.py "PER 분석 방법"           # auto hybrid
python3 skill/query.py --mode semantic "밸류에이션"
python3 skill/query.py --mode structural "cron jobs 연결"
```

## Cross-Repo Architecture

### Namespace Registry
Each repo gets a 2-letter namespace prefix for page IDs:
```
hw:  hermes-wiki         tp:  trade-pipeline
he:  harness-engineering cc:  claude-code
hl:  hermes-logs         hq:  wiki-quant
cx:  codex               am:  ai-marketing
hp:  hermes-prompts      aj:  ai-job-analysis
hs:  slash-commands
```

Page ID format: `{ns}:{relative-path-with-colons}` (e.g. `hw:infra:cron-jobs`)

### Wikilink Resolution
Cross-repo wikilinks resolved in two-pass indexing:
1. First pass (dry run): collect all page IDs from all repos
2. Second pass (real write): resolve `[[target]]` links against global registry

## Cron Jobs

| Job | Schedule (KST) | Mode | Purpose |
|-----|---------------|------|---------|
| neo4j-health-check | 08:00 daily | no_agent | Silent when healthy, alert on failure |
| neo4j-incremental-index | 03:00 daily | agent | Report changed repos + results |

Health check cron uses **no_agent mode** — LLM not invoked. Script exits 0 (silent) when healthy, exits 1 with details on failure.

## Best Practices

1. **Heap sizing first** — On low-RAM servers, default Neo4j heap (1GB+) causes OOM. Always set heap.initial_size=256m, heap.max_size=512m, pagecache=256m.
2. **Two-pass indexing** — Cross-repo wikilinks need global page registry. Always dry-run first to collect IDs, then real write.
3. **Embedding dimension matters** — 384d (bge-m3) fits in vector index better than 768d+ models on low-RAM. bge-m3 also supports Korean.
4. **Query Router bypasses LLM** — Rule-based mode detection costs 0 tokens, ~1ms latency. Reserve LLM for result synthesis only.
5. **Health check should be silent when healthy** — Use no_agent cron with exit 0/1. Only alert on failure.
6. **Incremental index over full reindex** — git HEAD diff is O(1) per repo. Full reindex takes 5-10x longer.

## Pitfalls

### 1. Manual vs systemd process conflict
Multiple Neo4j processes (manual start + systemd) fight over database file locks.
**Fix:** Kill manual processes first: `sudo /usr/local/neo4j/bin/neo4j stop && sudo pkill -f "org.neo4j"`, then `sudo systemctl start neo4j.service`.

### 2. SHOW INDEXES syntax varies by version
Neo4j 5.x uses `SHOW INDEXES WHERE name = 'page_emb'` (no quotes around name in some versions). Test your query before deploying health check.

### 3. Low-RAM embedding model loading
bge-m3 loads ~500MB on first inference. If combined with Neo4j (~600MB), total exceeds 1GB. **Load embedding model BEFORE starting Neo4j** or time the cron to avoid simultaneous memory peaks.

### 4. Submodule discovery
Submodules may be nested under `wiki/` directory in the super repo. Don't assume all repos are at root level.
```python
# Check both root and wiki/ subdirectory for submodules
search_dirs = [WIKI_SUPER]
wiki_dir = WIKI_SUPER / "wiki"
if wiki_dir.exists():
    search_dirs.append(wiki_dir)
```

### 5. .git can be a file (submodule link)
Submodule checkouts have `.git` as a FILE, not a directory. Check with `.exists()`, not `.is_dir()`.

### 6. State file must be committed
`.index_state.json` tracks per-repo HEAD. If it's not committed to git, a fresh clone loses all state → full reindex on first incremental run. Commit it after baseline creation.

## Verification Checklist

- [ ] Neo4j process active: `systemctl is-active neo4j.service`
- [ ] Bolt port listening: `ss -tlnp | grep 7687`
- [ ] Database queryable: `MATCH (n) RETURN count(n)` returns page count
- [ ] Vector index exists: `SHOW INDEXES WHERE name = 'page_emb'`
- [ ] Memory within limits: < 1GB (check with `check_health.py`)
- [ ] Incremental indexer reports 0 changed repos after baseline
- [ ] Query Router returns correct mode for known query patterns
- [ ] systemd auto-start tested: `sudo systemctl restart neo4j.service` recovers cleanly
- [ ] Cron jobs registered and enabled
- [ ] State file committed to git (`.index_state.json`)

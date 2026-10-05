---
name: local-graphrag-kb
description: "Build a local Neo4j GraphRAG knowledge base from Karpathy-style Markdown wiki repos — vector search, incremental indexing, cross-repo links, systemd service, health check crons. Phase 6: zero-keyword universal search, auto-discovery, paper-standard IR evaluation."
version: 1.2.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [neo4j, graphrag, knowledge-graph, vector-search, wiki, embedding, evaluation, universal-search]
    related_skills: [wiki-architecture, llm-wiki, wiki-save, hermes-agent-skill-authoring]
---

# Local GraphRAG Knowledge Base (Neo4j)

## Overview

Take a collection of Karpathy-style LLM wiki repos (Markdown with frontmatter + `[[wikilinks]]`) and turn them into a queryable Neo4j knowledge graph with vector search — all locally, zero cloud cost.

**Why this exists:**
- Hermes wiki repos have 1000+ pages across multiple repos
- Browsing them linearly is slow; grep is basic
- Neo4j + vector embeddings enable semantic search + graph traversal in one query
- Runs on a 1.9GB RAM server (no Docker, no cloud databases)

## Architecture

```
Wiki Repos (13 repos, 220+ pages)
    │ git HEAD tracking (incremental)
    ▼
indexer.py / index_incremental.py
    │ Neo4j MERGE
    ▼
Neo4j Community 5.26.0
  ┌──────────────────┐
  │ (:Page {id,      │
  │   title, summary,│
  │   embedding[384]})│
  │                  │
  │ [:LINKS {type}]  │
  └──────┬───────────┘
         │ Bolt (local:7687)
         ▼
Universal Query Router → pure vector + graph (zero keywords)
    │
    ▼
Synthesizer → 한글 자연어 응답
```

## Requirements

- Linux server (tested: Ubuntu 22.04)
- RAM: ≥1.9GB (Neo4j heap 512MB + page cache 256MB ~900MB total)
- Java 17+ (openjdk-17-jre-headless)
- Python 3.10+ venv
- No Docker required

## Setup Steps

### 1. Install Neo4j Community

```bash
# Java
sudo apt install -y openjdk-17-jre-headless

# Neo4j Community 5.26.0
wget -O ~/neo4j-community-5.26.0-unix.tar.gz \
  "https://dist.neo4j.org/neo4j-community-5.26.0-unix.tar.gz"
sudo tar xf ~/neo4j-community-5.26.0-unix.tar.gz -C /usr/local
sudo mv /usr/local/neo4j-community-5.26.0 /usr/local/neo4j
sudo chown -R ubuntu:ubuntu /usr/local/neo4j

# Low-memory config (1.9GB RAM server)
cat >> /usr/local/neo4j/conf/neo4j.conf << 'EOF'
dbms.memory.heap.initial_size=256m
dbms.memory.heap.max_size=512m
dbms.memory.pagecache.size=256m
dbms.security.auth_enabled=false
EOF
```

### 2. Set up Python venv

```bash
python3 -m venv ~/.venv-neo4j
source ~/.venv-neo4j/bin/activate
pip install neo4j sentence-transformers numpy
```

### 3. Create systemd service

```ini
# /etc/systemd/system/neo4j.service
[Unit]
Description=Neo4j Graph Database (Community, Local KB)
After=network.target

[Service]
Type=forking
ExecStart=/usr/local/neo4j/bin/neo4j start
ExecStop=/usr/local/neo4j/bin/neo4j stop
User=ubuntu
Group=ubuntu
Restart=on-failure
RestartSec=10
LimitNOFILE=40000
TimeoutStartSec=120

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable neo4j.service
sudo systemctl start neo4j.service
```

**Pitfall — stale process lock on first transition from manual to systemd.** If Neo4j was manually started before systemd was set up, stop it first: `sudo /usr/local/neo4j/bin/neo4j stop && sudo pkill -f "org.neo4j"` before systemctl start. Otherwise the old pid's file locks prevent the systemd process from starting.

### 4. Schema + Vector Index

```python
# create_schema.py
from neo4j import GraphDatabase
driver = GraphDatabase.driver("bolt://localhost:7687")
with driver.session() as sess:
    # Create vector index (384d, cosine)
    sess.run("CREATE VECTOR INDEX page_emb IF NOT EXISTS "
             "FOR (n:Page) ON (n.embedding) "
             "OPTIONS {indexConfig: {`vector.dimensions`: 384, "
             "`vector.similarity_function`: 'cosine'}}")
driver.close()
```

### 5. Embedding Model

Use BAAI/bge-m3 (384d) — open source, multilingual (한국어 포함), lightweight:

```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("BAAI/bge-m3")
def embed_batch(texts):
    return [emb.tolist() for emb in model.encode(texts)]
```

**Why bge-m3 not DeepSeek:** DeepSeek embedding API does not exist. bge-m3 is the best free alternative with Korean support and fits in server memory.

### 6. Indexer Design

#### Full Indexer (`indexer.py`)
- Discovers repos from two locations: root and `wiki/` subdirectory (submodule pattern)
- Scans `.md` files, skips `.git/`, hidden dirs, `logs/`, `raw/`
- Parses frontmatter (`---`) for: title, tags, related, updated, confidence
- Extracts `[[wikilinks]]` from body text
- Generates embeddings for each page's title + summary
- MERGEs into Neo4j (upsert, not duplicate)

#### Incremental Indexer (`index_incremental.py`)
- Tracks per-repo git HEAD in `.index_state.json`
- Only runs full indexer on repos where HEAD changed
- Supports `--force` (full reindex), `--status` (show state), `--dry-run`
- First run indexes all repos; subsequent runs only changed ones

**Repo discovery pitfall:** Submodules live under `wiki/` directory (not root). The auto-discovery is delegated to `discover.py` (Phase 6) which parses `.gitmodules` directly.

### 7. Cross-Repo Links

```python
# link_cross_repo.py
# For each [[wikilink]] that doesn't match within its own repo,
# try matching against ALL page IDs across ALL repos
# This connects: "hw:cron-jobs" ↔ "tp:docs:deployment" etc.
```

Namespace convention: `{repo_abbreviation}:{path_with_colons}`.
E.g. `hw:infra:neo4j-local` for hermes-wiki's infra/neo4j-local.md.

### 8. Health Check

```python
# check_health.py — checks 4 things:
# 1. systemctl is-active neo4j.service
# 2. ss -tlnp | grep 7687 (Bolt port)
# 3. MATCH (n) RETURN count(n), MATCH ()-[r]->() RETURN count(r)
# 4. SHOW INDEXES WHERE name = 'page_emb'
# Exit 0 if healthy, 1 if unhealthy
# --verbose for human-readable, --json for machine, --repair for auto-fix
```

**Health check cron:** no_agent=True, silent when healthy (exit 0 = no output). Only alerts on failure.

### 9. Cron Jobs

| Job | Schedule (KST) | Type | Description |
|-----|---------------|------|-------------|
| Health check | 08:00 daily | no_agent | Silent when healthy, alert on failure |
| Incremental index | 03:00 daily | agent | Discover new → init → index → report |

Register via cronjob tool:
```bash
# Health check (no_agent)
cronjob action=create name="neo4j-health-check" \
  schedule="0 7 * * *" script="neo4j_health.sh" no_agent=true deliver=local

# Incremental index (agent runs discover + init + index)
cronjob action=create name="neo4j-incremental-index" \
  schedule="0 2 * * *" prompt="Run discover --check, then init-new, then index_incremental..." \
  enabled_toolsets=["terminal","file"]
```

---

# Phase 6: Universal Knowledge Graph (v0.4)

**Problem Phase 5 left behind:** the query router had hardcoded Korean keywords and tag categories (`valuation`, `infra`, `analysis`, `trading`, `wiki`). New repos, new topics, or new languages broke the system — or required constant keyword maintenance.

**Solution:** zero-keyword, zero-tag universal search + auto-discovery from `.gitmodules`.

## 10. Auto-Discovery (discover.py)

Replace hardcoded NAMESPACES + manual registration with `.gitmodules` parser at runtime.

```python
def parse_gitmodules():
    cfg = configparser.ConfigParser()
    cfg.read(".gitmodules")
    repos = {}
    for section in cfg.sections():
        if section.startswith("submodule "):
            raw_name = section.split('"')[1]      # 'submodule "wiki/ai-agent-wiki"'
            name = os.path.basename(raw_name)     # → 'ai-agent-wiki'
            repos[name] = {
                "path": raw_name,
                "url": cfg[section].get("url", ""),
            }
    return repos

def auto_namespace(repo_name, existing):
    """Known mappings preserved, then auto from word initials."""
    known = {
        "hermes-wiki": "hw", "trade-pipeline": "tp",
        "hermes-wiki-claude-code": "cc", "hermes-wiki-codex": "cx",
        "harness-engineering-wiki": "he", "hermes-logs": "hl",
        "hermes-wiki-quant": "hq", "ai-job-analysis": "aj",
        "ai-marketing-wiki": "am", "hermes-prompts": "hp",
        "hermes-slash-commands": "hs", "hermes-wiki-schedule": "hsd",
        "subagents-library": "sl",
    }
    if repo_name in known: return known[repo_name]
    # Auto: first letter of each word, max 2 chars
    words = re.split(r'[-_\s]+', repo_name
                     .replace("hermes-wiki-", "")
                     .replace("hermes-", ""))
    return "".join(w[0] for w in words[:2])[:2]
```

**Discover result:** 13 repos detected, all namespaces backward-compatible. 2 uninitialized submodules flagged as `new` for auto-init via `discover.py --init-new`.

## 11. Universal Query Router (zero keyword, zero tag)

The old query router had 42 hardcoded items (17 Korean mode-detection keywords, 25 category keywords, 13 namespace mappings). Phase 6 removed all of them.

**Strategy:** vector search always works (language-agnostic), graph traversal always finds structure (no tags needed), keyword fallback only for connectivity ranking — and even that doesn't use domain-specific tags.

```python
def universal_search(query, k=5):
    # Step 1: vector search (semantic, no assumptions)
    vec_results = vector_search(query, k)
    # Step 2: graph connectivity (no tag filter)
    conn_results = get_connected_pages(query, k)
    # Step 3: fuse + deduplicate
    return fused[:k]

def get_connected_pages(query, k):
    """Find pages mentioning query in title/summary, ranked by connectivity.
    NO hardcoded tag categories. NO domain assumptions."""
    return sess.run("""
        MATCH (p:Page)
        OPTIONAL MATCH (p)-[r:LINKS]-(neighbor:Page)
        WITH p, count(DISTINCT neighbor) AS connections
        WHERE connections > 0
          AND (toLower(p.title) CONTAINS $q
               OR toLower(p.summary) CONTAINS $q)
        RETURN ... ORDER BY connections DESC
    """, q=query.lower(), k=k)
```

**What this enables:**
- New repo added → no code change → immediately searchable
- New language / new topic → no keyword update → works via embedding semantics
- Cross-language (EN-only terms like "a2a", "CoT", "MCP") → works automatically

## 12. Evaluation: Paper-Standard IR Metrics

**Do not** evaluate search systems with just `Hit@3` or a 1-5 relevance heuristic. Use standard IR metrics from the information retrieval literature:

| Metric | Formula | What it measures |
|--------|---------|------------------|
| **MRR** (Mean Reciprocal Rank) | mean(1/rank_of_first_relevant) | How quickly the user finds something useful |
| **MAP@k** (Mean Average Precision) | mean(precision_at_each_relevant_position) | Quality of the entire ranking |
| **nDCG@k** (Normalized DCG) | DCG/IDCG, with graded relevance (0/1/2/3) | Position-aware grading |
| **P@k, R@k, F1@k** | standard precision/recall/F1 | Standard retrieval quality |

**Graded relevance (not binary):**
- 3 = highly relevant (perfect match)
- 2 = partially relevant (related concept)
- 1 = marginally relevant (mentions but not core)
- 0 = not relevant (default)

**Implementation:** see `scripts/ir_evaluation.py` — runnable script with full ground truth harness.

## 13. Honest Comparison Reporting — A Critical Lesson

When comparing two search systems (old keyword vs new universal) on a small query set, the result may be **tied or near-tied on accuracy** (e.g., 9/10 queries returned the same Top-1). This is normal and not a failure of the new system.

The real differentiators that show up beyond the accuracy table:

| Dimension | Old (keyword) | New (universal) |
|-----------|---------------|-----------------|
| Hardcoded items to maintain | 42 (keywords + tags + namespaces) | **0** |
| New repo addition | 3 places to edit code (NAMESPACES, categories, structural_search) | **0 — just `git submodule add`** |
| New topic not in keyword map | Falls back to "most connected" (irrelevant) | Works via embedding semantics |
| Cross-language (EN-only terms like "a2a", "CoT") | May fail if not in EN keyword list | Works automatically |
| Latency | 145ms avg (3-mode detection + tag filter) | **63ms avg (single vector + neighbor)** |

**Reporting rule:** always include operational/scalability/maintenance dimensions alongside accuracy, even if accuracy is the headline. A system that ties on accuracy but requires 42 hardcoded items to maintain is NOT equivalent to one that requires zero.

## 14. Cron Pipeline Updated

```bash
# Incremental index cron — runs discover → init → index in sequence:
# 1. python3 .metagraph/discover.py --check
# 2. if exit 1 (new repos): python3 .metagraph/discover.py --init-new
# 3. python3 .metagraph/index_incremental.py
```

This handles the full lifecycle: detect new submodule → auto-init → auto-index → report. No human intervention needed.

## 15. Capacity Planning & Disk Budget

When the user asks "how many more wikis can I add?" or "is the disk OK?", measure real costs and report honestly.

**Empirical measurements (1.9GB RAM, 12 wikis, 223 pages):**
- 1 wiki ≈ 0.92 MB (.md + .git) + 0.24 MB (Neo4j) = **1.2 MB total**
- 1 node ≈ 13.8 KB Neo4j DB + 1.5 KB vector (bge-m3, 384 float32)
- 1 page ≈ 0.05 MB (sparse) to 0.5 MB (with images)
- Neo4j transactions backup: ~258MB (compressible)

**Quick formula (free disk N GB):**
```python
n_wiki = (N * 1024) / 1.2  # 15GB → ~13,000 normal wikis
```

**Honest ceiling (the one the user actually needs):** disc is not the limit. RAM (1.9GB) is. Safe sweet spot is 100–500 wikis (5k–15k pages). Beyond that → RAM upgrade.

**Disk cleanup safety table (always check before deleting):**

| Path | Size | Safe? | Notes |
|------|------|-------|-------|
| `/tmp/pip-unpack-*` | 1–2GB | 🟢 Safe | pip install done |
| `/tmp/neo4j-community.tar.gz` | 150MB | 🟢 Post-install | one-time |
| `~/.cache/pip/http-v2/*.body` | ~2GB | 🟡 Caution | venv rebuild needs |
| `~/.cache/uv/` | 1.1GB | 🟢 If not used | **always check** |
| `~/.cache/camoufox/` | 1.4GB | 🟢 If browser skill unused | check first |
| `~/.cache/huggingface/` | 142MB | ❌ NEVER | bge-m3 in use |

**Pitfall — answer "how many more wikis" with the real ceiling, not the math ceiling.** The user does not need "13,000 wikis" — they need "100–500 are safe, beyond that you need more RAM." Frame the answer around operational limits, not theoretical disk space.

## Phase 6 Verification Checklist

- [ ] `discover.py` lists all 13+ submodules with correct namespaces
- [ ] `discover.py --check` returns 0 when no changes, 1 when new repos present
- [ ] `query.py "<any question>"` works without any keyword updates
- [ ] Adding new submodule (`git submodule add ...`) auto-detected on next cron
- [ ] IR metrics (MRR, MAP@k, nDCG@k) computed for both old + new systems
- [ ] Comparison report includes operational dimensions, not just accuracy

## Pitfalls (consolidated from Phase 5 + 6)

1. **Neo4j and systemd conflict on restart.** If Neo4j was manually started, systemd's auto-restart finds stale PID. Resolution: `sudo /usr/local/neo4j/bin/neo4j stop && sudo pkill -f "org.neo4j" && sudo systemctl start neo4j.service`. Never leave manual + systemd neo4j processes running simultaneously — they both lock the same data files.

2. **Python venv must be activated.** Neo4j driver and sentence-transformers are in `~/.venv-neo4j/`, not system Python. All scripts must `source ~/.venv-neo4j/bin/activate` first.

3. **Repo discovery: submodules ≠ directories.** Submodules in hermes-wiki-super live under `wiki/`, not root. The indexer MUST check both locations OR delegate to `discover.py` which parses `.gitmodules` directly.

4. **`.git` is a file, not a directory, in submodules.** When checking for git repos, use `(path / ".git").exists()` not `(path / ".git").is_dir()`. Submodules have `.git` as a pointer file.

5. **State file persistence across restarts.** `.index_state.json` tracks per-repo HEAD. If the server restarts mid-index, the state file may be incomplete. Run `--force` on the first index after recovery.

6. **Embedding dimension mismatch.** Vector index is created with 384d. If you change the embedding model, the vector index must be recreated (drop + create). `bge-m3` produces exactly 384d.

7. **Memory budget for 1.9GB RAM server.** Neo4j heap 512MB + page cache 256MB + JVM overhead ~100MB = ~900MB. Leave ~1GB for OS and other processes. Do NOT increase heap beyond 512MB on this hardware.

8. **Cron timezone.** Memory says TZ=KST (UTC+9), cron=UTC+8. Schedule conversion: KST → subtract 1h for cron timezone. 08:00 KST = 07:00 cron time. 03:00 KST = 02:00 cron time.

9. **Hardcoded keywords rot.** (Phase 6 lesson) A query router with 42 hardcoded Korean/English keywords and tag categories will silently degrade as new repos, topics, or languages appear. Prefer vector+graph combinations that make no domain assumptions. Use `discover.py` to keep config in sync with reality, not in code.

10. **Hit@3 alone is not evaluation.** (Phase 6 lesson) For paper-quality comparison, use MRR, MAP@k, nDCG@k, P@k, R@k with graded relevance ground truth. A small query set can tie two systems on Hit@3 while the operational/maintenance dimensions diverge massively.

11. **Disk math ceiling ≠ operational ceiling.** (Capacity lesson) When estimating how many more wikis fit, the math says thousands; the real limit is RAM (Neo4j swap at ~1k pages). Always report the smaller, realistic number alongside the optimistic one.

12. **Always check `~/.cache/uv/` before deleting.** The user explicitly uses uv. Treat uv cache as protected even though it's "just a cache" — it is part of the user's declared toolchain.

## Verification Checklist

- [ ] `systemctl status neo4j.service` shows active (running)
- [ ] `ss -tlnp | grep 7687` shows Neo4j listening
- [ ] Health check passes: `check_health.py --verbose` → Overall: ✅ HEALTHY
- [ ] Query works: `python3 skill/query.py "PER"` returns correct pages
- [ ] Vector search works: custom embedding query matches semantically similar pages
- [ ] Incremental indexer state exists: `.index_state.json` has all repos with HEAD SHAs
- [ ] Cron jobs listed: `cronjob action=list` shows both neo4j-health-check and neo4j-incremental-index
- [ ] Systemd enabled: `systemctl is-enabled neo4j.service` → enabled
- [ ] Submodules indexed: all repos visible in `MATCH (n:Page) RETURN n.repo, count(n)`
- [ ] discover.py detects new submodule: `git submodule add ... && python3 discover.py` shows it
- [ ] IR metrics script runs: `python3 scripts/ir_evaluation.py` produces MRR/MAP/nDCG table
- [ ] Capacity estimate: 100+ wiki headroom confirmed before adding new submodules

## Refs

- `references/neo4j-operations.md` — Full operation guide with query examples
- `references/auto-discovery-pattern.md` — .gitmodules parsing + namespace auto-generation
- `references/capacity-planning.md` — Wiki 추가 가능 개수 계산 + 디스크 정리 안전 가이드
- `scripts/ir_evaluation.py` — Paper-standard IR metrics harness (MRR, MAP@k, nDCG@k, P@k, R@k, F1@k)
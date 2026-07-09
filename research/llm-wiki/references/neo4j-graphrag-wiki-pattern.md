# Neo4j GraphRAG Wiki Pattern — Setup & Query Reference

> Extension to Karpathy LLM Wiki. Adds structured+vector search layer atop existing wiki.
> Prerequisites: Java 17, 1.9GB+ RAM, 280MB+ disk.
> Current scale: 200 pages, 376 relationships, 11 repos.

## Installation

```bash
# Java 17 (headless, ~80MB)
sudo apt install -y openjdk-17-jre-headless

# Neo4j Community 5.26.0
wget https://dist.neo4j.org/neo4j-community-5.26.0-unix.tar.gz
sudo tar -xzf neo4j-*.tar.gz -C /usr/local/
sudo chown -R ubuntu:ubuntu /usr/local/neo4j

# Memory config (neo4j.conf)
server.memory.heap.initial_size=256m
server.memory.heap.max_size=512m
server.memory.pagecache.size=256m
dbms.security.auth_enabled=false

# Python deps (separate venv recommended)
python3 -m venv ~/.venv-neo4j
source ~/.venv-neo4j/bin/activate
pip install neo4j fastembed numpy
```

## Indexer Script Structure

```
hermes-wiki-super/.metagraph/
├── create_schema.py   ← Run once: constraints + indexes
├── embed.py           ← multilingual MiniLM (384d, 50+ languages)
├── indexer.py         ← Scan all wiki/* submodules → MERGE into Neo4j
├── link_cross_repo.py ← Post-indexer: creates cross-repo :LINKS via shared tags
└── skill/             ← Skill plugin scripts
    ├── query.py       ← Query Router (auto-detect semantic/structural/hybrid)
    └── synthesize.py  ← Result formatter
```

Code: https://github.com/mybotagent/hermes-wiki-super/tree/main/.metagraph

## Startup & Operation

```bash
# Start Neo4j
/usr/local/neo4j/bin/neo4j start

# Create schema (one-time)
source ~/.venv-neo4j/bin/activate
python3 ~/hermes-wiki-super/.metagraph/create_schema.py

# Full re-index
python3 ~/hermes-wiki-super/.metagraph/indexer.py

# Cross-repo linking (creates 125+ cross-repo edges)
python3 ~/hermes-wiki-super/.metagraph/link_cross_repo.py

# Query test
python3 ~/.hermes/skills/research/wiki-knowledge-search/scripts/query.py "PER 분석 방법"
```

**Memory usage:** ~466MB RSS (Java 17 heap 256MB + page cache 256MB) on 1.9GB server. Swap available.

## Essential Neo4j Schema

```cypher
-- Constraints
CREATE CONSTRAINT page_id IF NOT EXISTS FOR (p:Page) REQUIRE p.id IS UNIQUE;
CREATE CONSTRAINT page_path IF NOT EXISTS FOR (p:Page) REQUIRE (p.repo, p.path) IS UNIQUE;

-- Range indexes (Neo4j 5.x — NOT BTREE)
CREATE RANGE INDEX page_tags IF NOT EXISTS FOR (p:Page) ON (p.tags);
CREATE RANGE INDEX page_repo IF NOT EXISTS FOR (p:Page) ON (p.repo);
CREATE RANGE INDEX page_updated IF NOT EXISTS FOR (p:Page) ON (p.updated);

-- Vector index (384d for multilingual MiniLM, 1536d for OpenAI)
CREATE VECTOR INDEX page_emb IF NOT EXISTS FOR (p:Page) ON (p.embedding)
OPTIONS {indexConfig: {`vector.dimensions`: 384, `vector.similarity_function`: 'cosine'}};
```

## Cross-Repo Linking

After indexing all repos, run `link_cross_repo.py` to create same-tag edges across repos:

```cypher
// Creates :LINKS {type: 'cross-repo', tags: [...]} between pages in different repos
// that share one or more tags (e.g. both tagged "wiki", "hub", "infra")
MATCH (a:Page), (b:Page)
WHERE a.repo < b.repo AND a.id < b.id
UNWIND a.tags AS tag UNWIND b.tags AS btag
WITH a, b, tag WHERE tag = btag
WITH a, b, collect(tag) AS common WHERE size(common) > 0
MERGE (a)-[r:LINKS {type: 'cross-repo'}]->(b)
SET r.tags = common
```

This produces ~125 cross-repo links for an 11-repo / 200-page corpus.

## Namespace Convention

Each repo gets a 2-letter prefix to avoid ID collisions:

```
hw:analysis:orbit-valuation    ← hermes-wiki repo
tp:utils:finnhub-client        ← trade-pipeline repo
cc:setup-guide                 ← hermes-wiki-claude-code repo
he:lecture-1                   ← harness-engineering-wiki
```

Page ID format: `{ns}:{path_with_slashes_replaced_by_colons}`

## Embedding (no API key needed)

```python
from fastembed import TextEmbedding
model = TextEmbedding(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
emb = list(model.embed(["PER 분석 방법론"]))[0]  # 384d vector
```

**Why not DeepSeek/OpenAI:** DeepSeek has NO embedding API endpoint. OpenAI works but costs money. multilingual MiniLM supports 50+ languages including Korean, runs locally, 384d, ~80MB model download.

## Query Router: Auto-Detect Algorithm

The skill's `query.py` implements a rule-based router that detects query intent without an LLM call:

| Mode | Trigger Keywords | Backend |
|------|-----------------|---------|
| **semantic** | 뭐, 무엇, 방법, 설명, 알려줘, 의미, 정의, 개념 | Vector Index cosine |
| **structural** | 연결, 관계, 관련, 링크, 연관, 함께, 같이, 리스트, 목록 | Cypher MATCH + tag filter |
| **hybrid** | (default for ambiguous) | Both + interleave dedup |

## Query Patterns (tested)

### Vector semantic search
```cypher
// "PER 분석 방법론" → Methodology(0.757), Orbit Valuation(0.718)
CALL db.index.vector.queryNodes('page_emb', 5, $embedding)
YIELD node, score
RETURN node.title, node.repo, node.summary, score ORDER BY score DESC;
```

### Graph traversal (2-hop)
```cypher
// "Cron Jobs 연결 페이지" → Environment, Discord, GH Token
MATCH (p:Page {title: 'Cron Jobs'})-[:LINKS*1..2]->(x:Page)
RETURN DISTINCT x.title, x.repo;
```

### Tag filter + graph
```cypher
MATCH (p:Page)-[:LINKS*1..2]->(related:Page)
WHERE 'valuation' IN p.tags
RETURN p.title, collect(DISTINCT related.title) AS related_pages;
```

### Cross-repo query
```cypher
// Pages connected across repos
MATCH (a:Page)-[r:LINKS {type: 'cross-repo'}]->(b:Page)
RETURN a.title, a.repo, b.title, b.repo, r.tags LIMIT 10;
```

### Connection hubs
```cypher
MATCH (p:Page)-[r:LINKS]-(x:Page)
RETURN p.title, p.repo, count(DISTINCT x) AS degree
ORDER BY degree DESC LIMIT 5;
```

## Pitfalls

| Problem | Fix |
|---------|-----|
| `store_lock` after crash | `rm -f /usr/local/neo4j/data/databases/store_lock` |
| Korean LLMs (DeepSeek etc.) no embedding API | Use fastembed multilingual MiniLM instead |
| Vector index dimension mismatch | Match embedding model dim (384 MiniLM, 768 BGE, 1024 E5) |
| Neo4j needs auth disabled | `dbms.security.auth_enabled=false` in neo4j.conf |
| Systemd service fails | Type=forking, TimeoutStartSec=120, check PID file path |
| Neo4j 5.x: `BTREE INDEX` → `RANGE INDEX` | Neo4j 5 deprecated BTREE; use `CREATE RANGE INDEX ... ON (p.field)` |
| `type(r)` on variable-length path `[r:LINKS*1]` | Use `[r:LINKS]` (fixed length) instead; variable-length returns a list not a single rel |
| hermes-logs pages dominate vector results | Log messages contain rich keywords. Consider repo-weighted scoring for production |
| Cross-repo wikilink resolution | Indexer resolves within-repo only. Cross-repo links generated separately via shared-tag matching |

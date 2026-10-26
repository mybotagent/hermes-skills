# GraphRAG Search Backend for Multi-Repo Wiki

> **Context:** Designed during a discussion about scaling the Karpathy LLM Wiki
> (mybotagent/hermes-wiki-super) to 100+ repositories with a knowledge search
> skill plugin. User wanted GraphRAG + Vector DB (Neo4j) for portfolio value
> and future-proof scalability.
>
> **Design principle:** Scalability-first. Build for 100+ repos from day one.
> Incremental index, not full rebuild.

## Architecture Overview

```
┌─────────────────────────────────────────────┐
│           Hermes Agent (질문)                │
│  ┌─ 의미 검색 필요? ──────────────────┐     │
│  │ Vector index → semantic top-K     │     │
│  └────────────────────────────────────┘     │
│  ┌─ 관계 탐색 필요? ──────────────────┐     │
│  │ Cypher → graph traversal (1~N hop)│     │
│  └────────────────────────────────────┘     │
│  ↓ 결과 합성                              │
│  ↓ LLM reads candidate pages from wiki    │
│  ↓ Synthesis                              │
└─────────────────────┬───────────────────────┘
                      │
┌─────────────────────▼───────────────────────┐
│              Neo4j (AuraDB)                 │
│                                             │
│  (:Page)─[:LINKS]→(:Page)                   │
│    └── embedding: [...1536d]                │
│                                             │
│  Indexes:                                    │
│  - page_emb (vector, cosine)                │
│  - idx_page_repo (B-tree on repo)           │
│  - idx_page_tag (B-tree on tags)            │
└─────────────────────┬───────────────────────┘
                      │
┌─────────────────────▼───────────────────────┐
│        .metagraph/ (build artifacts)        │
│  - config.yaml (namespace mappings)         │
│  - last_commit_map.json (incremental SHA)   │
│  - BUILD.md (rebuild procedure)             │
└─────────────────────┬───────────────────────┘
                      │
┌─────────────────────▼───────────────────────┐
│  hermes-wiki-super/ (100+ submodules)       │
│  ├── hermes-wiki/     ← submodule @ SHA     │
│  ├── trade-pipeline/  ← submodule @ SHA     │
│  ├── hermes-wiki-codex/ ← submodule @ SHA   │
│  └── ... (100+)                             │
└─────────────────────────────────────────────┘
```

## Neo4j Data Model

### Node: `:Page`

Every wiki page across all repos becomes one Neo4j node:

```cypher
CREATE CONSTRAINT page_id_unique IF NOT EXISTS
FOR (p:Page) REQUIRE p.id IS UNIQUE;
```

| Property | Type | Example | Description |
|----------|------|---------|-------------|
| `id` | STRING | `hw:valuation` | `{repo_namespace}:{page_slug}` |
| `repo` | STRING | `hermes-wiki` | Submodule repo name |
| `repo_sha` | STRING | `b8ebbf3` | Git SHA at time of index |
| `path` | STRING | `analysis/orbit-valuation.md` | Relative path in repo |
| `title` | STRING | `Orbit Valuation` | From frontmatter or h1 |
| `tags` | STRING[] | `["valuation", "analysis"]` | From frontmatter |
| `confidence` | STRING | `high` | From frontmatter |
| `summary` | STRING | `적정 PER+PBR 혼합 밸류에이션...` | LLM-generated (200 char) |
| `created` | DATE | `2026-01-15` | From frontmatter |
| `updated` | DATE | `2026-06-01` | From frontmatter |
| `embedding` | FLOAT[] | `[0.123, -0.456, ...]` | 1536d vector (text-embedding-3-small or local) |

### Relationship: `[:LINKS]`

Every explicit connection between pages:

```cypher
CREATE INDEX links_from_to IF NOT EXISTS
FOR ()-[r:LINKS]-() ON (r.from, r.to);
```

| Property | Type | Example | Description |
|----------|------|---------|-------------|
| `type` | STRING | `wikilink` | `wikilink` or `related` |
| `weight` | FLOAT | `1.0` | Relevance weight (default 1.0) |

Source: `[[wikilinks]]` in page body → `[:LINKS {type: 'wikilink'}]`
Source: `related: [page-list]` in frontmatter → `[:LINKS {type: 'related'}]`

## Repository Namespace Strategy

Prevents ID collisions across 100+ repos:

```yaml
# .metagraph/config.yaml
namespaces:
  hermes-wiki: hw
  trade-pipeline: tp
  hermes-wiki-codex: wc
  hermes-wiki-claude-code: wcc
  harness-engineering-wiki: hew
  subagents-library: sal
  # ... auto-generated for new submodules
```

**Resolution rule:** When page X in repo A wikilinks to `[[page-y]]` without namespace,
it's resolved within the same repo first. If no match, the resolver checks all repos
for a page titled `page-y` and logs a warning for ambiguous matches.

## Build Pipeline

### Full Build

```python
def build():
    for submodule in scan_submodules(super_repo_path):
        for page in scan_pages(submodule.path):
            frontmatter = parse_frontmatter(page)
            embedding = generate_embedding(frontmatter.title + " " + frontmatter.summary)

            # Upsert node
            tx.run("""
                MERGE (p:Page {id: $id})
                SET p.repo = $repo, p.repo_sha = $sha,
                    p.path = $path, p.title = $title,
                    p.tags = $tags, p.summary = $summary,
                    p.embedding = $embedding,
                    p.updated = $updated
            """, id=namespaced_id, ...)

            # Upsert edges
            for link in frontmatter.related + page.wikilinks:
                tx.run("""
                    MATCH (from:Page {id: $from_id})
                    MATCH (to:Page {id: $to_id})
                    MERGE (from)-[r:LINKS {type: $link_type}]->(to)
                """, ...)

    # Save commit map for incremental builds
    save_last_commits()
```

### Incremental Build

Only re-index repos whose git SHA changed:

```python
def incremental_build():
    current_shas = {submodule: get_head_sha(submodule)
                    for submodule in scan_submodules()}
    last_shas = load_last_commits()

    for repo, sha in current_shas.items():
        if sha != last_shas.get(repo):
            print(f"🔄 Re-indexing {repo} ({sha[:7]})")
            reindex_repo(repo)
            record_commit(repo, sha)

    save_last_commits(current_shas)
```

## Query Patterns

### Pattern 1: Semantic Search (Vector Index)

```cypher
// 질문: "PER valuation 방법"
CALL db.index.vector.queryNodes('page_emb', 5, $query_embedding)
YIELD node, score
RETURN node.title, node.repo, node.path, score
ORDER BY score DESC
```

### Pattern 2: Graph Traversal (Structural)

```cypher
// 질문: "valuation과 연결된 모든 페이지"
MATCH (p:Page {repo: 'hermes-wiki'})-[:LINKS*1..2]->(related:Page)
WHERE p.title CONTAINS 'valuation' OR 'valuation' IN p.tags
RETURN p.title, collect(DISTINCT related.title) AS connections
```

### Pattern 3: Hybrid (Best) ⭐

```cypher
// 질문: "딥시크 분석 방법"
// Step 1: Semantic search for "딥시크"
CALL db.index.vector.queryNodes('page_emb', 10, $deepseek_embedding)
YIELD node, score

// Step 2: Graph traversal from semantic matches
MATCH (node)-[:LINKS*1..2]->(related:Page)

// Step 3: Filter by domain relevance
WHERE any(tag IN related.tags WHERE tag IN ['analysis', 'methodology', 'valuation'])

RETURN node.title, node.repo, score,
       collect(DISTINCT {title: related.title, repo: related.repo}) AS extended_context
ORDER BY score DESC LIMIT 5
```

### Pattern 4: Community Discovery (GraphRAG)

```cypher
// Graph Data Science: Leiden community detection
CALL gds.graph.project('wiki_graph', 'Page', 'LINKS')
YIELD graphName

CALL gds.leiden.mutate('wiki_graph', {mutateProperty: 'community'})
YIELD communityCount

// 각 커뮤니티 요약 (미리 생성)
MATCH (p:Page)
RETURN p.community AS community,
       collect(p.title)[..5] AS sample_pages,
       count(*) AS size
ORDER BY size DESC
```

Community summaries are LLM-generated and stored as separate nodes for
global query support (Microsoft GraphRAG pattern).

## Infrastructure Options

| Option | Setup | Cost | Best for |
|--------|-------|------|----------|
| **AuraDB Free** | 가입 5분 | 무료 (50k nodes, 175k edges) | 프로덕션, 항상 켜짐 |
| **AuraDB Pro** | 업그레이드 | ~$55/월 | 100k+ nodes |
| **Docker (local)** | `docker run neo4j` | 무료 | 개발/테스트 |
| **Neo4j Desktop** | 설치 | 무료 (dev only) | 초기 프로토타입 |

**AuraDB Free 권장** — 무료 tier로 100+ repo 커버 가능. Hermes Agent가
Bolt protocol로 직접 연결. 인증서 + URL만 있으면 됨.

## Implementation Order

```
Phase 1: Neo4j setup (30분)
  → AuraDB Free 가입 또는 Docker 실행
  → .metagraph/config.yaml 생성
  → Python 연결 확인

Phase 2: Index build (1일)
  → submodule scan
  → frontmatter → node upsert
  → wikilink → edge upsert
  → embedding generation
  → incremental SHA tracking

Phase 3: Query skill (1~2일)
  → Hermes Skill Plugin (wiki-knowledge-search)
  → Semantic search (vector index)
  → Graph traversal (Cypher)
  → Hybrid merge
  → LLM synthesis

Phase 4: GraphRAG (별도)
  → Leiden community detection
  → Community summary generation
  → Global query support
  → Neo4j Browser visualization
```

## Design Alternatives Evaluated

### ❌ Pure Vector DB (Pinecone/Qdrant/Chroma)
- Wikilinks, related fields, tags, hierarchy **all discarded** by chunking
- Our wiki is already a structured knowledge graph — flattening to chunks wastes it
- Portfolio: "basic RAG" — saturated market, low differentiation

### ❌ SQLite + Recursive CTE
- No vector index → no semantic search
- Recursive CTE for graph traversal works but verbose
- Portfolio value: minimal

### ❌ qmd standalone
- Great for text search but no relationship graph
- No multi-repo namespace support
- Good companion tool, not replacement

### ✅ Neo4j + Vector Index (this design)
- Graph + vector in single DB
- Portfolio: "GraphRAG: Neo4j + Vector Index over 100+ repo knowledge base"
- Cypher for structure, vector for semantics — complementary, not competing

---
name: wiki-knowledge-search
description: "hermes-wiki-super × Neo4j GraphRAG 기반 지식 검색 — 자연어 질문 → Vector + Graph 하이브리드 검색 → LLM 합성"
version: 0.2.0
author: aiprofit
platforms: [linux]
metadata:
  hermes:
    tags: [wiki, graphrag, neo4j, search, knowledge-base, graphdb]
    category: research
    related_skills: [llm-wiki, wiki-auto-refresh]
---

# Wiki Knowledge Search

> **Backend:** Neo4j Community (localhost:7687) + multilingual MiniLM embedding (384d)
> **Data:** 200 pages, 376 relationships, 11 repos
> **설치:** `infra/neo4j-local.md` | **설계:** `meeting-notes/2026/06/29/DESIGN.md`

## When to Use

Use this skill when the user asks about our wiki's knowledge domains — valuation, infra, analysis, trading, prompts, AI job analysis, etc. Or when they explicitly request Neo4j/GraphRAG/wiki search.

**Do NOT use** when the question is a simple memory lookup or about the current trade pipeline execution — those have dedicated skills.

## Current Status (Phase 4 Complete)

| Phase | Pages | Repos | Links |
|-------|-------|-------|-------|
| P1: Neo4j Setup | 64 | 2 | 78 |
| P2: Embedding | 64 | 2 | 78 |
| P3: Skill Plugin | 64 | 2 | 78 |
| **P4: Cross-repo** | **200** | **11** | **376** |

## How It Works

```
사용자 질문
  → Auto-detect: semantic / structural / hybrid
  → Neo4j: Vector Search + Cypher Graph Traversal
  → Enrich: 1-hop neighborhood
  → Synthesize: 결과 + provenance
```

## Architecture

Three query modes (rule-based auto-detect, no LLM call needed):

| Mode | Trigger | Backend | Example |
|------|---------|---------|---------|
| **semantic** | 개념/정의/방법 질문 | Vector Index (cosine) | "PER 분석 방법" |
| **structural** | 관계/연결/목록 질문 | Cypher Graph (1~2 hop) | "Cron Jobs 연결" |
| **hybrid** | 일반/모호한 질문 | Both + interleave | "밸류에이션 관련" |

## Scripts

### query.py — Query Router
```bash
source ~/.venv-neo4j/bin/activate
python3 ~/.hermes/skills/research/wiki-knowledge-search/scripts/query.py "PER 분석 방법 알려줘"
python3 ~/.hermes/skills/research/wiki-knowledge-search/scripts/query.py --mode structural "Cron Jobs랑 연결된 페이지"
python3 ~/.hermes/skills/research/wiki-knowledge-search/scripts/query.py --json "밸류에이션"
```

### synthesize.py — Result Formatter
Structured response with provenance. Pass JSON via stdin:
```bash
python3 query.py --json "질문" | python3 synthesize.py
```

### Indexer Pipeline (in hermes-wiki-super/.metagraph/)
```bash
# Full re-index
python3 indexer.py

# Single repo
python3 indexer.py --repo hermes-wiki

# Cross-repo linking (run after indexer)
python3 link_cross_repo.py
```

## Cross-Repo Namespaces

| Prefix | Repo | Pages |
|--------|------|-------|
| `hw:` | hermes-wiki | 34 |
| `hl:` | hermes-logs | 30 |
| `he:` | harness-engineering-wiki | 26 |
| `tp:` | trade-pipeline | 24 |
| `am:` | ai-marketing-wiki | 20 |
| `hp:` | hermes-prompts | 18 |
| `cc:` | hermes-wiki-claude-code | 18 |
| `hq:` | hermes-wiki-quant | 10 |
| `cx:` | hermes-wiki-codex | 9 |
| `aj:` | ai-job-analysis | 8 |
| `hs:` | hermes-slash-commands | 3 |

## Pitfalls

- **DeepSeek has NO embedding API** — use fastembed multilingual MiniLM instead
- **Neo4j 5.x uses RANGE INDEX not BTREE INDEX** — `CREATE RANGE INDEX` syntax
- **Variable-length path returns a list** — `[r:LINKS*1]` returns a list of rels, not a single one. Use `[r:LINKS]` for fixed-length
- **store_lock after crash** — `rm -f /usr/local/neo4j/data/databases/store_lock`
- **Auto-detect misses subtle queries** — extend keyword lists in query.py's detect_mode() when needed
- **🔴 Submodule HEAD stale (CRITICAL — silent indexing failure, 2026-07-02 발견)** — after `git push` to `~/hermes-wiki/` (standalone clone), new page does NOT appear in `query.py` results even after indexer runs.

  **Symptom**: `index_incremental.py` reports `All 14 repos unchanged. Nothing to index.` despite recent push.

  **Root cause**:
  - `~/hermes-wiki/` (standalone clone) and `~/hermes-wiki-super/wiki/hermes-wiki/` (submodule working tree) are **TWO DIFFERENT working trees** pointing to the same remote
  - Indexer reads `~/hermes-wiki-super/.metagraph/.index_state.json` which stores HEAD from the **SUBMODULE's working tree**, not the standalone clone
  - Pushing to `~/hermes-wiki/` updates the remote but does NOT update the submodule HEAD in `~/hermes-wiki-super/wiki/hermes-wiki/`
  - Indexer compares its stored HEAD against the submodule's (still-old) HEAD → no diff → no reindex

  **Fix** (15-20 seconds):
  ```bash
  cd ~/hermes-wiki-super/wiki/hermes-wiki
  git fetch origin
  git reset --hard origin/main
  cd ~/hermes-wiki-super
  python3 .metagraph/index_incremental.py
  ```

  **Verification**:
  ```bash
  python3 -c "
  from neo4j import GraphDatabase
  driver = GraphDatabase.driver('bolt://localhost:7687')
  with driver.session() as session:
      for r in session.run('MATCH (p:Page) WHERE p.repo = \"hermes-wiki\" AND p.path CONTAINS \"architecture\" RETURN p.path LIMIT 10'):
          print(r['p.path'])
  "
  ```
  Expected: new page appears in result. If only old 3 pages appear → submodule reset not applied.

  **Automation**: see `~/.hermes/scripts/wiki_reindex.sh` (created 2026-07-02, ~990 bytes) — wraps submodule reset + incremental reindex in a single command.

  **Two `indexer.py` scripts exist** (CONFUSION HAZARD):
  - `~/.hermes/skills/research/wiki-knowledge-search/scripts/indexer.py` — single `--repo` only, no `--force`
  - `~/hermes-wiki-super/.metagraph/indexer.py` — accepts multiple `--repo`, has `--force`, called by `index_incremental.py`
  - Use the second one (via `index_incremental.py`) for production reindex.

## Related

- **🔴 Layer 1→2 자동 sync 미작동 (CRITICAL for 4-Layer 합의)**: wiki 페이지 push 후에도 Neo4j 색인은 자동 갱신 안 됨. 증상: `query.py` "memory pipeline 4 layer" 검색 시 `architecture/hermes-memory-pipeline.md` (commit 271e571, 방금 push) 미반영. Neo4j 직접 query 결과 architecture/ 색인은 기존 3페이지만 (신규 push 누락). 해결 옵션: (a) cron 등록으로 주기적 full reindex (`indexer.py --repo <name>`), (b) wiki-save hook에서 `indexer.py` 자동 호출, (c) v0.3 upgrade (incremental indexer 포함 평가). 4-Layer 합의의 wiki→Neo4j sync는 **별도 인프라 작업 필수** — 가정으로 두지 말 것.
- **indexer.py is NOT incremental**: `--repo` 옵션으로 실행해도 신규 페이지가 count에 안 잡히는 케이스 발생 (위 pitfall 원인). full reindex로 작동하지만 git HEAD 기반 incremental 동작 X. 35 pages count 동일하게 유지되면 새 콘텐츠 미반영 신호.
- **Sub-directory (memory-snapshots/) 누락 가능**: `architecture/memory-snapshots/<file>` 같은 nested 신규 디렉토리는 indexer가 재귀 인덱싱 안 할 수 있음. architecture/ 직속 페이지는 OK, sub-directory는 별도 검증 필수.
- **Embedding model latency**: 첫 호출 시 모델 로드 ~7s (paraphrase-multilingual-MiniLM-L12-v2). 캐시 후 ~3-4s. 두 회 이상 측정 권장 — 첫 latency로 false-negative 판단 금지.
- **Wiki repo private**: `raw.githubusercontent.com/mybotagent/<repo>/main/...` → 404 (private repo). 검증은 `git ls-remote origin main` commit hash 일치로.

## Integration with Hermes Memory Pipeline (4-Layer)

This skill is **Layer 2** of the 4-Layer Memory Pipeline architecture (agreed 2026-07-02, doc: `hermes-wiki/architecture/hermes-memory-pipeline.md`):

| Layer | Tool | Role |
|-------|------|------|
| 0 | Memory Tool (2.2KB) | Hot data, session 1회 로드, 캐시 hit 5m |
| 1 | hermes-wiki + 13+ repos (wiki-save) | 영속 원본 |
| **2** | **wiki-knowledge-search (this skill)** | **Vector + graph 인덱스** |
| 3 | 채니봇 lazy search (3-mode) | 의미 검색 |

**운영 패턴 (Lazy + Cache):**
- 매 세션 전체 wiki 로드 X → search 시점에만 `query.py` 호출
- 결과는 시스템 메시지로 합성 → 후속 turn 캐시 hit
- `prompt_caching: cache_ttl: 5m` (Hermes 기본 활성) 이 비용 0화

**Stale 위험 (5분 캐시 + wiki 갱신):**
- wiki-save 직후 5분 내 검색 시 이전 내용 나올 수 있음
- Mitigation: 5분 경과로 자연 만료 또는 cache evict hook 검토
- 일반 워크플로우 (분석/요약/리포트)에서는 문제 X

**연결:**
- `wiki-save` (Layer 1) — raw + 페이지 + INDEX + 로그 + push 일괄
- `index_incremental.py` — git HEAD 기반 incremental reindex (cron 등록 가능)
- `query.py --mode {semantic,structural,hybrid}` — 3-mode auto-routing

## Related

- `llm-wiki` — the Karpathy wiki pattern this builds on
- `infra/neo4j-local.md` — installation docs in hermes-wiki
- `architecture/hermes-memory-pipeline.md` — 4-Layer 합의 디자인

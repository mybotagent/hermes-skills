---
name: wiki-graphrag-search
description: "GraphRAG 검색 레이어를 Karpathy LLM Wiki 위에 구축 — Neo4j + Vector Index + Hermes Skill Plugin 아키텍처"
version: 1.0.0
author: aiprofit
platforms: [linux, macos]
metadata:
  hermes:
    tags: [wiki, graphrag, neo4j, vector-search, knowledge-base, search]
    related_skills: [llm-wiki, wiki-auto-refresh]
---

# Wiki GraphRAG Search

> Karpathy LLM Wiki 패턴 위에 **검색/그래프 인프라**를 추가하는 아키텍처 가이드.
> 단순 markdown 파일 탐색을 넘어, 100+ submodule / 2000+ 페이지 환경에서도 확장 가능한 검색 시스템.

## When This Skill Activates

- 사용자가 wiki 검색 성능 개선, GraphRAG, knowledge search plugin을 언급
- "Neo4j", "Vector DB", "Graph DB", "GraphRAG" 관련 논의
- 위키 기반 검색 시스템 아키텍처 설계
- OpenKB / lcwiki / qmd / knowledge-manager 참조

## 배경: 왜 GraphRAG인가

Karpathy LLM Wiki는 **LLM이 직접 파일을 읽고 탐색**하는 방식을 기본으로 함. 이 방식은 ~100페이지까지는 index.md + `[[wikilinks]]` + frontmatter `related:` 필드로 충분.

그러나 100+ submodule / 2000+ 페이지 환경에서는:
- cross-repo 검색 불가 (`search_files`는 단일 디렉토리 한계)
- 관계 추적에 N번의 read_file 필요 (O(n) 비용)
- "이 개념이 어떤 분석들과 연결되어 있나?" 같은 global 질의 불가

## Architecture: Neo4j + Vector Index Hybrid

```
┌──────────────────────────────────────┐
│        Hermes Agent                  │
│  wiki-knowledge-search skill plugin  │
└────────────────┬─────────────────────┘
                 │
┌────────────────▼─────────────────────┐
│       Query Router (LLM decides)     │
│                                      │
│  Semantic Path ─── Vector Search     │
│    (embedding cosine similarity)     │
│                                      │
│  Structural Path ── Cypher Graph Traverse│
│    (wikilink / related / same_as)    │
│                                      │
│  결과 합성 → top-K 페이지 → LLM read │
└────────────────┬─────────────────────┘
                 │
┌────────────────▼─────────────────────┐
│   Neo4j (AuraDB Free or Local)       │
│                                      │
│  (:Page) {                           │
│    id: "hw:valuation",              │
│    repo: "hermes-wiki",             │
│    title: "Orbit Valuation",        │
│    tags: ["valuation","analysis"],  │
│    summary: "...",                   │
│    embedding: [1536d vector],        │
│    updated: 2026-06-01               │
│  }                                   │
│                                      │
│  [:LINKS] {                          │
│    type: "wikilink"|"related"|"same_as"│
│  }                                   │
│                                      │
│  VECTOR INDEX page_emb (cosine)      │
└────────────────┬─────────────────────┘
                 ▲  (incremental upsert)
┌────────────────┴─────────────────────┐
│  hermes-wiki-super/.metagraph/        │
│                                      │
│  submodule git SHA 기반 증분 인덱싱    │
│  → 변경된 레포만 재스캔               │
│  → MERGE nodes + edges into Neo4j    │
└──────────────────────────────────────┘
```

### 핵심 결정 (이 사용자 환경 기준)

| 결정사항 | 선택 | 이유 |
|----------|------|------|
| Backend | **Neo4j 5.x Vector Index** | DB 하나로 Graph + Vector 통합. Cypher 네이티브. |
| Vector DB 단독 | ❌ | wikilink/related/tags 등 구조 정보 전부 손실 |
| Graph DB 단독 | 🟡 | 의미 검색 약함 (LLM에 100% 의존) |
| SQLite + CTE | ❌ | 10k node 이상에서 recursive CTE 성능 저하 |
| KùzuDB | 🟡 | 좋지만 ecosystem 작음, 포트폴리오 가치 ↓ |
| Tier | **AuraDB Free** | 50k nodes / 175k edges 무료, 유지보수 0 |

### .metagraph/ Incremental Indexer

```
hermes-wiki-super/
├── .metagraph/
│   ├── indexer.py          ← submodule 스캔 → Neo4j upsert
│   ├── config.yaml         ← namespace mappings + build rules
│   └── BUILD.md            ← 빌드 절차
├── hermes-wiki/             ← submodule
├── trade-pipeline/          ← submodule
└── ... (100+)
```

**동작:**
1. 각 submodule의 git SHA 확인 (이전 SHA와 비교)
2. 변경된 submodule만 재스캔 (incremental — O(changed) not O(total))
3. index.md + frontmatter 읽기 → nodes upsert
4. wikilink / related 필드 → edges upsert
5. 페이지 본문 → embedding 생성 → Vector Index upsert

## 참고 프로젝트 비교

| 프로젝트 | 특징 | 우리에 활용 |
|----------|------|-----------|
| **OpenKB** (VectifyAI, ⭐2.7k) | CLI 기반, PageIndex vectorless retrieval, Skill Factory, `openkb visualize`로 지식 그래프 | 아이디어: 문서 컴파일 → wiki + concept + entity 분리 |
| **lcwiki** (LCccode, ⭐4) | 3-layer (articles → concepts → vis-network graph), ~10% RAG token | 아이디어: vis-network 그래프 시각화, incremental training |
| **qmd** (tobi, ⭐27k) | CLI search engine, hybrid BM25/vector, LLM re-ranking, MCP server | 아이디어: re-ranking 전략, BM25 fallback |
| **knowledge-manager** (treylom, ⭐177) | Claude Code plugin, Zettelkasten, Obsidian/Notion 저장 | 구조 참고용 (플랫폼 달라 직접 사용 불가) |

## 실행 순서 (구현 가이드)

### Phase 1: Infrastructure Setup
1. AuraDB 가입 → Free Tier 인스턴스 생성
2. `pip install neo4j` (Python driver)
3. `.metagraph/` 디렉토리 생성 + `config.yaml` 작성

### Phase 2: Indexer
4. `indexer.py` — submodule 스캔 → Neo4j MERGE nodes
5. wikilink 파싱 → `[:LINKS]` 관계 upsert
6. embedding 생성 → Vector Index 저장

### Phase 3: Query Plugin
7. Hermes Skill: `wiki-knowledge-search` 구현
8. Query Router (Vector or Cypher or both)
9. 결과 합성 → LLM context 주입

## Pitfalls

- **Vector DB 단독 선택 금지** — 우리 wiki는 구조(태그, 관계, 계층)가 핵심 자산. Flat chunk 검색은 이 구조를 전부 무시함.
- **Graph DB 단독 선택 금지** — 유의어 검색 ("PER" = "P/E Ratio" = "Price Earnings")이 안 됨. embedding layer가 반드시 필요.
- **Full scan 금지** — 100 repo를 매번 풀스캔하면 인덱싱 시간이 O(n). submodule git SHA 기반 incremental만.
- **Binary file (KùzuDB 등) git track 금지** — .metagraph/는 코드만. Neo4j 데이터는 cloud에.
- **Namespace 충돌 방지** — 각 repo에 고유 접두사 부여 (예: `hw:` = hermes-wiki, `tp:` = trade-pipeline)

## Related Skills

- `llm-wiki` — Karpathy LLM Wiki 기본 패턴 (이 skill의 기반)
- `wiki-auto-refresh` — wiki 주간 정리/health check
- `wiki-architecture` — wiki repo 구조 설계

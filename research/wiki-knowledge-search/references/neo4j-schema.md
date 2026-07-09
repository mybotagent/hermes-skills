# Neo4j Schema Reference

## Node: Page

```cypher
(p:Page {
  id: "hw:analysis:orbit-valuation",    // STRING (PK) — {namespace}:{path.replace('/',':')}
  repo: "hermes-wiki",                   // STRING — submodule name
  path: "analysis/orbit-valuation.md",   // STRING — repo 내 상대 경로
  title: "Orbit Valuation",             // STRING — frontmatter title or file name
  tags: ["valuation", "analysis"],       // STRING[] — frontmatter tags
  summary: "적정 PER+PBR 혼합 밸류에이션...", // STRING — 200자 첫 문단
  full_text: STRING,                     // 전문 (optional, 2KB truncated)
  embedding: FLOAT[],                    // 1536d vector (optional)
  updated: "2026-06-01",                 // STRING — date
  confidence: "medium",                  // STRING — high|medium|low
  created: "2026-06-01"                  // STRING — date (optional)
})
```

## Rel: LINKS

```cypher
(a:Page)-[r:LINKS {type: "wikilink"}]->(b:Page)
```

`type` enum:
- `wikilink` — 본문 `[[wikilink]]` 참조
- `related` — frontmatter `related:` 필드
- `same_as` — 동일 개념 다른 이름
- `subpage` — parent/child 관계 (future)

## Constraints

```cypher
CREATE CONSTRAINT page_id IF NOT EXISTS FOR (p:Page) REQUIRE p.id IS UNIQUE;
CREATE CONSTRAINT page_path IF NOT EXISTS FOR (p:Page) REQUIRE (p.repo, p.path) IS UNIQUE;
```

## Indexes (Range)

```cypher
CREATE RANGE INDEX page_tags IF NOT EXISTS FOR (p:Page) ON (p.tags);
CREATE RANGE INDEX page_repo IF NOT EXISTS FOR (p:Page) ON (p.repo);
CREATE RANGE INDEX page_updated IF NOT EXISTS FOR (p:Page) ON (p.updated);
```

## Index (Vector, Neo4j 5.18+)

```cypher
CREATE VECTOR INDEX page_emb IF NOT EXISTS FOR (p:Page) ON (p.embedding)
OPTIONS {indexConfig: {`vector.dimensions`: 1536, `vector.similarity_function`: "cosine"}};
```

## Neo4j 5.x 주의사항

- `BTREE INDEX`는 Neo4j 5.x에서 제거됨 → `RANGE INDEX` 사용
- Vector Index는 Neo4j 5.18+에서만 지원
- Vector dimension은 생성 시 고정 (변경 불가 → drop & recreate)
- embedding 필드 없는 노드는 Vector Index 쿼리에서 자동 제외

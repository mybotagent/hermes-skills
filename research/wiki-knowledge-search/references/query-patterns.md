# Query Patterns

## 1. 단순 벡터 검색 (질문 → 유사 페이지)

```cypher
CALL db.index.vector.queryNodes('page_emb', 10, $query_embedding)
YIELD node, score
RETURN node.id, node.title, node.repo, score
ORDER BY score DESC
```

Python:
```python
query_emb = get_embedding(question)  # OpenAI / Ollama
with driver.session() as s:
    results = s.run(
        "CALL db.index.vector.queryNodes('page_emb', $k, $emb) "
        "YIELD node, score RETURN node.id AS id, node.title AS title, score",
        k=10, emb=query_emb
    )
    for r in results:
        print(f"{r['title']}: {r['score']:.3f}")
```

## 2. 태그 필터 + 그래프 탐색

```cypher
MATCH (p:Page)-[:LINKS*1..2]->(related:Page)
WHERE 'valuation' IN p.tags
RETURN p.title AS source,
       collect(DISTINCT {id: related.id, title: related.title, repo: related.repo}) AS connections,
       count(DISTINCT related) AS connection_count
ORDER BY connection_count DESC
```

## 3. 특정 레포만 검색

```cypher
MATCH (p:Page)
WHERE p.repo = 'hermes-wiki'
  AND p.updated > date('2026-01-01')
RETURN p.title, p.path, p.updated
ORDER BY p.updated DESC
```

## 4. 연결 중심 페이지 찾기 (Hub 탐지)

```cypher
MATCH (p:Page)-[r:LINKS]-()
RETURN p.title, p.repo, count(r) AS degree
ORDER BY degree DESC
LIMIT 10
```

## 5. 두 페이지 사이 경로 찾기

```cypher
MATCH path = shortestPath(
  (a:Page {id: 'hw:analysis:orbit-valuation'})-[:LINKS*]-(b:Page {id: 'hw:analysis:methodology'})
)
RETURN [n in nodes(path) | n.title] AS path_nodes,
       [r in relationships(path) | r.type] AS path_rels
```

## 6. 콜드 스타트 (벡터 없을 때)

embedding이 아직 없으면 frontmatter 태그 매칭으로 fallback:

```cypher
MATCH (p:Page)
WHERE ANY(tag IN $keywords WHERE tag IN p.tags)
RETURN p.title, p.repo, p.tags
ORDER BY size(apoc.coll.intersection(p.tags, $keywords)) DESC
LIMIT 10
```

## 7. 통계 쿼리

```cypher
// Repo별 페이지 수
MATCH (p:Page) RETURN p.repo, count(p) AS cnt ORDER BY cnt DESC

// Confidence 분포
MATCH (p:Page) RETURN p.confidence, count(p) AS cnt ORDER BY cnt DESC

// 연결 타입 분포
MATCH ()-[r:LINKS]->() RETURN r.type, count(*) AS cnt ORDER BY cnt DESC
```

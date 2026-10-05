# Query Router: Auto-Detect Mode Architecture

> Hermes Agent가 사용자 질문을 받았을 때, semantic(벡터) 검색인지 structural(Cypher 그래프) 검색인지, 아니면 둘 다(hybrid)인지 **자동 판단**하는 로직.

## Why Auto-Detect

사용자가 "PER 분석 방법 알려줘"라고 물으면 **의미 기반 검색**(벡터 유사도)으로 충분.
"크론 작업이랑 연결된 페이지"라고 물으면 **구조 기반 검색**(Cypher 그래프 탐색)이 필요.
매번 사용자가 모드를 지정하게 하면 UX가 나쁘고, Hermes Agent가 매번 LLM 호출로 판단하면 비용이 듦.

→ **규칙 기반 auto-detect**가 최적.

## Detection Algorithm

```python
def detect_mode(query: str) -> str:
    q = query.lower()
    
    # Structural keywords: 관계/연결 탐색
    if any(w in q for w in [
        "연결", "관계", "관련", "링크", "연관",
        "함께", "같이", "리스트", "목록",
        "연결된", "관련된",
    ]):
        return "structural"
    
    # Semantic keywords: 개념/의미 질문
    if any(w in q for w in [
        "뭐", "무엇", "방법", "설명", "알려줘",
        "의미", "정의", "개념", "뜻",
        "어떻게", "왜",
    ]):
        return "semantic"
    
    # Default: hybrid (best general purpose)
    return "hybrid"
```

## Three Modes

### 1. Semantic (벡터 검색)
```
사용자: "PER 분석 방법론"
→ vec search → Methodology(0.757), Orbit Valuation(0.718) ✅
```

**적합:** 개념 질문, 정의, 방법론, 용어 설명
**백엔드:** Neo4j `db.index.vector.queryNodes('page_emb', ...)` cosine similarity

### 2. Structural (그래프 탐색)
```
사용자: "Cron Jobs 연결 페이지"
→ tag filter 'cron','infra' → 23연결 → Environment, Discord Gateway, GH Token ✅
```

**적합:** 관계 질문, 의존성, 연결 맵, 태그 기반 목록
**백엔드:** Cypher `MATCH (p)-[:LINKS*1..2]->(neighbor) WHERE tag IN p.tags`

### 3. Hybrid (융합)
```
사용자: "밸류에이션 관련 페이지와 연결 관계"
→ semantic top-K → 각각의 1-hop neighborhood → fused result ✅
```

**적합:** 일반적/모호한 질문
**백엔드:** Vector search → graph traversal on top results → interleave + deduplicate

## Result Fusion (Hybrid)

```python
def hybrid_search(query, k=5):
    vec_results = semantic_search(query, k)     # 의미 기반
    struct_results = structural_search(query, k) # 구조 기반
    
    # Interleave: 번갈아가며 배치
    fused = []
    seen = set()
    for i in range(max(len(vec_results), len(struct_results))):
        if i < len(vec_results):
            r = vec_results[i]; r["match_type"] = "semantic"
            if r["id"] not in seen:
                fused.append(r); seen.add(r["id"])
        if i < len(struct_results):
            r = struct_results[i]; r["match_type"] = "structural"
            if r["id"] not in seen:
                fused.append(r); seen.add(r["id"])
    return fused[:k]
```

## Enrichment: Context Window

검색 결과에 **1-hop neighborhood**를 함께 제공:

```
사용자: "PER 분석 방법"
→ vector top-1: Methodology
    └ neighbors: Index, Agents (related links)
→ Or LLM이 Methodology.md full text + Index.md/Agents.md reference 읽음
```

이렇게 하면 단일 페이지 검색 결과로 끝나지 않고 **그래프 컨텍스트**까지 함께 제공.

## Pitfalls

- **hermes-logs** 페이지가 항상 높은 유사도를 보임 (로그 메시지에 키워드 풍부).
  → 실제 로그 vs wiki 페이지 구분이 필요하면 추후 repo 가중치 도입.
- **한국어 키워드 검출** — 형태소 분석 없이 substring match라 정확도 제한.
  '밸류'는 잡지만 '가치평가'는 못 잡을 수 있음. 필요 시 딕셔너리 확장.
- **hybrid deduplication** — semantic과 structural이 같은 페이지를 반환하면
  `seen` set으로 중복 제거하지만, score가 다른 문제는 아직 미해결.

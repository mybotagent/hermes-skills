#!/usr/bin/env python3
"""
Wiki Knowledge Search — Query Router
자연어 질문 → LLM 판단 → Neo4j Vector/Cypher → 결과 포매팅.

Usage:
  python3 query.py "PER 분석 방법 알려줘"
  python3 query.py --mode semantic "밸류에이션"
  python3 query.py --mode structural "Cron Jobs와 연결된 페이지"
"""
import os, sys, argparse, textwrap
sys.path.insert(0, os.path.expanduser("~/.venv-neo4j/lib/python*/site-packages"))
sys.path.insert(0, os.path.expanduser("~/hermes-wiki-super/.metagraph"))

from neo4j import GraphDatabase
from embed import embed_text, cosine_similarity

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
TOP_K = 5  # default results per query

# ──────────────────────────────────────────────
# Query Modes
# ──────────────────────────────────────────────

def semantic_search(query: str, k: int = TOP_K) -> list:
    """Vector similarity search. Best for concept/questions."""
    emb = embed_text(query)
    with GraphDatabase.driver(NEO4J_URI).session() as s:
        results = s.run("""
            CALL db.index.vector.queryNodes('page_emb', $k, $emb)
            YIELD node, score
            RETURN node.id AS id, node.title AS title,
                   node.repo AS repo, node.path AS path,
                   node.summary AS summary, score
        """, emb=emb, k=k)
        return [dict(r) for r in results]

def structural_search(query: str, k: int = TOP_K) -> list:
    """Graph traversal + tag filter. Best for relationship questions."""
    # Detect intent from query keywords
    keywords = {
        "valuation": ["per", "pbr", "밸류", "valuation", "가치", "궤도", "적정"],
        "infra": ["디스코드", "discord", "크론", "cron", "서버", "token", "토큰", "깃허브", "github"],
        "analysis": ["분석", "방법론", "methodology", "스크리닝", "screener", "랭그래프", "langgraph"],
        "trading": ["트레이딩", "파이프라인", "pipeline", "포트폴리오", "portfolio"],
        "wiki": ["wiki", "위키", "인덱스", "index", "스키마", "schema"],
    }

    matched_tags = []
    query_lower = query.lower()
    for tag, words in keywords.items():
        if any(w in query_lower for w in words):
            matched_tags.append(tag)

    with GraphDatabase.driver(NEO4J_URI).session() as s:
        if matched_tags:
            # Tag-based search + neighbors
            tag_condition = " OR ".join(f"'{t}' IN p.tags" for t in matched_tags)
            results = s.run(f"""
                MATCH (p:Page)-[r:LINKS*1..2]-(neighbor:Page)
                WHERE {tag_condition}
                RETURN DISTINCT p.id AS id, p.title AS title,
                       p.repo AS repo, p.path AS path,
                       p.summary AS summary,
                       count(DISTINCT neighbor) AS connections
                ORDER BY connections DESC LIMIT $k
            """, k=k)
        else:
            # Fallback: most connected pages
            results = s.run("""
                MATCH (p:Page)-[r:LINKS]-(neighbor:Page)
                RETURN p.id AS id, p.title AS title,
                       p.repo AS repo, p.path AS path,
                       p.summary AS summary,
                       count(DISTINCT neighbor) AS connections
                ORDER BY connections DESC LIMIT $k
            """, k=k)
        return [dict(r) for r in results]

def hybrid_search(query: str, k: int = TOP_K) -> list:
    """Vector + Graph combined. Best general purpose."""
    # Get semantic results
    vec_results = semantic_search(query, k)
    vec_ids = {r["id"] for r in vec_results}

    # Get structural results
    struct_results = structural_search(query, k)
    struct_ids = {r["id"] for r in struct_results}

    # Fuse: interleave, deduplicate
    fused = []
    seen = set()
    for i in range(max(len(vec_results), len(struct_results))):
        if i < len(vec_results):
            r = dict(vec_results[i])
            r["match_type"] = "semantic"
            if r["id"] not in seen:
                fused.append(r); seen.add(r["id"])
        if i < len(struct_results):
            r = dict(struct_results[i])
            r["match_type"] = "structural"
            if r["id"] not in seen:
                fused.append(r); seen.add(r["id"])
    return fused[:k]

def context_query(page_id: str) -> list:
    """Get 1-hop neighborhood for a specific page (provenance context)."""
    with GraphDatabase.driver(NEO4J_URI).session() as s:
        results = s.run("""
            MATCH (p:Page {id: $id})-[r:LINKS]-(neighbor:Page)
            RETURN DISTINCT neighbor.id AS id, neighbor.title AS title,
                   neighbor.repo AS repo, neighbor.path AS path,
                   neighbor.summary AS summary,
                   r.type AS rel_type
            LIMIT 10
        """, id=page_id)
        return [dict(r) for r in results]

# ──────────────────────────────────────────────
# Query Router (auto-detect mode)
# ──────────────────────────────────────────────

def detect_mode(query: str) -> str:
    """Auto-detect best query mode from question."""
    q = query.lower()
    # Relationship questions -> structural
    if any(w in q for w in ["연결", "관계", "관련", "링크", "연관", "함께", "같이", "리스트", "목록"]):
        return "structural"
    # Concept questions -> semantic
    if any(w in q for w in ["뭐", "무엇", "방법", "설명", "알려줘", "의미", "정의", "개념"]):
        return "semantic"
    # Default: hybrid
    return "hybrid"

def query_kb(question: str, mode: str = None) -> dict:
    """Main query entry point. Returns structured results."""
    if not mode:
        mode = detect_mode(question)

    print(f"🔍 Mode: {mode}", file=sys.stderr)

    if mode == "semantic":
        results = semantic_search(question)
    elif mode == "structural":
        results = structural_search(question)
    else:
        results = hybrid_search(question)

    # Enrich with 1-hop context for top results
    for r in results[:3]:
        r["neighbors"] = context_query(r["id"])

    return {
        "question": question,
        "mode": mode,
        "total": len(results),
        "results": results,
    }

# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Wiki Knowledge Search")
    parser.add_argument("query", nargs="?", help="질문")
    parser.add_argument("--mode", choices=["semantic", "structural", "hybrid"],
                        help="검색 모드 (기본: auto-detect)")
    parser.add_argument("--top-k", type=int, default=TOP_K)
    parser.add_argument("--json", action="store_true", help="JSON 출력")
    args = parser.parse_args()

    if not args.query:
        # Interactive mode
        while True:
            try:
                q = input("\n❓ 질문 (q=종료): ").strip()
                if q.lower() in ("q", "quit", "exit"): break
                if not q: continue
                result = query_kb(q, args.mode)
                print(format_results(result, json_output=args.json))
            except KeyboardInterrupt:
                break
        return

    result = query_kb(args.query, args.mode)
    print(format_results(result, json_output=args.json))

def format_results(data: dict, json_output=False) -> str:
    """Format query results for display."""
    if json_output:
        import json
        return json.dumps(data, ensure_ascii=False, indent=2, default=str)

    lines = []
    lines.append(f"\n{'='*60}")
    lines.append(f"📌 {data['question']}")
    lines.append(f"🔍 Mode: {data['mode']}  |  검색결과: {data['total']}건")
    lines.append('='*60)

    for i, r in enumerate(data["results"], 1):
        lines.append(f"\n{i}. [{r['repo']}] {r['title']}")
        lines.append(f"   📄 {r['path']}")
        if r.get("score"):
            lines.append(f"   🎯 유사도: {r['score']:.3f}")
        if r.get("connections"):
            lines.append(f"   🔗 연결: {r['connections']}개")
        if r.get("match_type"):
            lines.append(f"   🏷 매칭: {r['match_type']}")
        summary = (r.get("summary") or "")[:150]
        if summary:
            lines.append(f"   {summary}...")
        # Show neighbors
        neighbors = r.get("neighbors", [])
        if neighbors:
            n_titles = [n["title"] for n in neighbors[:5]]
            lines.append(f"   └ 연결페이지: {', '.join(n_titles)}")

    lines.append(f"\n{'='*60}")
    return "\n".join(lines)

if __name__ == "__main__":
    main()

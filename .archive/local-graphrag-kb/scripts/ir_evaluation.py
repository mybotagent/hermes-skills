#!/usr/bin/env python3
"""
Paper-Standard IR Evaluation for GraphRAG Search Systems
-------------------------------------------------------
Computes MRR, MAP@k, nDCG@k, P@k, R@k, F1@k for any search system.

Usage:
  source ~/.venv-neo4j/bin/activate
  python3 ir_evaluation.py                   # Run with default test set
  python3 ir_evaluation.py --system new      # Evaluate only the new (universal) system
  python3 ir_evaluation.py --compare         # Compare old vs new (side-by-side)

Ground truth format (in TEST_SET):
  relevant: list of (title_keyword, grade) tuples
  - 3 = highly relevant (perfect)
  - 2 = partially relevant (related)
  - 1 = marginally relevant (mentions but not core)
  - 0 = not relevant (default)

Metrics (standard IR literature):
  - MRR (Mean Reciprocal Rank): 1/rank of first relevant result
  - MAP@5 (Mean Average Precision): precision at each relevant position, averaged
  - nDCG@5 (Normalized DCG): graded relevance, position-discounted
  - P@1, P@3, P@5: precision at top-k
  - R@5: recall at top-5
  - F1@5: harmonic mean of P@5 and R@5

Why this exists: Phase 6 transition revealed that Hit@3 alone hides real
differences. Old (keyword) and new (universal) systems tied 9/10 on Hit@3
but diverged massively on operational/maintenance dimensions. Use this
script to produce paper-quality evidence, not vibes-based comparison.
"""
import os, sys, time, json, math, argparse
sys.path.insert(0, os.path.expanduser("~/.venv-neo4j/lib/python*/site-packages"))
sys.path.insert(0, '/home/ubuntu/hermes-wiki-super/.metagraph')

# === Test set: query, intent, graded relevance ground truth ===
TEST_SET = [
    {
        "q": "PER 분석 방법",
        "intent": "valuation methodology",
        "relevant": [
            ("methodology", 3),
            ("orbit valuation", 3),
            ("stock rating", 2),
            ("post analyzer", 2),
            ("screener", 2),
            ("regime classification", 1),
        ]
    },
    {
        "q": "Claude Code 활용법",
        "intent": "how-to use claude code",
        "relevant": [
            ("claude code log", 3),
            ("claude code hooks", 3),
            ("claude code commands", 3),
            ("claude code hub", 2),
            ("dynamic workflow", 2),
            ("claude cowork", 2),
            ("ohmyclaudecode", 2),
            ("agent context techniques", 2),
        ]
    },
    {
        "q": "cron jobs에 연결된 페이지",
        "intent": "find connected pages",
        "relevant": [("cron jobs", 3), ("cron", 2)]
    },
    {
        "q": "AI Agent Bible",
        "intent": "comprehensive AI agent guide",
        "relevant": [
            ("toolformer", 3), ("multi-agent", 2), ("codeact", 3),
            ("react", 2), ("mcp", 2), ("a2a", 2), ("rag", 2), ("self-rag", 1),
        ]
    },
    {
        "q": "LangGraph 멀티에이전트",
        "intent": "langgraph multi-agent architecture",
        "relevant": [("langgraph graphrag", 3), ("architecture", 2), ("multi-agent", 2), ("moa", 1)]
    },
    {
        "q": "MCP 도구 프로토콜",
        "intent": "MCP protocol",
        "relevant": [("claude code mcp", 3), ("mcp", 2), ("anthropic", 1)]
    },
    {
        "q": "GraphRAG 지식 그래프",
        "intent": "graph RAG with neo4j",
        "relevant": [("neo4j-local", 3), ("langgraph graphrag", 3), ("graphrag", 2), ("design", 1)]
    },
    {
        "q": "oh my claude code 플러그인",
        "intent": "find OhMyClaudeCode plugin docs",
        "relevant": [("ohmyclaudecode", 3), ("ralph", 2), ("deep interview", 2), ("ultrawork", 1)]
    },
    {
        "q": "Subagent 디스패치 패턴",
        "intent": "subagent delegation pattern",
        "relevant": [("subagent", 3), ("kanban-codex", 2), ("subagent-driven", 3), ("delegat", 2)]
    },
    {
        "q": "github deploy workflow",
        "intent": "github workflow automation",
        "relevant": [("github", 2), ("workflow", 2), ("github-pr-workflow", 2)]
    },
]


def get_relevance(result, relevant_list):
    title = (result.get("title", "") + " " + result.get("path", "")).lower()
    grade = 0
    for kw, g in relevant_list:
        if kw.lower() in title:
            grade = max(grade, g)
    return grade


def dcg_at_k(grades, k):
    return sum((2**g - 1) / math.log2(i + 2) for i, g in enumerate(grades[:k]))


def ndcg_at_k(grades, k):
    dcg = dcg_at_k(grades, k)
    ideal = sorted(grades, reverse=True)[:k]
    idcg = dcg_at_k(ideal, k)
    return dcg / idcg if idcg > 0 else 0.0


def average_precision(grades, k):
    hits = 0
    sum_prec = 0.0
    for i, g in enumerate(grades[:k]):
        if g > 0:
            hits += 1
            sum_prec += hits / (i + 1)
    return sum_prec / hits if hits > 0 else 0.0


def reciprocal_rank(grades):
    for i, g in enumerate(grades):
        if g > 0:
            return 1.0 / (i + 1)
    return 0.0


def recall_at_k(grades, relevant_list, k):
    total_relevant = sum(1 for _, g in relevant_list if g > 0)
    if total_relevant == 0:
        return 0.0
    retrieved_relevant = sum(1 for g in grades[:k] if g > 0)
    return retrieved_relevant / total_relevant


def evaluate(results, relevant_list, k_max=5):
    grades = [get_relevance(r, relevant_list) for r in results]
    metrics = {
        "recip_rank": reciprocal_rank(grades),
        "map@5": average_precision(grades, k=5),
        "ndcg@5": ndcg_at_k(grades, k=5),
    }
    for k in [1, 3, 5]:
        top_k = grades[:k]
        relevant_retrieved = sum(1 for g in top_k if g > 0)
        metrics[f"p@{k}"] = relevant_retrieved / k
        metrics[f"r@{k}"] = recall_at_k(grades, relevant_list, k)
    metrics["f1@5"] = (
        2 * metrics["p@5"] * metrics["r@5"] /
        (metrics["p@5"] + metrics["r@5"])
        if (metrics["p@5"] + metrics["r@5"]) > 0 else 0.0
    )
    return metrics


def run_system(system_name, query):
    if system_name == "old":
        from neo4j import GraphDatabase
        NEO4J_URI = "bolt://localhost:7687"
        STRUCTURAL_KEYWORDS = {
            "valuation": ["per", "pbr", "밸류", "valuation", "가치", "궤도", "적정"],
            "infra":     ["디스코드", "discord", "크론", "cron", "서버", "token", "토큰", "깃허브", "github"],
            "analysis":  ["분석", "방법론", "methodology", "스크리닝", "screener", "랭그래프", "langgraph"],
            "trading":   ["트레이딩", "파이프라인", "pipeline", "포트폴리오", "portfolio"],
            "wiki":      ["wiki", "위키", "인덱스", "index", "스키마", "schema"],
        }
        matched = []
        q_lower = query.lower()
        for tag, words in STRUCTURAL_KEYWORDS.items():
            if any(w in q_lower for w in words):
                matched.append(tag)
        with GraphDatabase.driver(NEO4J_URI).session() as s:
            if matched:
                cond = " OR ".join(f"'{t}' IN p.tags" for t in matched)
                results = s.run(f"""
                    MATCH (p:Page)-[r:LINKS*1..2]-(neighbor:Page)
                    WHERE {cond}
                    RETURN DISTINCT p.id AS id, p.title AS title, p.repo AS repo,
                           p.path AS path, p.summary AS summary,
                           count(DISTINCT neighbor) AS connections
                    ORDER BY connections DESC LIMIT 5
                """)
            else:
                results = s.run("""
                    MATCH (p:Page)-[r:LINKS]-(neighbor:Page)
                    RETURN p.id AS id, p.title AS title, p.repo AS repo,
                           p.path AS path, p.summary AS summary,
                           count(DISTINCT neighbor) AS connections
                    ORDER BY connections DESC LIMIT 5
                """)
            return [dict(r) for r in results]
    else:
        sys.path.insert(0, '/home/ubuntu/hermes-wiki-super/.metagraph/skill')
        import query as new_query
        return new_query.query_kb(query).get("results", [])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--system", choices=["old", "new"], default=None)
    parser.add_argument("--compare", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    systems = ["old", "new"] if args.compare or args.system is None else [args.system]
    all_metrics = {s: [] for s in systems}

    for test in TEST_SET:
        for system in systems:
            results = run_system(system, test["q"])
            m = evaluate(results, test["relevant"])
            all_metrics[system].append(m)

    if args.json:
        out = {s: {k: sum(m[k] for m in ms) / len(ms) for k in ms[0]}
               for s, ms in all_metrics.items()}
        print(json.dumps(out, indent=2))
        return

    print(f"{'Metric':<12} | {'OLD (keyword)' :<16} | {'NEW (universal)':<18} | Delta")
    print("-" * 70)
    metric_names = ["recip_rank", "map@5", "ndcg@5", "p@1", "p@3", "p@5", "r@5", "f1@5"]
    for k in metric_names:
        o = sum(m[k] for m in all_metrics.get("old", [])) / max(len(all_metrics.get("old", [])), 1)
        n = sum(m[k] for m in all_metrics.get("new", [])) / max(len(all_metrics.get("new", [])), 1)
        delta = n - o
        sign = "UP" if delta > 0.01 else ("DOWN" if delta < -0.01 else "SAME")
        print(f"{k:<12} | {o:<16.3f} | {n:<18.3f} | {sign} {delta:+.3f}")

    print(f"\nTotal queries: {len(TEST_SET)}")
    print("Operational dimensions to ALSO report (don't rely on accuracy alone):")
    print("  - Hardcoded items to maintain (keywords/tags/namespaces)")
    print("  - New repo addition cost (manual vs auto)")
    print("  - Cross-language support (KR-only / EN-only / mixed)")
    print("  - Latency (ms per query)")


if __name__ == "__main__":
    main()

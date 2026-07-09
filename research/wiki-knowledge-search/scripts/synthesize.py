#!/usr/bin/env python3
"""
Wiki Knowledge Search — Result Synthesizer
Neo4j 검색 결과 → 자연어 요약 + provenance 포함.
"""
import json
from datetime import datetime

def synthesize(data: dict) -> str:
    """검색 결과를 읽기 좋은 자연어로 합성."""
    lines = []
    q = data["question"]
    mode = data["mode"]
    results = data["results"]

    lines.append(f"## Wiki Knowledge Search 결과")
    lines.append(f"")
    lines.append(f"> 질문: {q}")
    lines.append(f"> 검색모드: {mode} | 검색결과: {len(results)}건")
    lines.append(f"> {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")

    if not results:
        lines.append("❌ 검색 결과가 없습니다.")
        return "\n".join(lines)

    # Summarize findings
    lines.append("### 📊 요약")
    lines.append("")
    repos = set(r["repo"] for r in results)
    top_pages = [r["title"] for r in results[:3]]
    lines.append(f"- 관련 레포지토리: {', '.join(sorted(repos))}")
    lines.append(f"- 주요 페이지: {', '.join(top_pages)}")
    lines.append("")

    # Per-result detail
    lines.append("### 📄 상세 결과")
    lines.append("")

    for i, r in enumerate(results, 1):
        lines.append(f"**{i}. [{r['repo']}] {r['title']}**")
        lines.append("")
        if r.get("summary"):
            lines.append(f"   {r['summary']}")
            lines.append("")
        lines.append(f"   📍 `{r['path']}`")
        if r.get("score"):
            lines.append(f"   🎯 관련도: {r['score']:.2f}")
        if r.get("match_type"):
            lines.append(f"   🏷 매칭방식: {r['match_type']}")
        lines.append("")

        # Neighbors
        neighbors = r.get("neighbors", [])
        if neighbors:
            lines.append("   **연결된 페이지:**")
            for n in neighbors[:5]:
                lines.append(f"   • [{n['repo']}] {n['title']} → `{n['path']}`")
            lines.append("")

    # Provenance
    lines.append("---")
    lines.append(f"*Source: Neo4j GraphRAG (hermes-wiki-super) | {len(results)} results*")
    lines.append(f"*Query: `{q}`*")

    return "\n".join(lines)


def synthesize_short(results: list, question: str) -> str:
    """Simple one-line summary per result (for quick inline display)."""
    lines = [f"🔍 Wiki Search: {question}"]
    for r in results[:3]:
        repo = r.get("repo", "?")
        title = r.get("title", "?")
        score = r.get("score")
        score_str = f" ({score:.2f})" if score else ""
        lines.append(f"  • [{repo}] {title}{score_str}")
    if len(results) > 3:
        lines.append(f"  ... 외 {len(results)-3}건")
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    data = json.loads(sys.stdin.read())
    print(synthesize(data))

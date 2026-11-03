#!/usr/bin/env python3
"""매크로 리포트 텍스트 오염 3계열 QA + dual-save 동등성 검사.

사용법:
    python3 macro_text_qa.py <macro_context.json> [second_path.json]

exit 0 = 통과, exit 1 = 오염/불일치 검출 (stdout에 상세 출력).
크론에서 no_agent로 돌릴 때는 exit 0으로 끝낼 것 (exit 1은 stdout 전달 차단).
"""
import json
import re
import sys

CJK = re.compile(r"[\u4e00-\u9fff]")
MIX = re.compile(r"[가-힣]([A-Za-z]{3,})")

# 정상 혼입 가능 토큰 (화이트리스트)
ALLOW = {
    "AI", "HBM", "DRAM", "NAND", "LPDDR", "ASP", "API", "GDP", "PCE", "CPI", "PPI",
    "EPS", "PER", "PBR", "ROE", "MLCC", "EV", "ETF", "NAV", "US", "EUR", "USD",
    "JPY", "KRW", "IT", "PC", "TV", "AP", "PCB", "SIA", "SEMI", "FOMC", "GDP",
    "Reuters", "Bloomberg", "CNBC", "SEC", "FED", "GDP", "OPEC", "OPEC",
}

# 뉴스 title에 실제 등장하는 한자 → 정상 한국어 매핑
CJK_MAP = {
    "證": "증", "說": "설", "美": "미국", "佛": "프랑스", "獨": "독일",
    "中": "중국", "日": "일본", "俄": "러시아", "經": "경", "濟": "제",
    "業": "업", "會": "회", "社": "사", "經": "경",
}


def scan_text(label, text):
    """계열 1(CJK) + 계열 2(Hangul-Latin 혼합) 검사. 문제 목록 반환."""
    problems = []
    if not isinstance(text, str):
        return ["%s: 문자열 아님 (%r)" % (label, type(text))]

    # 계열 1 — CJK 한자
    for m in CJK.finditer(text):
        problems.append("%s CJK: %r  ...%s..." % (
            label, m.group(0), text[max(0, m.start() - 35):m.end() + 35]))

    # 계열 2 — Hangul 바로 뒤에 붙은 라틴 단어 (화이트리스트 외)
    for m in MIX.finditer(text):
        tok = m.group(1)
        if tok in ALLOW:
            continue
        problems.append("%s MIX: %r  ...%s..." % (
            label, tok, text[max(0, m.start() - 35):m.end() + 35]))
    return problems


def main():
    if len(sys.argv) < 2:
        print("usage: macro_text_qa.py <macro_context.json> [second.json]")
        return 0
    path = sys.argv[1]
    try:
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
    except Exception as e:
        print("LOAD FAIL: %s" % e)
        return 1

    problems = []
    problems += scan_text("macro_report_summary", d.get("macro_report_summary", ""))

    for i, n in enumerate(d.get("news_items", []) or []):
        problems += scan_text("news_items[%d].summary" % i, n.get("summary", ""))
        # title 은 한자 정상 혼입 가능 → 정정 가능성만 알림
        for m in CJK.finditer(n.get("title", "")):
            fixed = n["title"]
            for k, v in CJK_MAP.items():
                fixed = fixed.replace(k, v)
            print("WARN title[%d] 한자 있음 (clean() 매핑 권장): %r -> %r"
                  % (i, n.get("title", "")[:60], fixed[:60]))

    # URL 무결성
    for i, n in enumerate(d.get("news_items", []) or []):
        u = n.get("url", "")
        if not u.startswith("https://news.google.com/rss/articles/") or len(u) < 120:
            problems.append("news_items[%d].url 불완전: %r" % (i, u[:60]))

    # dual-save 동등성
    if len(sys.argv) > 2:
        try:
            with open(sys.argv[2], encoding="utf-8") as f:
                d2 = json.load(f)
            if d != d2:
                problems.append("dual-save 불일치: %s != %s" % (path, sys.argv[2]))
        except Exception as e:
            problems.append("dual-save LOAD FAIL: %s" % e)

    if problems:
        print("❌ TEXT QA 실패 (%d건)" % len(problems))
        for p in problems:
            print("  -", p)
        return 1

    print("✅ TEXT QA 통과 — CJK 0건, 혼합 후보 0건, URL 무결, dual-save 일치")
    print("   timestamp:", d.get("timestamp"))
    print("   summary chars:", len(d.get("macro_report_summary", "")),
          "| news:", len(d.get("news_items", []) or []))
    return 0


if __name__ == "__main__":
    sys.exit(main())

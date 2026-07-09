#!/usr/bin/env python3
"""
verdict_analyzer.py — read-only PR verdict 분석기 (자가개선 기초 자료).

review-bot이 박은 **Verdict:** X 코멘트 + 🔴/🟠/🟡/⚪ severity 출현 횟수 +
반복 지적 keyword를 PR 코멘트 전체에서 집계 → stdout + json dump.

SAFE: read-only. PR/Pull Request 코멘트 GET 만 사용. push/mutation 일절 없음.

사용법:
    python3 verdict_analyzer.py mybotagent/hermes-pr-gate mybotagent/mybotagent.github.io
    (인자 없으면 기본 4개 repo)
"""
from __future__ import annotations
import json, os, re, sys, urllib.request, datetime as dt
from pathlib import Path
from collections import Counter

HERMES_HOME = Path(os.environ.get("HERMES_HOME", "/home/ubuntu/.hermes"))
ENV_FILE = HERMES_HOME / ".env"


def get_env_var(name: str) -> str:
    if name in os.environ:
        return os.environ[name]
    try:
        with open(ENV_FILE) as f:
            for line in f:
                m = re.match(rf"^{name}=(.*)$", line.strip())
                if m:
                    return m.group(1).strip().strip('"')
    except FileNotFoundError:
        pass
    return ""


GITHUB_TOKEN = get_env_var("GITHUB_TOKEN")
HEADERS_GH = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "User-Agent": "hermes-bot/1.0",
}


def gh_paged(path: str) -> list:
    """Pagination 자동 follow."""
    results = []
    url = f"https://api.github.com{path}"
    while url:
        req = urllib.request.Request(url, headers=HEADERS_GH)
        with urllib.request.urlopen(req, timeout=15) as r:
            chunk = json.loads(r.read())
            link = r.headers.get("Link", "")
        if isinstance(chunk, list):
            results.extend(chunk)
        else:
            results.append(chunk)
        next_url = None
        for part in link.split(","):
            if 'rel="next"' in part:
                next_url = part.split("<")[1].split(">")[0]
        url = next_url
    return results


def analyze_verdicts(repos: list[str]) -> dict:
    findings = {
        "repos_scanned": 0,
        "prs_analyzed": 0,
        "verdicts": Counter({"Approve": 0, "Changes Requested": 0, "Blocked": 0, "Other": 0}),
        "severity_counts": Counter({"🔴": 0, "🟠": 0, "🟡": 0, "⚪": 0}),
        "issue_keywords": Counter(),
    }
    verdict_re = re.compile(r"\*\*Verdict:\*\*\s*(\w[\w ]*?)(?:\s|$|\n)", re.M)
    sev_re = re.compile(r"(🔴|🟠|🟡|⚪)")
    keyword_re = re.compile(
        r"(?i)\b(workflow|review|trusted|secret|fix|test|ci|leak|token|sanity|"
        r"changelog|copyright|license|refactor|api[_ ]?key|retire|deprecated)\b"
    )

    for repo in repos:
        findings["repos_scanned"] += 1
        try:
            prs = gh_paged(
                f"/repos/{repo}/pulls?state=all&per_page=20&sort=updated&direction=desc"
            )
        except Exception:
            continue
        for pr in prs:
            if not isinstance(pr, dict):
                continue
            pr_num = pr.get("number")
            if not pr_num:
                continue
            findings["prs_analyzed"] += 1
            try:
                comments = gh_paged(f"/repos/{repo}/issues/{pr_num}/comments?per_page=50")
            except Exception:
                continue
            for c in comments:
                body = (c.get("body") or "")
                if "**Verdict:**" not in body and "🔴" not in body:
                    continue
                v_match = verdict_re.search(body)
                if v_match:
                    label = v_match.group(1).strip()
                    findings["verdicts"][label if label in findings["verdicts"] else "Other"] += 1
                for sm in sev_re.finditer(body):
                    findings["severity_counts"][sm.group(1)] += 1
                words = set(m.group(0).lower() for m in keyword_re.finditer(body))
                for w in words:
                    findings["issue_keywords"][w] += 1
    return findings


def report(findings: dict) -> str:
    lines = [
        f"[Hermes Verdict Analyzer] {dt.date.today()}",
        "",
        f"Repos scanned: {findings['repos_scanned']}",
        f"PRs analyzed: {findings['prs_analyzed']}",
        "",
        "## Verdict distribution",
        *[f"- {k}: {v}" for k, v in findings["verdicts"].items() if v],
        "",
        "## Severity frequency",
        *[f"- {k}: {v}" for k, v in findings["severity_counts"].items() if v],
        "",
        "## Top issue keywords (top 15)",
        *[f"- {k}: {v}" for k, v in findings["issue_keywords"].most_common(15)],
    ]
    return "\n".join(lines)


DEFAULT_REPOS = [
    "mybotagent/hermes-pr-gate",
    "mybotagent/mybotagent.github.io",
    "mybotagent/hermes-wiki-super",
    "mybotagent/hermes-stock-briefings",
]


if __name__ == "__main__":
    repos = sys.argv[1:] or DEFAULT_REPOS
    findings = analyze_verdicts(repos)
    print(report(findings))
    log_dir = HERMES_HOME / "scripts" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    today = dt.date.today().isoformat()
    out = {k: dict(v) if hasattr(v, "items") else v for k, v in findings.items()}
    with (log_dir / f"verdict-analyzer-{today}.json").open("w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

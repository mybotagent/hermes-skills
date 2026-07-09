#!/usr/bin/env python3
"""
verdict_analyzer.py — read-only 자가개선 분석기.

PR review-bot verdict 코멘트를 GitHub에서 읽고 자주 나오는 패턴
(🔴/🟠/🟡 verdict 비율, 자주 지적되는 라인/주제)을 빈도 순으로 출력.
wiki/skill 자동 제안용 기초 자료. SAFE: read-only.
"""
from __future__ import annotations
import json, os, re, sys, urllib.request, datetime as dt
from pathlib import Path
from collections import Counter

_HH = os.environ.get("HERMES_HOME", "/home/ubuntu")
HERMES_HOME = Path(_HH) if _HH.endswith("/.hermes") else Path(_HH) / ".hermes"
ENV_FILE = HERMES_HOME / ".env"


def get_env_var(name):
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


def gh(path: str) -> list:
    url = f"https://api.github.com{path}"
    req = urllib.request.Request(url, headers=HEADERS_GH)
    out = []
    while url:
        with urllib.request.urlopen(req, timeout=15) as r:
            chunk = json.loads(r.read())
        out.extend(chunk if isinstance(chunk, list) else [chunk])
        link = req.headers.get("Link", "")  # Python urllib은 request headers 못 읽음. next link 파싱 별도 필요.
        # GitHub pagination: Link 헤더의 next URL
        next_url = None
        # urllib의 response object에서 headers 읽기
        # 위 urlopen은 req.headers가 아닌 response.headers임
        break
    return out


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


def analyze_verdicts(repos: list[str], since: str = "2026-06-01") -> dict:
    """각 repo의 PR 코멘트 중 verdict 코멘트만 분석."""
    since_dt = dt.datetime.fromisoformat(since)
    findings = {
        "repos_scanned": 0,
        "prs_analyzed": 0,
        "verdicts": Counter({"Approve": 0, "Changes Requested": 0, "Blocked": 0, "Other": 0}),
        "severity_counts": Counter({"🔴": 0, "🟠": 0, "🟡": 0, "⚪": 0}),
        "issue_keywords": Counter(),
        "examples_per_repo": {},
    }
    verdict_re = re.compile(r"\*\*Verdict:\*\*\s*(\w[\w ]*?)(?:\s|$|\n)", re.M)
    sev_re = re.compile(r"(🔴|🟠|🟡|⚪)\s*(\w+)?\s*:?\s*(.+)")
    keyword_re = re.compile(r"(?i)(retire|deprecated|leak|secret|token|api[_ ]?key|sanity|changelog|copyright|license|workflow|secret|ci |pr|workflow|trusted|review|test|fix|feat|refactor)", re.U)

    for repo in repos:
        findings["repos_scanned"] += 1
        try:
            prs = gh_paged(f"/repos/{repo}/pulls?state=all&per_page=20&sort=updated&direction=desc")
        except Exception as e:
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
                # only hermes-bot verdicts
                if "**Verdict:**" not in body and "🔴" not in body and "🟠" not in body:
                    continue
                v_match = verdict_re.search(body)
                if v_match:
                    label = v_match.group(1).strip()
                    findings["verdicts"][label if label in findings["verdicts"] else "Other"] += 1
                # severity
                for sm in sev_re.finditer(body):
                    findings["severity_counts"][sm.group(1)] += 1
                # 키워드 카운트 (단어 단위)
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
        *(f"- {k}: {v}" for k, v in findings["verdicts"].items() if v),
        "",
        "## Severity frequency (이슈 icon 카운트)",
        *(f"- {k}: {v}" for k, v in findings["severity_counts"].items() if v),
        "",
        "## Top issue keywords (반복 지적 패턴)",
        *(f"- {k}: {v}" for k, v in findings["issue_keywords"].most_common(15)),
    ]
    return "\n".join(lines)


# default repositories — 사용자/사용자 사이트 영역
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
    # log 저장
    log_dir = HERMES_HOME / "scripts" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    today = dt.date.today().isoformat()
    with (log_dir / f"verdict-analyzer-{today}.json").open("w") as f:
        json.dump({k: dict(v) if hasattr(v, "items") else v
                   for k, v in findings.items()}, f, indent=2, ensure_ascii=False)

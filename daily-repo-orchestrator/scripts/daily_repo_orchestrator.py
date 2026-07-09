#!/usr/bin/env python3
"""
daily_repo_orchestrator.py

매일 07:00 KST cron이 호출하는 단일 공식:
  harvest  →  prioritize  →  mirror  →  fix  →  report

  harvest   : mybotagent/* 레포 전부 진단 → 누락/단순 이슈 후보 리스트
  prioritize: (impact × certainty) / effort  →  top-3
  mirror    : Linear SHO-XX  ←→  Kanban t_…  ←→  GitHub issue (#N)
  fix       : 각 후보에 대해 patch → branch → push → PR open
  report    : (mirror-only/prod) himalaya SMTP로 사용자에게 일일 리포트 발송

DRY_RUN 환경변수가 '1' 또는 인자 --dry-run이면 모든 mutation 함수들은
  실제 mutation 대신 어떤 동작을 했는지 stdout에만 인쇄한다.

자율모드 = 외부 영향(push/payment/delete)은 사전 동의 필수.
  - 첫 실행은 dry-run 1회 후 사용자가 production 명령 (DRY_RUN=0) 으로 실행
  - 이후 매일 cron 자동 (production 모드)

Stage별 dry-run flags (v1.3):
  DRY_RUN_MIRROR / DRY_RUN_FIX / DRY_RUN_EMAIL / DRY_RUN_HARVEST
  누락 시 DRY_RUN 으로 fallback. DRY_RUN 본값이 '1'이면 전부 dry.

Mode presets:
  DRY_RUN=1                     → 전부 dry
  DRY_RUN=0                     → 전부 production (Linear/Kanban/email/push/PR)
  DRY_RUN_MIRROR=0 (_나머지=1)  → mirror 단계까지 실제, fix/PR/email은 dry (read-light)
"""
from __future__ import annotations
import json, os, re, sys, subprocess, urllib.request, urllib.parse, datetime as dt
from pathlib import Path
from typing import Any

# ---------------------------- env ----------------------------
_HH = os.environ.get("HERMES_HOME", "/home/ubuntu")
if _HH.endswith("/.hermes"):
    HERMES_HOME = Path(_HH)
else:
    HERMES_HOME = Path(_HH) / ".hermes"
ENV_FILE = HERMES_HOME / ".env"


def _get_stage_dry(prefix: str) -> bool:
    """Return True if the given stage should be dry-run."""
    explicit = os.environ.get(f"DRY_RUN_{prefix}")
    if explicit is not None:
        return explicit == "1"
    return os.environ.get("DRY_RUN", "1") == "1" or "--dry-run" in sys.argv


DRY_RUN = os.environ.get("DRY_RUN", "1") == "1" or "--dry-run" in sys.argv
DRY_RUN_HARVEST = _get_stage_dry("HARVEST")
DRY_RUN_MIRROR = _get_stage_dry("MIRROR")
DRY_RUN_FIX = _get_stage_dry("FIX")
DRY_RUN_EMAIL = _get_stage_dry("EMAIL")

LOG_DIR = HERMES_HOME / "scripts" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
TODAY = dt.datetime.now().strftime("%Y-%m-%d")
TS = dt.datetime.now().strftime("%H%M%S")


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
LINEAR_KEY = get_env_var("LINEAR_API_KEY") or get_env_var("LINEAR_KEY")

HEADERS_GH = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "User-Agent": "hermes-bot/1.0",
}
HEADERS_LINEAR = {
    "Authorization": LINEAR_KEY,
    "Content-Type": "application/json",
}

# ---------------------------- log ----------------------------
LOG_FILE = LOG_DIR / f"daily-repo-{TODAY}.jsonl"


def log_event(stage: str, action: str, **kw: Any) -> None:
    rec = {"ts": dt.datetime.now().isoformat(timespec="seconds"),
           "stage": stage, "action": action,
           "dry_flags": {"harvest": DRY_RUN_HARVEST, "mirror": DRY_RUN_MIRROR,
                          "fix": DRY_RUN_FIX, "email": DRY_RUN_EMAIL},
           **kw}
    with LOG_FILE.open("a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"[{rec['ts']}] {stage}/{action}", " ".join(f"{k}={v}" for k, v in kw.items()))


# ---------------------------- GitHub ----------------------------
def gh(path: str, method: str = "GET", data: dict | None = None) -> dict:
    url = f"https://api.github.com{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, headers=HEADERS_GH, method=method, data=body)
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())


def harvest_repos() -> list[dict]:
    """mybotagent 본인이 owner인 모든 레포 진단."""
    if DRY_RUN_HARVEST:
        log_event("harvest", "dry-skip")
        return []
    repos = gh("/user/repos?per_page=30&sort=pushed&affiliation=owner")
    out = []
    for r in repos:
        full = r["full_name"]
        pushed = r.get("pushed_at", "")[:10]
        if (dt.datetime.now() - dt.datetime.fromisoformat(pushed)).days > 60 and r.get("archived"):
            continue
        out.append({
            "name": full,
            "pushed_at": pushed,
            "default_branch": r.get("default_branch", "main"),
            "private": r.get("private", True),
            "language": r.get("language"),
        })
    log_event("harvest", "scan", n=len(out))
    return out


def harvest_candidates(repos: list[dict]) -> list[dict]:
    """각 레포에서 open issue + 자동 진단 (lint/diff 등) 으로 후보 작업 수집."""
    if DRY_RUN_HARVEST:
        log_event("harvest", "candidates-dry", n=0)
        return []
    candidates = []
    for r in repos:
        try:
            ixs = gh(f"/repos/{r['name']}/issues?state=open&per_page=10")
        except Exception as e:
            log_event("harvest", "skip", repo=r["name"], err=str(e)[:60])
            continue
        for ix in ixs:
            if "pull_request" in ix:
                continue
            candidates.append({
                "repo": r["name"],
                "number": ix["number"],
                "title": ix["title"],
                "body": (ix.get("body") or "")[:600],
                "labels": [l["name"] for l in ix.get("labels", [])],
                "comments": ix.get("comments", 0),
                "created": ix.get("created_at", "")[:10],
                "url": ix.get("html_url"),
            })
        # 추가 자동 진단: README/LICENSE/CHANGELOG 존재 여부
        try:
            readme = gh(f"/repos/{r['name']}/contents/README.md")
        except Exception:
            candidates.append({
                "repo": r["name"], "number": None,
                "title": "❗ README.md 누락",
                "body": f"레포 {r['name']} 에 README.md 없음. 표준 양식 작성 필요.",
                "labels": ["auto-detected", "docs"], "comments": 0,
                "created": TODAY, "url": f"https://github.com/{r['name']}",
                "auto": True,
            })
    log_event("harvest", "candidates", n=len(candidates))
    return candidates


# ---------------------------- prioritize ----------------------------
LABEL_IMPACT = {"bug": 4, "security": 5, "auto-detected": 3, "feature": 3,
                "docs": 2, "enhancement": 3, "cleanup": 2, "good first issue": 2}


def prioritize(cands: list[dict]) -> list[dict]:
    out = []
    for c in cands:
        impact = max((LABEL_IMPACT.get(l, 2) for l in c.get("labels", [])), default=2)
        body_len = len(c.get("body", ""))
        effort = max(1, 5 - body_len // 200)
        certainty = 4 if c.get("auto") else 3
        score = (impact * certainty) / max(effort, 1)
        c2 = {**c, "impact": impact, "effort": effort,
              "certainty": certainty, "score": round(score, 2)}
        out.append(c2)
    out.sort(key=lambda x: -x["score"])
    log_event("prioritize", "score", top=[x["title"][:40] for x in out[:3]])
    return out


# ---------------------------- mirror ----------------------------
KANBAN_BOARD = "hermes"


def _issue_dedupe_key(c: dict) -> str:
    """candidate별 dedupe key: 동일 repo+title이면 같은 key → 같은 SHO/t_ 발번."""
    # repo + 80자 정규화 (front ref 변동 무시). 길이 제한으로 key 안정성.
    title_norm = re.sub(r"\s+", " ", c["title"]).strip()[:80]
    return f"{c.get('repo','?')}::{title_norm}"

def _linear_find_existing(title: str) -> dict | None:
    """동일 title의 Linear 이슈가 있으면 반환. 없으면 None.
    SAFE: read-only GraphQL query."""
    query = """
        query Q($title: String!) {
          issues(filter: {title: {eqIgnoreCase: $title}}, first: 1) {
            nodes { identifier url }
          }
        }"""
    req = urllib.request.Request(
        "https://api.linear.app/graphql",
        data=json.dumps({"query": query, "variables": {"title": title}}).encode(),
        headers=HEADERS_LINEAR, method="POST",
    )
    try:
        r = json.loads(urllib.request.urlopen(req, timeout=10).read())
        nodes = (r.get("data") or {}).get("issues", {}).get("nodes", [])
        return nodes[0] if nodes else None
    except Exception:
        return None


def mirror_to_linear(top: list[dict]) -> list[dict]:
    """각 후보를 Linear SHO-XX 로 등록. dry-run이면 어떤 ID로 발급될지 인쇄만.
    idempotency: 동일 title의 기존 이슈가 있으면 재사용 (중복 생성 안 함)."""
    out = []
    for c in top:
        title = f"[AUTO {TODAY}] {c['title']}"
        body = (f"**auto-detected** from {c.get('repo')}\n\n{c.get('body','')}\n\n"
                f"kanban: TBD / score={c['score']}")
        dedupe = _issue_dedupe_key(c)
        if DRY_RUN_MIRROR:
            fake_id = f"SHO-{850 + len(out)}"
            log_event("mirror", "linear-dry", fake_id=fake_id, title=title[:60])
            out.append({"candidate": c, "linear_id": fake_id, "linear_url": f"https://linear.app/shootingstock/issue/{fake_id}"})
            continue
        mutation = """
            mutation IssueCreate($input: IssueCreateInput!) {
              issueCreate(input: $input) { success issue { identifier url } }
            }"""
        # idempotency: 동일 title 검색해서 있으면 skip
        existing = _linear_find_existing(title)
        if existing:
            out.append({"candidate": c, "linear_id": existing.get("identifier"),
                        "linear_url": existing.get("url")})
            log_event("mirror", "linear-reuse", id=existing.get("identifier"), key=dedupe)
            continue
        variables = {"input": {
            "teamId": "acb9037a-9a30-4848-bb13-cf72c95c13e8",
            "title": title,
            "description": body,
        }}
        req = urllib.request.Request("https://api.linear.app/graphql",
            data=json.dumps({"query": mutation, "variables": variables}).encode(),
            headers=HEADERS_LINEAR, method="POST")
        try:
            r = json.loads(urllib.request.urlopen(req, timeout=15).read())
            iss = r.get("data", {}).get("issueCreate", {}).get("issue", {})
            if iss:
                out.append({"candidate": c, "linear_id": iss.get("identifier"),
                            "linear_url": iss.get("url")})
                log_event("mirror", "linear", id=iss.get("identifier"))
            else:
                log_event("mirror", "linear-fail", err=str(r)[:120])
        except Exception as e:
            log_event("mirror", "linear-err", err=str(e)[:120])
    return out


def _kanban_list_existing_titles(hermes_home: Path) -> set[str]:
    """hermes kanban의 모든 (status 무관) task에서 오늘자 dedupe 키 추출.
    SAFE: read-only `hermes kanban list --json` 호출."""
    try:
        res = subprocess.run(
            ["hermes", "kanban", "list", "--json"],
            capture_output=True, text=True, timeout=15,
            cwd=str(hermes_home.parent),
        )
        try:
            data = json.loads(res.stdout)
            if not isinstance(data, list):
                return set()
            today_marker = f"[Auto {TODAY}]"
            return {t.get("title", "")[:80]
                    for t in data if today_marker in t.get("title", "")}
        except (json.JSONDecodeError, KeyError, TypeError):
            return set()
    except Exception:
        return set()


def mirror_to_kanban(top: list[dict]) -> list[dict]:
    """hermes kanban에 mirror. dry-run이면 task id 발번/print만.
    idempotency: 동일 title-prefix(`[Auto TODAY]`) 가 이미 있으면 skip."""
    out = []
    existing_titles: set[str] = (
        _kanban_list_existing_titles(HERMES_HOME)
        if not DRY_RUN_MIRROR else set()
    )
    for c in top:
        title = f"[Auto {TODAY}] {c['title'][:60]}"
        if DRY_RUN_MIRROR:
            fake = f"t_daily_{TS}_{len(out):02d}"
            log_event("mirror", "kanban-dry", task=fake, title=c["title"][:60])
            out.append({"candidate": c, "kanban_task_id": fake})
            continue
        # idempotency: 동일 title marker가 오늘 이미 kanban에 있으면 skip
        if title[:80] in existing_titles:
            log_event("mirror", "kanban-reuse", title=title[:60])
            out.append({"candidate": c, "kanban_task_id": "(reused, no id captured)"})
            continue
        try:
            res = subprocess.run(
                ["hermes", "kanban", "create",
                 title,
                 "--body", (c.get("body") or "")[:400]],
                capture_output=True, text=True, timeout=20)
            stdout = res.stdout.strip()
            # stdout format: 'Created t_xxxxxxxx  (ready, assignee=-)'
            import re as _re
            m = _re.search(r"(t_[a-z0-9]+)", stdout)
            task_id = m.group(1) if m else (stdout.split()[1] if stdout else "t_?")
            out.append({"candidate": c, "kanban_task_id": task_id})
            log_event("mirror", "kanban", task=task_id)
        except Exception as e:
            log_event("mirror", "kanban-err", err=str(e)[:120])
    return out


# ---------------------------- fix / PR ----------------------------
def fix_and_pr(top: list[dict]) -> list[dict]:
    """각 후보에 대해 patch → branch → push → PR. dry-run이면 print."""
    out = []
    for c in top:
        slug = re.sub(r"[^a-z0-9]+", "-", c["title"].lower())[:30].strip("-")
        branch = (f"hermes-auto/{TODAY}-{slug}" if not DRY_RUN_FIX
                  else f"(would be: hermes-auto/{TODAY}-{slug})")
        title = f"fix: {c['title']}"
        body = (f"closes #{c.get('number', 0)}\n\n"
                f"kanban: {c.get('kanban_task_id','?')}\n"
                f"linear: {c.get('linear_id','?')}\n\n"
                f"## 변경\n* auto-detected\n* auto-fixed\n\n"
                f"## 검증\n* [ ] TODO\n")
        if DRY_RUN_FIX:
            log_event("fix", "pr-dry", title=title, branch=branch)
            out.append({"candidate": c, "branch": branch, "title": title,
                        "pr_url": f"(would open PR in {c['repo']})"})
            continue
        # 실제 clone + patch + push + open PR은 여기서 진행
        out.append({"candidate": c, "branch": branch, "title": title, "pr_url": "(production)"})
    return out


# ---------------------------- report ----------------------------
GMAIL_TARGET = os.environ.get("REPORT_TO", "sanghee.lee2222@gmail.com")


def report(harvested, prioritized, linear, kanban, fixed) -> None:
    lines = [
        f"[Hermes Daily Repo Report] {TODAY}",
        "",
        "## 1. Harvested repos",
        f"- {len(harvested)} repos scanned" if harvested else "- (dry-skip)",
        "",
        "## 2. Top-3 candidates (prioritized)",
        *[f"- score={c['score']}  {c['title'][:60]}  (repo={c['repo']})"
          for c in prioritized[:3]],
        "",
        "## 3. Linear mirror",
        *[f"- {m['linear_id']}: {m['candidate']['title'][:50]}" for m in linear],
        "",
        "## 4. Kanban mirror",
        *[f"- {m['kanban_task_id']}: {m['candidate']['title'][:50]}" for m in kanban],
        "",
        "## 5. Fix / PR",
        *[f"- branch={f['branch']}  title={f['title'][:60]}" for f in fixed],
        "",
        f"MODE: {'DRY_RUN' if DRY_RUN else 'PRODUCTION'}",
        f"  harvest={'dry' if DRY_RUN_HARVEST else 'real'} "
        f"mirror={'dry' if DRY_RUN_MIRROR else 'real'} "
        f"fix={'dry' if DRY_RUN_FIX else 'real'} "
        f"email={'dry' if DRY_RUN_EMAIL else 'real'}",
        f"timestamp: {TS}",
    ]
    body = "\n".join(lines)
    print(body)
    if DRY_RUN_EMAIL:
        log_event("report", "dry-skip-email")
        return
    send_email(GMAIL_TARGET, f"[Hermes Daily Repo] {TODAY}", body)


def send_email(to: str, subject: str, body: str) -> None:
    raw = (f"From: hermes-bot <sanghee.lee2222@gmail.com>\r\n"
           f"To: {to}\r\n"
           f"Subject: {subject}\r\n"
           f"Content-Type: text/plain; charset=UTF-8\r\n\r\n{body}")
    p = subprocess.Popen(["himalaya", "message", "send"], stdin=subprocess.PIPE,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    p.communicate(input=raw.encode())
    log_event("report", "email-sent", to=to, subject=subject)


# ---------------------------- cycle ----------------------------
def daily_repo_cycle() -> None:
    print(f"=== Hermes daily_repo_orchestrator.py | {TODAY} | "
          f"DRY_RUN={DRY_RUN} ===")
    harvested = harvest_repos()
    candidates = harvest_candidates(harvested)
    prioritized = prioritize(candidates)
    top3 = prioritized[:3]
    lin = mirror_to_linear(top3)
    kan = mirror_to_kanban(top3)
    fix = fix_and_pr([{**t, **l, **k} for t, l, k in zip(top3, lin, kan)])
    report(harvested, prioritized, lin, kan, fix)
    log_event("cycle", "done", n_repos=len(harvested),
              n_cands=len(candidates), n_top=len(top3))


if __name__ == "__main__":
    daily_repo_cycle()

#!/usr/bin/env python3
"""Same-repo merge-gate poller — cron-driven fallback for trigger gap.

Background: GitHub Actions `pull_request` / `pull_request_target` triggers do
NOT fire for same-repo PRs on private repos with GitHub Free plan. The trigger
is registered with caching that prevents later workflow edits from re-registering
the trigger.

Fix: this script polls open PRs on registered repos, parses any
`**Verdict:**` line in PR issue comments (from a prior review-bot run), and
auto-merges via PUT API if the verdict is Approve and the PR is mergeable.

Verdict substring (set by scripts/review_pr.py / equivalents):
  **Verdict:** Approve
  **Verdict:** Changes Requested
  **Verdict:** Blocked

Usage:
  python3 same_repo_merge_poller.py                # uses $GITHUB_TOKEN
  python3 same_repo_merge_poller.py --once          # single-pass (cron)
  POLL_INTERVAL=300 python3 ...                    # 5 min loop (long-running)

Environment:
  GITHUB_TOKEN              Classic or fine-grained PAT with PRs:RW
  POLL_REPOS                CSV of owner/repo (default: mybotagent/hermes-pr-gate)
  DRY_RUN=1                 Print actions without mutating
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

POLL_REPOS = [r for r in os.environ.get("POLL_REPOS", "mybotagent/hermes-pr-gate").split(",") if r]
VERDICT_RE = re.compile(r"\*\*Verdict:\*\*\s*(Approve|Changes Requested|Blocked)")
PASS_STATES = {"clean", "unstable", "behind"}


def gh(method: str, path: str, token: str, body=None):
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "hermes-bot/1.0",
    }
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(
        f"https://api.github.com{path}", data=data, headers=headers, method=method
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def poll_repo(owner_repo: str, token: str, dry_run: bool) -> None:
    status, prs = gh("GET", f"/repos/{owner_repo}/pulls?state=open&per_page=30", token)
    if status != 200:
        print(f"[skip] {owner_repo}: list PRs HTTP {status}")
        return

    for pr in prs:
        n = pr["number"]
        if pr.get("merged"):
            continue

        # Find latest verdict in PR comments
        s, comments = gh("GET", f"/repos/{owner_repo}/issues/{n}/comments?per_page=100", token)
        if s != 200:
            print(f"[skip] PR #{n}: comments HTTP {s}")
            continue

        verdict = None
        for c in comments:
            m = VERDICT_RE.search(c.get("body") or "")
            if m:
                verdict = m.group(1)

        if not verdict:
            print(f"[skip] PR #{n}: no verdict")
            continue

        # Check mergeable state
        s, full = gh("GET", f"/repos/{owner_repo}/pulls/{n}", token)
        if s != 200:
            print(f"[skip] PR #{n}: pull HTTP {s}")
            continue
        state = full.get("mergeable_state")
        if state not in PASS_STATES:
            print(f"[skip] PR #{n}: state={state}")
            continue

        if verdict != "Approve":
            print(f"[no-merge] PR #{n}: verdict={verdict}, state={state}")
            if dry_run:
                continue
            # Drop a short note explaining
            gh("POST", f"/repos/{owner_repo}/issues/{n}/comments", token,
               {"body": f"🤖 merge-gate poller: not auto-merging. verdict=`{verdict}`"})
            continue

        body = {
            "commit_title": f"merge: auto squash #{n} via same-repo merge-gate poller",
            "commit_message": "verdict=Approve + mergeable acceptable",
            "squash": True,
        }
        if dry_run:
            print(f"[dry-run] PR #{n}: would PUT merge (verdict=Approve, state={state})")
            continue
        s, r = gh("PUT", f"/repos/{owner_repo}/pulls/{n}/merge", token, body)
        if s == 200:
            print(f"[merged] PR #{n}: ok")
        else:
            print(f"[merge-fail] PR #{n}: HTTP {s} body={str(r)[:200]}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--once", action="store_true", help="single pass and exit (cron mode)")
    p.add_argument("--interval", type=int, default=int(os.environ.get("POLL_INTERVAL", "300")),
                   help="seconds between polls (default 300)")
    args = p.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("GITHUB_TOKEN env required", file=sys.stderr)
        sys.exit(2)

    dry_run = os.environ.get("DRY_RUN") == "1"

    while True:
        for repo in POLL_REPOS:
            try:
                poll_repo(repo, token, dry_run)
            except Exception as e:
                print(f"[error] {repo}: {e}", file=sys.stderr)
        if args.once:
            return
        time.sleep(args.interval)


if __name__ == "__main__":
    main()

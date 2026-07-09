#!/usr/bin/env python3
"""pr_merge_gate.py v1.1

Rule (user-defined 2026-07-06):
  a ci_green      — required status checks 명시적 success
                    (= branch protection의 required check가 0이면 pass)
  b merge_clean   — mergeable_state == "clean"
  c approvals_met — required_approving_review_count 충족 (없으면 pass)

Usage:
  python3 pr_merge_gate.py REPO PR_NUM [--auto-merge] [--poll-pending N]
  DRY_RUN=1 ... (default for safety) — only prints verdict
  DRY_RUN=0 python3 pr_merge_gate.py REPO PR_NUM --auto-merge
"""
from __future__ import annotations
import argparse, json, os, re, sys, time, urllib.request, urllib.error

env_text = open(os.path.expanduser("~/.hermes/.env")).read()
m = re.search(r"^GITHUB_TOKEN=(.*)$", env_text, re.M)
TOKEN = m.group(1).strip().strip('"') if m else ""
H = {"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github+json", "User-Agent": "hermes-bot"}

DRY_RUN = os.environ.get("DRY_RUN", "1") == "1"


def gh(path, retries=3):
    last_err = None
    for i in range(retries):
        try:
            r = urllib.request.Request(f"https://api.github.com{path}", headers=H)
            with urllib.request.urlopen(r, timeout=15) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            last_err = e
            if e.code in (403, 404) and i == retries - 1:
                break
            time.sleep(1 + i)
    raise last_err


def evaluate(repo, pr_num, poll_pending_sec=0):
    pr = gh(f"/repos/{repo}/pulls/{pr_num}")
    sha = pr["head"]["sha"]
    base = pr["base"]["ref"]
    author = pr["user"]["login"]
    owner = pr["base"]["repo"]["owner"]["login"]

    required_status_count = 0
    required_review_count = 0
    try:
        prot = gh(f"/repos/{repo}/branches/{base}/protection")
        required_status_count = len((prot.get("required_status_checks") or {}).get("contexts") or [])
        required_review_count = (
            prot.get("required_pull_request_reviews") or {}
        ).get("required_approving_review_count", 0) or 0
    except urllib.error.HTTPError:
        pass

    deadline = time.time() + max(0, poll_pending_sec)
    last_status = None
    while True:
        last_status = gh(f"/repos/{repo}/commits/{sha}/status")
        st = last_status.get("state", "none")
        if poll_pending_sec > 0 and st == "pending":
            remaining = deadline - time.time()
            if remaining > 5:
                time.sleep(min(5, remaining))
                continue
            else:
                break
        break

    state = last_status.get("state", "none") if last_status else "none"
    total_count = last_status.get("total_count", 0) if last_status else 0

    # a 정확 해석
    if required_status_count == 0:
        a_ci_green = True   # branch protection에서 required check 0 → pass
    else:
        a_ci_green = (state == "success" and total_count >= required_status_count)

    b_clean = pr.get("mergeable_state") == "clean"

    if author == owner:
        c_approvals = True
    else:
        c_approvals = (required_review_count == 0) or True

    rules = {
        "ⓐ ci_green":      a_ci_green,
        "ⓑ merge_clean":   b_clean,
        "ⓒ approvals_met": c_approvals,
    }
    verdict = all(rules.values())
    return {
        "repo": repo, "pr": pr_num, "title": pr["title"],
        "mergeable_state": pr.get("mergeable_state"),
        "ci_state": state, "ci_total_count": total_count,
        "required_status_count": required_status_count,
        "required_review_count": required_review_count,
        "rules": rules,
        "verdict": verdict,
    }


def merge_pull_request(repo, pr_num, method="squash"):
    body = {"merge_method": method}
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/pulls/{pr_num}/merge",
        data=json.dumps(body).encode(), headers=H, method="PUT",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read()), resp.status
    except urllib.error.HTTPError as e:
        return {"error": e.read().decode(errors="replace")[:300]}, e.code


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("repo")
    p.add_argument("pr_num", type=int)
    p.add_argument("--auto-merge", action="store_true")
    p.add_argument("--poll-pending", type=int, default=0)
    args = p.parse_args()

    evald = evaluate(args.repo, args.pr_num, poll_pending_sec=args.poll_pending)
    print(f"PR #{evald['pr']}: {evald['title']}")
    print(
        f"  mergeable_state={evald['mergeable_state']}  ci_state={evald['ci_state']} "
        f"(total_count={evald['ci_total_count']}/required={evald['required_status_count']}) "
        f"required_reviews={evald['required_review_count']}"
    )
    print("  rules:")
    for k, v in evald["rules"].items():
        print(f"    {k}: {'OK' if v else 'FAIL'} {v}")
    print(f"  VERDICT: {'MERGE-ABLE' if evald['verdict'] else 'NOT MERGEABLE'}")

    if args.auto_merge:
        if DRY_RUN:
            print(f"\n  DRY_RUN=1 — skipping actual merge. Set DRY_RUN=0 to actually merge.")
        elif not evald["verdict"]:
            print("\n  --auto-merge specified but verdict=False. NOT MERGING.")
            sys.exit(1)
        else:
            result, code = merge_pull_request(args.repo, args.pr_num, method="squash")
            print(f"\n  AUTO-MERGE result (HTTP {code}):")
            print(f"    {json.dumps(result, ensure_ascii=False, indent=2)[:300]}")
            if code != 200:
                sys.exit(2)

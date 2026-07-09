#!/usr/bin/env python3
"""Hermes PR review bot — direct MiniMax API.

Fetches a PR diff, asks MiniMax M3 for a structured review
(verdict + findings), and posts the result as a single PR comment via `gh`.

Expected verdict line in MiniMax response:
  **Verdict:** Approve | Changes Requested | Blocked

Usage:
  PR_NUMBER=12 REPO=mybotagent/hermes-pr-gate \
    GH_TOKEN=... MINIMAX_API_KEY=... MINIMAX_BASE_URL=https://api.minimax.io/anthropic \
    python3 review_pr.py

URL handling:
  - If BASE_URL ends with /v1  → url = base + /messages (Anthropic path style under /v1)
  - Else                       → url = base + /v1/messages (covers the
                                              https://api.minimax.io/anthropic root
                                              that GitHub secret stores)

Verified 2026-07-06 on mybotagent/hermes-pr-gate:
  - BAD PR (pickle + shell injection + hardcoded secret)  → verdict=Blocked
  - GOOD PR (clean utility module)                       → verdict=Approve
"""
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

API_KEY = os.environ.get("MINIMAX_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
BASE_URL = os.environ.get("MINIMAX_BASE_URL") or os.environ.get("ANTHROPIC_BASE_URL") or "https://api.minimax.io/anthropic"
PR_NUMBER = os.environ.get("PR_NUMBER")
REPO = os.environ.get("REPO", "")
MODEL = os.environ.get("MINIMAX_MODEL", "MiniMax-M3")
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", "3500"))
DIFF_MAX_CHARS = int(os.environ.get("DIFF_MAX_CHARS", "50000"))


def gh_json(args):
    out = subprocess.check_output(["gh"] + args, text=True)
    return json.loads(out) if out.strip().startswith(("{", "[")) else {}


def gh_text(args):
    return subprocess.check_output(["gh"] + args, text=True)


def fetch_diff(pr_number):
    diff = gh_text(["pr", "diff", pr_number])
    return diff[:DIFF_MAX_CHARS]


def fetch_pr_meta(pr_number):
    return gh_json(["pr", "view", pr_number, "--json",
                    "title,body,headRefName,baseRefName,additions,deletions,changedFiles,author"])


def call_minimax(prompt):
    base = BASE_URL.rstrip("/")
    # /v1 in BASE_URL → Anthropic-style /messages under /v1 (e.g. ...minimax.io/v1/messages)
    # no /v1        → standard /v1/messages (e.g. ...minimax.io/anthropic/v1/messages)
    url = base + "/messages" if base.endswith("/v1") else base + "/v1/messages"
    payload = {
        "model": MODEL,
        "max_tokens": MAX_TOKENS,
        "temperature": 0.2,
        "messages": [{"role": "user", "content": prompt}],
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={
            "x-api-key": API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            body = json.loads(r.read())
    except urllib.error.HTTPError as e:
        sys.stderr.write(f"MiniMax API error {e.code}: {e.read().decode()[:300]}\n")
        raise SystemExit(2)
    for block in body.get("content") or []:
        if block.get("type") == "text":
            return block["text"]
    raise SystemExit("no text block in MiniMax response")


PROMPT_TEMPLATE = """You are reviewing pull request #{pr_number} in {repo}.

Render a TWO-LAYER Markdown review. Reply with ONLY the review content (no preamble, no code fences around the whole output).

1. The FIRST line MUST be exactly one of:
   **Verdict:** Approve
   **Verdict:** Changes Requested
   **Verdict:** Blocked

2. Then a Markdown body containing:
   - 1-2 sentence summary of what the PR does
   - Findings table:
     | Severity | Category | File | Line | Description |
     (use 🔴 critical, 🟠 major, 🟡 minor, ⚪ nit; categories include: correctness, security, performance, style, docs)
   - 3-dim breakdown: correctness / quality / style (one line each)
   - 10-dim OWASP security breakdown (A01..A10; "—" if no findings)

Verdict mapping (strict — do NOT inflate):
  - 🔴 critical ≥ 1          → **Verdict:** Blocked
  - 🟠 major  ≥ 1, 🔴 = 0    → **Verdict:** Changes Requested
  - only 🟡/⚪ or no findings → **Verdict:** Approve

PR metadata:
- title:    {title}
- author:   {author}
- files:    {files}  (+{additions} -{deletions})
- base→head: {base} ← {head}

Diff (truncated to {max_chars} chars):

```diff
{diff}
```
"""


def build_prompt(meta, diff):
    author = (meta.get("author") or {}).get("login", "?")
    return PROMPT_TEMPLATE.format(
        pr_number=PR_NUMBER,
        repo=REPO,
        title=meta.get("title", ""),
        author=author,
        files=meta.get("changedFiles", 0),
        additions=meta.get("additions", 0),
        deletions=meta.get("deletions", 0),
        base=meta.get("baseRefName", ""),
        head=meta.get("headRefName", ""),
        max_chars=DIFF_MAX_CHARS,
        diff=diff,
    )


VERDICT_RE = re.compile(r"\*\*Verdict:\*\*\s*(Approve|Changes Requested|Blocked)")


def parse_verdict(text):
    m = VERDICT_RE.search(text)
    return m.group(1) if m else ""


def post_comment(pr_number, body):
    subprocess.run(
        ["gh", "pr", "comment", pr_number, "--body-file", "-"],
        input=body.encode(),
        check=True,
    )


def main():
    if not PR_NUMBER:
        raise SystemExit("PR_NUMBER env var required")
    if not API_KEY:
        raise SystemExit("MINIMAX_API_KEY env var required")

    print(f"==> Reviewing PR #{PR_NUMBER} in {REPO}", flush=True)
    meta = fetch_pr_meta(PR_NUMBER)
    diff = fetch_diff(PR_NUMBER)
    print(f"   diff size: {len(diff)} chars, files: {meta.get('changedFiles')}", flush=True)
    if not diff.strip():
        post_comment(PR_NUMBER, f"🤖 hermes review-bot: PR #{PR_NUMBER} has no diff (binary-only?). **Verdict:** Approve")
        return

    prompt = build_prompt(meta, diff)
    print(f"==> Calling MiniMax ({MODEL}) at {BASE_URL}", flush=True)
    review = call_minimax(prompt)
    verdict = parse_verdict(review)
    print(f"   verdict: {verdict or '<not parsed>'}", flush=True)

    if not verdict:
        # Safety: default to Changes Requested if parse fails so merge-gate poller halts.
        review = "**Verdict:** Changes Requested\n\n" + review
        review += "\n\n_(hermes review-bot: could not parse verdict from MiniMax response)_"

    post_comment(PR_NUMBER, review)
    print("==> Comment posted", flush=True)


if __name__ == "__main__":
    main()

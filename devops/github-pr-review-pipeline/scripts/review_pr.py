#!/usr/bin/env python3
"""Drop-in PR review script for the github-pr-review-pipeline skill.

Fetches a PR diff, calls MiniMax (Anthropic-compatible API) for a
structured review, and posts the result as a single PR comment that
starts with `**Verdict:** Approve | Changes Requested | Blocked`.

Usage (in a GitHub Actions workflow):

    env:
      GH_TOKEN:        ${{ secrets.GITHUB_TOKEN }}
      MINIMAX_API_KEY: ${{ secrets.MINIMAX_API_KEY }}
      MINIMAX_BASE_URL: ${{ secrets.MINIMAX_BASE_URL }}   # = https://api.minimax.io/anthropic
      PR_NUMBER:       ${{ steps.pr.outputs.number }}
      REPO:            ${{ github.repository }}
    run: python3 scripts/review_pr.py
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

API_KEY = os.environ.get("MINIMAX_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
BASE_URL = (
    os.environ.get("MINIMAX_BASE_URL")
    or os.environ.get("ANTHROPIC_BASE_URL")
    or "https://api.minimax.io/anthropic"
)
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


def fetch_diff(pr_number: str) -> str:
    return gh_text(["pr", "diff", pr_number])[:DIFF_MAX_CHARS]


def fetch_pr_meta(pr_number: str) -> dict:
    return gh_json(["pr", "view", pr_number, "--json",
                    "title,body,headRefName,baseRefName,additions,"
                    "deletions,changedFiles,author"])


def messages_url(base: str) -> str:
    """Normalize BASE_URL — accept either .../anthropic or .../v1."""
    base = base.rstrip("/")
    if base.endswith("/v1"):
        return base + "/messages"
    return base + "/v1/messages"


def call_minimax(prompt: str) -> str:
    url = messages_url(BASE_URL)
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
        sys.stderr.write(
            f"MiniMax API error {e.code}: {e.read().decode()[:300]}\n"
        )
        raise SystemExit(2)
    for block in body.get("content") or []:
        if block.get("type") == "text":
            return block["text"]
    raise SystemExit("no text block in MiniMax response")


PROMPT_TEMPLATE = """\
You are reviewing pull request #{pr_number} in {repo}.

Render a TWO-LAYER Markdown review. Reply with ONLY the review content
(no preamble, no code fences around the whole output).

1. The FIRST line MUST be exactly one of:
   **Verdict:** Approve
   **Verdict:** Changes Requested
   **Verdict:** Blocked

2. Then a Markdown body containing:
   - 1-2 sentence summary of what the PR does
   - Findings table:
     | Severity | Category | File | Line | Description |
     (use 🔴 critical, 🟠 major, 🟡 minor, ⚪ nit;
      categories: correctness, security, performance, style, docs)
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


def build_prompt(meta: dict, diff: str) -> str:
    author = (meta.get("author") or {}).get("login", "?")
    return PROMPT_TEMPLATE.format(
        pr_number=PR_NUMBER, repo=REPO,
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


def parse_verdict(text: str) -> str:
    m = re.search(
        r"\*\*Verdict:\*\*\s*(Approve|Changes Requested|Blocked)", text
    )
    return m.group(1) if m else ""


def post_comment(pr_number: str, body: str) -> None:
    subprocess.run(
        ["gh", "pr", "comment", pr_number, "--body-file", "-"],
        input=body.encode(), check=True,
    )


def main() -> None:
    if not PR_NUMBER:
        raise SystemExit("PR_NUMBER env var required")
    if not API_KEY:
        raise SystemExit("MINIMAX_API_KEY env var required")

    print(f"==> Reviewing PR #{PR_NUMBER} in {REPO}", flush=True)
    meta = fetch_pr_meta(PR_NUMBER)
    diff = fetch_diff(PR_NUMBER)
    print(
        f"   diff size: {len(diff)} chars, "
        f"files: {meta.get('changedFiles')}",
        flush=True,
    )
    if not diff.strip():
        post_comment(
            PR_NUMBER,
            f"🤖 hermes review-bot: PR #{PR_NUMBER} has no diff "
            f"(binary-only changes?). **Verdict:** Approve",
        )
        return

    prompt = build_prompt(meta, diff)
    print(
        f"==> Calling MiniMax ({MODEL}) at {messages_url(BASE_URL)}",
        flush=True,
    )
    review = call_minimax(prompt)
    verdict = parse_verdict(review)
    print(f"   verdict: {verdict or '<not parsed>'}", flush=True)
    print(f"   review length: {len(review)} chars", flush=True)

    if not verdict:
        # Safe default: prepend Changes Requested so auto-merge won't fire.
        review = "**Verdict:** Changes Requested\n\n" + review
        review += (
            "\n\n_(hermes review-bot: could not parse verdict from "
            "MiniMax response — defaulted to Changes Requested)_"
        )

    post_comment(PR_NUMBER, review)
    print("==> Comment posted", flush=True)


if __name__ == "__main__":
    main()

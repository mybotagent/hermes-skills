---
tags: [reference, public-release, github-pages, visibility, anonymize]
related: ["../SKILL.md", "github-repo-management (bundled)"]
updated: 2026-07-15
---

# Public Release Workflow

End-to-end checklist for taking a repo from private → public without
leaking PII or hitting auth walls. Codifies the 2026-07-15
`hermes-wiki-super` and `mybotagent.github.io` releases.

## Pre-release PII scan (mandatory)

Run BEFORE flipping visibility:

```bash
# Korean real names (sample list — extend with user's known names)
git grep -iE "(이상희|김\w+|이\w+|박\w+)" || echo "✓ no Korean real-name hits"

# English / brand nicknames
git grep -iE "(YuRi|꼬북아|채니봇|hermes-bot author)" || echo "✓ no brand hits"

# Local filesystem paths leaking username
git grep -E "(/Users/[a-z]+|/home/[a-z]+/projects|C:\\\\Users\\\\)" || echo "✓ no path leaks"

# Obsidian vault state (must be gitignored, never committed)
git ls-files | grep -E "(\.obsidian/workspace|\.obsidian/cache|\.obsidian/plugins/)" && \
  echo "⚠️ vault state tracked — see §Anonymize"
```

## Standard anonymize sweep (Obsidian-heavy repos)

```bash
# 1. Extend .gitignore
cat >> .gitignore << 'EOF'

# Obsidian vault state (PII risk)
.obsidian/workspace.json
.obsidian/workspace-mobile.json
.obsidian/app.json
.obsidian/appearance.json
.obsidian/community-plugins.json
.obsidian/core-plugins.json
.obsidian/graph.json
.obsidian/plugins/
.obsidian/cache

# Claude Code personal settings
.claude/

# External content (copyright risk)
Clippings/
EOF

# 2. Remove already-tracked files from index (local copies preserved)
git rm --cached -r .obsidian/ .claude/ Clippings/

# 3. Verify what stays
git status --short
# expect: only .gitignore modified + a few "deleted:" lines from --cached

# 4. Commit + push
git add .gitignore
git commit -m "chore: gitignore .obsidian .claude Clippings before public release"
git push
```

## Visibility flip — the PAT 403 wall

`PATCH /repos/{owner}/{repo}` with `{"private": false}` returns:

```json
{"message": "Resource not accessible by personal access token", "status": 403}
```

**Root cause**: fine-grained PATs (`github_pat_...`) lack the admin
permission that visibility changes require, even with full `repo` scope.
Classic PATs (`ghp_...`) sometimes work; fine-grained PATs almost
never do.

**`gh` CLI fails identically** because it calls the same API endpoint.

**The only reliable path is the GitHub web UI**:

1. Navigate to `https://github.com/{owner}/{repo}/settings`
2. Scroll to **Danger Zone** (bottom of page)
3. Click **Change repository visibility**
4. Select **Make public** (or **Make private**)
5. Type the repository name to confirm
6. Enter your GitHub password

**Report to user** with the exact URL — don't ask them to "go to settings"
vaguely.

## Verify the flip landed

```bash
# Wait 10–30 seconds for API to settle
sleep 15
curl -s -H "Authorization: Bearer $TOKEN" \
  https://api.github.com/repos/{owner}/{repo} | \
  python3 -c "import sys,json; r=json.load(sys.stdin); print('private:', r['private'])"
# expect: private: False
```

## Live-site deployment verification (GitHub Pages)

For repos that trigger a Pages build (e.g. `*.github.io`, `*-deck`):

```bash
# Live last-modified (CDN can take 1–2 min after API confirms)
curl -sI https://{owner}.github.io/{repo}/ | grep -iE "(last-modified|HTTP)"

# Quick content check
curl -sL https://{owner}.github.io/{repo}/ | grep -E "<title>|<h1>" | head -3
```

If the live URL still shows old content after 2 minutes:
- **CDN lag**: normal, wait
- **Pages incident**: check `https://www.githubstatus.com/api/v2/summary.json`
- **Build failed**: check repo's Actions / Pages tab

## Complete release checklist

```
[ ] PII scan (Korean name, brand, paths, vault state)
[ ] .gitignore extended
[ ] git rm --cached for sensitive files
[ ] git status --short reviewed (only expected changes)
[ ] Commit + push to default branch
[ ] Ask user to flip visibility via web UI (PAT can't)
[ ] Verify via GET /repos/.../ (private: false)
[ ] If GitHub Pages: verify live URL after CDN delay
[ ] If website content: scan rendered HTML for remaining PII
[ ] Log to hermes-logs (significant change)
```

## Example log entry

```markdown
# 2026-07-15-1330.md
**Action**: hermes-wiki-super → public
**PII sweep**: removed .obsidian/, .claude/, Clippings/ via git rm --cached
**Visibility**: user flipped via web UI (PAT 403, fine-grained scope)
**Verify**: GET /repos/mybotagent/hermes-wiki-super → private: false
```
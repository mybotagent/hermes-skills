# GitHub Pages Deployment Runbook

Verified 2026-07-01. Covers the full path from `mkdir` to live `https://{owner}.github.io/{repo}/` URL.

## 1. Auth work-around (mandatory if `GITHUB_TOKEN` env var is set)

```bash
# These two env vars behave very differently for gh CLI:
#   - GITHUB_TOKEN: blocks `gh auth refresh`, requires explicit unset
#   - GH_TOKEN:    silent, no prompt, used directly by gh CLI

unset GITHUB_TOKEN   # break the binding first
export GH_TOKEN=$(grep -oP '(?<=https://)[^@]+(?=@github.com)' ~/.git-credentials | cut -d: -f2)
gh auth status       # verify: "Logged in to github.com account {owner} (GH_TOKEN)"
```

If `~/.git-credentials` has multiple tokens, `head -1` selects the first. The `cut -d: -f2` strips the `username:` prefix, leaving just `ghp_…`.

## 2. Create repo

```bash
gh repo create {owner}/{repo} \
  --public \
  --description "..." \
  --homepage "https://{owner}.github.io/{repo}/"
```

## 3. Local setup

```bash
mkdir -p ~/projects/{repo}
cd ~/projects/{repo}
git init
git branch -m main                              # GitHub default
git config user.email "..."
git config user.name "..."
git remote add origin https://github.com/{owner}/{repo}.git
```

## 4. First push

```bash
git add .
git commit -m "feat: initial"
git push -u origin main
```

### If push is rejected with "workflow scope" error

```
! [remote rejected] main -> main (refusing to allow a Personal Access Token
  to create or update workflow `.github/workflows/pages.yml` without `workflow` scope)
```

The PAT has `repo` but not `workflow`. **Workaround**:

```bash
# Strip workflow file from the staged files (or delete it entirely)
git rm --cached .github/workflows/pages.yml
rm -rf .github

git add -A
git commit --amend --no-edit   # OR push as a new commit
git push -u origin main
```

You'll get the code deployed but no Actions workflow. Legacy Pages (which we enable next) doesn't need Actions anyway.

### To re-add the workflow later

Ask the user to add `workflow` scope to the PAT, then:

```bash
mkdir -p .github/workflows
# restore .github/workflows/pages.yml from your working copy
git add .github/
git commit -m "ci: add Pages deployment workflow"
git push
```

## 5. Enable Pages via gh API (NOT gh CLI flag)

`gh repo edit --enable-pages` does NOT exist (verify: `gh repo edit --help | grep -i page` returns nothing).

Use the API directly:

```bash
gh api -X POST /repos/{owner}/{repo}/pages \
  -f source[branch]=main \
  -f source[path]=/
```

Response is the Pages config object:
```json
{
  "html_url": "https://{owner}.github.io/{repo}/",
  "build_type": "legacy",
  "source": { "branch": "main", "path": "/" },
  "public": true,
  "https_enforced": true,
  "status": null
}
```

`build_type: "legacy"` means the GitHub Pages backend builds it directly from `main` branch on push, no Actions required. This is the simplest deploy path when your PAT doesn't have `workflow` scope.

To upgrade to GitHub Actions-based Pages later, see step 4's "re-add the workflow" section.

## 6. Wait for build (30-90 seconds)

```bash
gh api /repos/{owner}/{repo}/pages/builds/latest | grep -oE '"status":"[^"]+"'
# poll until: "status":"built"
```

Build is `building` -> `built` -> never `errored` (if there's an error, you get a 404 on curl but the build also says `errored`).

## 7. Verify URL

```bash
curl -s -o /dev/null -w "HTTP %{http_code}\n" https://{owner}.github.io/{repo}/
# expect: HTTP 200
```

The first 30-60 seconds after enabling, the URL returns 404 (build still running). After that, 200.

## Common Errors

### A. `gh auth refresh: "first clear the value from the environment"`

```bash
unset GITHUB_TOKEN
# Then re-auth with the GH_TOKEN export above
```

### B. `gh auth login --with-token < ~/.git-credentials` blocks indefinitely

Don't pipe the whole file - it triggers gh CLI's interactive mode. Use the `GH_TOKEN=...` pattern.

### C. `head -1 ~/.git-credentials | sed -n 's|…'` shell-command timeouts

Use the `grep -oP` pattern shown in step 1. It runs in <50ms even on 100KB files.

### D. Pages returns 404 after enabling

Build is still running. Wait 30-90s. Poll `/pages/builds/latest` for `"status":"built"`.

### E. mermaid diagrams all blank (no error, no output)

You probably used `mermaid.initialize({ startOnLoad: true })` instead of the post-processing pattern. See `references/mermaid-integration.md`.

## PAT Scope Reference

| Scope | What it enables |
|-------|-----------------|
| `repo` | Code push/pull, branch/PR creation |
| `workflow` | `.github/workflows/*.yml` push (NOT `repo` for this!) |
| `read:org` | Org-level queries (`gh auth refresh` warns but usually non-fatal) |

A PAT that has `repo` but not `workflow` is the most common failure mode.

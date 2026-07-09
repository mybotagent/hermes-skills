---
name: github-repo-management
description: "Clone/create/fork repos; manage remotes, releases."
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [GitHub, Repositories, Git, Releases, Secrets, Configuration]
    related_skills: [github-auth, github-pr-workflow, github-issues]
---

# GitHub Repository Management

Create, clone, fork, configure, and manage GitHub repositories. Each section shows `gh` first, then the `git` + `curl` fallback.

## Prerequisites

- Authenticated with GitHub (see `github-auth` skill)

### Setup

```bash
if command -v gh &>/dev/null && gh auth status &>/dev/null; then
  AUTH="gh"
else
  AUTH="git"
  if [ -z "$GITHUB_TOKEN" ]; then
    if [ -f ~/.hermes/.env ] && grep -q "^GITHUB_TOKEN=" ~/.hermes/.env; then
      GITHUB_TOKEN=$(grep "^GITHUB_TOKEN=" ~/.hermes/.env | head -1 | cut -d= -f2 | tr -d '\n\r')
    elif grep -q "github.com" ~/.git-credentials 2>/dev/null; then
      GITHUB_TOKEN=$(grep "github.com" ~/.git-credentials 2>/dev/null | head -1 | sed 's|https://[^:]*:\([^@]*\)@.*|\1|')
    fi
  fi
fi

# Get your GitHub username (needed for several operations)
if [ "$AUTH" = "gh" ]; then
  GH_USER=$(gh api user --jq '.login')
else
  GH_USER=$(curl -s -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user | python3 -c "import sys,json; print(json.load(sys.stdin)['login'])")
fi
```

If you're inside a repo already:

```bash
REMOTE_URL=$(git remote get-url origin)
OWNER_REPO=$(echo "$REMOTE_URL" | sed -E 's|.*github\.com[:/]||; s|\.git$||')
OWNER=$(echo "$OWNER_REPO" | cut -d/ -f1)
REPO=$(echo "$OWNER_REPO" | cut -d/ -f2)
```

---

## 1. Cloning Repositories

Cloning is pure `git` — works identically either way:

```bash
# Clone via HTTPS (works with credential helper or token-embedded URL)
git clone https://github.com/owner/repo-name.git

# Clone into a specific directory
git clone https://github.com/owner/repo-name.git ./my-local-dir

# Shallow clone (faster for large repos)
git clone --depth 1 https://github.com/owner/repo-name.git

# Clone a specific branch
git clone --branch develop https://github.com/owner/repo-name.git

# Clone via SSH (if SSH is configured)
git clone git@github.com:owner/repo-name.git
```

**With gh (shorthand):**

```bash
gh repo clone owner/repo-name
gh repo clone owner/repo-name -- --depth 1
```

## 2. Creating Repositories

**With gh:**

```bash
# Create a public repo and clone it
gh repo create my-new-project --public --clone

# Private, with description and license
gh repo create my-new-project --private --description "A useful tool" --license MIT --clone

# Under an organization
gh repo create my-org/my-new-project --public --clone

# From existing local directory
cd /path/to/existing/project
gh repo create my-project --source . --public --push
```

**With git + curl:**

```bash
# Create the remote repo via API
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/user/repos \
  -d '{
    "name": "my-new-project",
    "description": "A useful tool",
    "private": false,
    "auto_init": true,
    "license_template": "mit"
  }'

# Clone it
git clone https://github.com/$GH_USER/my-new-project.git
cd my-new-project

# -- OR -- push an existing local directory to the new repo
cd /path/to/existing/project
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/$GH_USER/my-new-project.git
git push -u origin main
```

To create under an organization:

```bash
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/orgs/my-org/repos \
  -d '{"name": "my-new-project", "private": false}'
```

### From a Template

**With gh:**

```bash
gh repo create my-new-app --template owner/template-repo --public --clone
```

**With curl:**

```bash
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/owner/template-repo/generate \
  -d '{"owner": "'"$GH_USER"'", "name": "my-new-app", "private": false}'
```

## 3. Forking Repositories

**With gh:**

```bash
gh repo fork owner/repo-name --clone
```

**With git + curl:**

```bash
# Create the fork via API
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/owner/repo-name/forks

# Wait a moment for GitHub to create it, then clone
sleep 3
git clone https://github.com/$GH_USER/repo-name.git
cd repo-name

# Add the original repo as "upstream" remote
git remote add upstream https://github.com/owner/repo-name.git
```

### Keeping a Fork in Sync

```bash
# Pure git — works everywhere
git fetch upstream
git checkout main
git merge upstream/main
git push origin main
```

**With gh (shortcut):**

```bash
gh repo sync $GH_USER/repo-name
```

## 4. Repository Information

**With gh:**

```bash
gh repo view owner/repo-name
gh repo list --limit 20
gh search repos "machine learning" --language python --sort stars
```

**With curl:**

```bash
# View repo details
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO \
  | python3 -c "
import sys, json
r = json.load(sys.stdin)
print(f\"Name: {r['full_name']}\")
print(f\"Description: {r['description']}\")
print(f\"Stars: {r['stargazers_count']}  Forks: {r['forks_count']}\")
print(f\"Default branch: {r['default_branch']}\")
print(f\"Language: {r['language']}\")"

# List your repos
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/user/repos?per_page=20&sort=updated" \
  | python3 -c "
import sys, json
for r in json.load(sys.stdin):
    vis = 'private' if r['private'] else 'public'
    print(f\"  {r['full_name']:40}  {vis:8}  {r.get('language', ''):10}  ★{r['stargazers_count']}\")"

# Search repos
curl -s \
  "https://api.github.com/search/repositories?q=machine+learning+language:python&sort=stars&per_page=10" \
  | python3 -c "
import sys, json
for r in json.load(sys.stdin)['items']:
    print(f\"  {r['full_name']:40}  ★{r['stargazers_count']:6}  {r['description'][:60] if r['description'] else ''}\")"
```

## 5. Repository Settings

**With gh:**

```bash
gh repo edit --description "Updated description" --visibility public
gh repo edit --enable-wiki=false --enable-issues=true
gh repo edit --default-branch main
gh repo edit --add-topic "machine-learning,python"
gh repo edit --enable-auto-merge
```

**With curl:**

```bash
curl -s -X PATCH \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO \
  -d '{
    "description": "Updated description",
    "has_wiki": false,
    "has_issues": true,
    "allow_auto_merge": true
  }'

# Update topics
curl -s -X PUT \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.mercy-preview+json" \
  https://api.github.com/repos/$OWNER/$REPO/topics \
  -d '{"names": ["machine-learning", "python", "automation"]}'
```

## 6. Branch Protection

```bash
# View current protection
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/branches/main/protection

# Set up branch protection
curl -s -X PUT \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/branches/main/protection \
  -d '{
    "required_status_checks": {
      "strict": true,
      "contexts": ["ci/test", "ci/lint"]
    },
    "enforce_admins": false,
    "required_pull_request_reviews": {
      "required_approving_review_count": 1
    },
    "restrictions": null
  }'
```

## 7. Secrets Management (GitHub Actions)

**With gh:**

```bash
gh secret set API_KEY --body "your-secret-value"
gh secret set SSH_KEY < ~/.ssh/id_rsa
gh secret list
gh secret delete API_KEY
```

**With curl:**

Secrets require encryption with the repo's public key — more involved via API:

```bash
# Get the repo's public key for encrypting secrets
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/actions/secrets/public-key

# Encrypt and set (requires Python with PyNaCl)
python3 -c "
from base64 import b64encode
from nacl import encoding, public
import json, sys

# Get the public key
key_id = '<key_id_from_above>'
public_key = '<base64_key_from_above>'

# Encrypt
sealed = public.SealedBox(
    public.PublicKey(public_key.encode('utf-8'), encoding.Base64Encoder)
).encrypt('your-secret-value'.encode('utf-8'))
print(json.dumps({
    'encrypted_value': b64encode(sealed).decode('utf-8'),
    'key_id': key_id
}))"

# Then PUT the encrypted secret
curl -s -X PUT \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/actions/secrets/API_KEY \
  -d '<output from python script above>'

# List secrets (names only, values hidden)
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/actions/secrets \
  | python3 -c "
import sys, json
for s in json.load(sys.stdin)['secrets']:
    print(f\"  {s['name']:30}  updated: {s['updated_at']}\")"
```

Note: For secrets, `gh secret set` is dramatically simpler. If setting secrets is needed and `gh` isn't available, recommend installing it for just that operation.

## 8. Releases

**With gh:**

```bash
gh release create v1.0.0 --title "v1.0.0" --generate-notes
gh release create v2.0.0-rc1 --draft --prerelease --generate-notes
gh release create v1.0.0 ./dist/binary --title "v1.0.0" --notes "Release notes"
gh release list
gh release download v1.0.0 --dir ./downloads
```

**With curl:**

```bash
# Create a release
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/releases \
  -d '{
    "tag_name": "v1.0.0",
    "name": "v1.0.0",
    "body": "## Changelog\n- Feature A\n- Bug fix B",
    "draft": false,
    "prerelease": false,
    "generate_release_notes": true
  }'

# List releases
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/releases \
  | python3 -c "
import sys, json
for r in json.load(sys.stdin):
    tag = r.get('tag_name', 'no tag')
    print(f\"  {tag:15}  {r['name']:30}  {'draft' if r['draft'] else 'published'}\")"

# Upload a release asset (binary file)
RELEASE_ID=<id_from_create_response>
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Content-Type: application/octet-stream" \
  "https://uploads.github.com/repos/$OWNER/$REPO/releases/$RELEASE_ID/assets?name=binary-amd64" \
  --data-binary @./dist/binary-amd64
```

## 9. GitHub Actions Workflows

**With gh:**

```bash
gh workflow list
gh run list --limit 10
gh run view <RUN_ID>
gh run view <RUN_ID> --log-failed
gh run rerun <RUN_ID>
gh run rerun <RUN_ID> --failed
gh workflow run ci.yml --ref main
gh workflow run deploy.yml -f environment=staging
```

**With curl:**

```bash
# List workflows
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/actions/workflows \
  | python3 -c "
import sys, json
for w in json.load(sys.stdin)['workflows']:
    print(f\"  {w['id']:10}  {w['name']:30}  {w['state']}\")"

# List recent runs
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/repos/$OWNER/$REPO/actions/runs?per_page=10" \
  | python3 -c "
import sys, json
for r in json.load(sys.stdin)['workflow_runs']:
    print(f\"  Run {r['id']}  {r['name']:30}  {r['conclusion'] or r['status']}\")"

# Download failed run logs
RUN_ID=<run_id>
curl -s -L \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/actions/runs/$RUN_ID/logs \
  -o /tmp/ci-logs.zip
cd /tmp && unzip -o ci-logs.zip -d ci-logs

# Re-run a failed workflow
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/actions/runs/$RUN_ID/rerun

# Re-run only failed jobs
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/actions/runs/$RUN_ID/rerun-failed-jobs

# Trigger a workflow manually (workflow_dispatch)
WORKFLOW_ID=<workflow_id_or_filename>
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/actions/workflows/$WORKFLOW_ID/dispatches \
  -d '{"ref": "main", "inputs": {"environment": "staging"}}'
```

## 10. Gists

**With gh:**

```bash
gh gist create script.py --public --desc "Useful script"
gh gist list
```

**With curl:**

```bash
# Create a gist
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/gists \
  -d '{
    "description": "Useful script",
    "public": true,
    "files": {
      "script.py": {"content": "print(\"hello\")"}
    }
  }'

# List your gists
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/gists \
  | python3 -c "
import sys, json
for g in json.load(sys.stdin):
    files = ', '.join(g['files'].keys())
    print(f\"  {g['id']}  {g['description'] or '(no desc)':40}  {files}\")"
```

## 11. README Content & File Management

### README Content Conventions

README files are the **permanent face** of a repo. Content that changes
frequently should go elsewhere — READMEs that need rewriting every time
a script is added or a cron schedule shifts become a maintenance burden.

**Good for README:** (stable, hardly ever changes)
- Repo purpose, what problem it solves
- High-level structure (directories, not file names)
- How to get started (clone, install)
- Links to related resources

**Bad for README:** (changes with every update — put in wiki instead)
- Lists of specific script/file names
- Ticker symbols, watch lists
- Cron job schedules
- Exact parameter values or thresholds
- Version-specific dependency lists

**Karpathy wiki repos** (where `index.md` is the main entry point):
  Add a minimal `README.md` that just points to `index.md`:
  ```markdown
  # Repo Name
  
  > Brief one-liner.
  
  👉 All content is in **[index.md](index.md)**.
  ```
  This avoids duplicating `index.md`'s content and keeps only one file
  to update when the catalog changes.

### Updating a File via API (No Local Clone)

When you need to update a file in a repo that has no local clone:

```python
import json, urllib.request, base64

# 1. Get the current SHA
req = urllib.request.Request(
    'https://api.github.com/repos/$OWNER/$REPO/contents/path/to/file.md',
    headers={'Authorization': f'token {token}', 'User-Agent': 'Hermes'}
)
with urllib.request.urlopen(req) as resp:
    sha = json.loads(resp.read())['sha']

# 2. PUT the new content with the SHA
payload = json.dumps({
    'message': 'commit message',
    'content': base64.b64encode(new_content.encode()).decode(),
    'sha': sha
}).encode()

req2 = urllib.request.Request(
    'https://api.github.com/repos/$OWNER/$REPO/contents/path/to/file.md',
    data=payload,
    headers={
        'Authorization': f'token {token}',
        'User-Agent': 'Hermes',
        'Content-Type': 'application/json',
        'Accept': 'application/vnd.github.v3+json'
    },
    method='PUT'
)
with urllib.request.urlopen(req2) as resp:
    result = json.loads(resp.read())
    print(f'Updated! SHA: {result[\"content\"][\"sha\"][:8]}')
```

The `PUT /repos/{owner}/{repo}/contents/{path}` endpoint requires the
current file's `sha` — fetch it first, then include it in the PUT body.
This is also the only way to update files in repos where you only have
an API token and no local clone set up.

### Forcing Push When Remote Has Conflicting Content

When a remote repo has old/incorrect content (e.g. a stale "Deprecated"
README) that conflicts with a local `git push`:

```bash
git pull --rebase     # if no conflict
# OR
git push -f origin main   # when you're certain your local is correct
```

Use `--force-with-lease` instead of `-f` when working on shared branches
to avoid overwriting others' work. For single-user repos, `-f` is fine.

### Pitfall — Verifying Push via raw.githubusercontent.com

`raw.githubusercontent.com/<owner>/<repo>/<branch>/<path>` URL can return
**404 for newly created files even when `gh api .../contents/...` shows
the file as present**. This is a known GitHub CDN propagation delay —
the underlying git tree is correct, but the raw-content CDN hasn't caught up
(takes seconds to a few minutes).

**Don't trust raw.githubusercontent.com as the verification path.** Use:

```bash
# ✅ Reliable verification — works immediately after push
git clone --depth 1 https://github.com/$OWNER/$REPO.git /tmp/verify
diff -r /local/path /tmp/verify/path

# ✅ Alternative — through GitHub API (uses git tree, not raw CDN)
gh api repos/$OWNER/$REPO/contents/$PATH --jq '.content' | base64 -d

# ❌ Unreliable immediately after create/push
curl -sI https://raw.githubusercontent.com/$OWNER/$REPO/main/$PATH | head -1
# → may show "HTTP/2 404" even when the file IS in the repo
```

**Diagnostic recipe** when in doubt:
```bash
# 1) Is file in tree? (always works)
gh api repos/$OWNER/$REPO/git/trees/HEAD?recursive=1 \
  --jq '.tree[] | select(.path == "scripts/foo.sh") | "  \(.path)  \(.size)B  sha=\(.sha[:8])"'
# → expect: scripts/foo.sh  1234B  sha=abc12345

# 2) Can API contents fetch it?
gh api repos/$OWNER/$REPO/contents/scripts/foo.sh --jq '.sha'
# → expect: abc12345...
# If both work but raw.githubusercontent.com 404s → CDN lag, wait or use clone test
```

Confirmed 2026-07-01: pushed a 5897-byte file via `gh repo create --push`,
`gh api .../contents/...` returned the file immediately and `git clone --depth 1`
matched local exactly, but `curl -sI https://raw.githubusercontent.com/.../main/scripts/...sh`
still showed `HTTP/2 404` after 90 seconds.

## 12. Repo Lifecycle Management (Archive, Delete, Cleanup)

Repos go through a lifecycle: **create → active → archive → (optionally) delete**. Archive is safe and reversible; delete is permanent and requires elevated token scope.

### Repo Consolidation / Migration Workflow

When the user has **overlapping repos** (e.g. `stock-analysis-toolkit` and `trading-agents-nuri-*`) and wants to **consolidate into one place**:

**Step 1: Audit — what's unique vs what's duplicate?**

```bash
# Clone the source repo
git clone https://github.com/$OWNER/old-repo.git /tmp/old-repo

# Compare scripts by md5 — if same, it's a duplicate
for f in /tmp/old-repo/scripts/*.py; do
  name=$(basename "$f")
  if [ -f "target-repo/$name" ]; then
    md5_old=$(md5sum "$f" | cut -d' ' -f1)
    md5_new=$(md5sum "target-repo/$name" | cut -d' ' -f1)
    if [ "$md5_old" = "$md5_new" ]; then
      echo "🟡 DUPLICATE: $name (identical)"
    else
      echo "🔴 DIFFERENT: $name (check which is newer)"
    fi
  else
    echo "🟢 UNIQUE: $name (doesn't exist in target)"
  fi
done
```

Classify each file:
- **🟢 UNIQUE** → move to target repo
- **🟡 DUPLICATE identical** → discard (skip)
- **🔴 DIFFERENT** → inspect both; keep the newer/superior version
- **🗑️ DEPRECATED** (obsolete methodology, e.g. `orbit_final.py`) → discard

**Step 2: Move unique files to target repo**

```bash
cp /tmp/old-repo/scripts/unique_file.py target-repo/
cd target-repo && git add -A && git commit -m "merge: old-repo 고유 스크립트 통합 — file1, file2" && git push
```

**Step 3: Update the old repo's README → redirect + archive**

Replace the old README with an archive notice containing a migration table:

```markdown
# 🗄️ Repo Name — **보관됨 (Archived)**

> **YYYY-MM-DD: 모든 내용이 `target-repo`로 통합되었습니다.**
> 이 리포지토리는 더 이상 유지보수되지 않습니다.

## 📦 Migration

| 이전 (이 repo) | 이후 (통합) |
|:--------------|:-----------|
| `old_script_a.py` | → [`target-repo/script_a.py`](https://github.com/owner/target-repo) |
| `old_script_b.py` | → **방법론 대체** |
| 문서/README | → [`target-repo`](https://github.com/owner/target-repo) |
```

**Step 4: Clean up deprecated files from old repo**

```bash
cd /tmp/old-repo
# Remove files that are duplicates, deprecated, or already moved
rm scripts/duplicate.py scripts/deprecated.py

# If ALL scripts are moved, remove the entire scripts/ directory
rm -rf scripts/

git add -A && git commit -m "cleanup: scripts 정리 (통합 완료)" && git push
```

**Step 5: Update main repo README with migration history**

Add a "통합 이력 — Legacy Repositories" section to the main README:

| 이전 리포지토리 | 상태 | 통합처 |
|:---------------|:----:|:-------|
| **`owner/old-repo`** | ✅ **보관 (Archived)** | → `target-repo` |
| → `deprecated_script.py` | 방법론 대체 | `new_script.py`로 완전 대체 |
| → `unique_script.py` | 📦 이동 | `target-repo/` |

> 기존 `old-repo` 리포지토리는 README에서 새 위치로 안내하며 아카이브 상태로 유지됩니다.

**Step 6: If the old repo is deleted — update ALL wiki cross-references**

After the user confirms and deletes the old repo, the `hermes-wiki` (and any wiki that referenced it) still has stale links. The deleted repo URL will 404. Fix every reference:

```bash
# 1. Search ALL wiki files for the old repo name
cd ~/.hermes/wiki
grep -r "old-repo" --include="*.md" . 2>/dev/null

# 2. Update each file found:
#    - index.md — submodule path, Repo Map table, Quick Reference table
#    - AGENTS.md — structure diagram if old repo was a submodule path
#    - README.md — submodules table and structure diagram
#    - infra/gh-token.md — Active Repos list
#    - infra/environment.md — Active Repos line
#    - infra/obsidian-github-sync.md — super repo submodule table
#    - code/*.md — script references that pointed to the old repo
#    - people/<user>.md — if user profile mentions the repo

# 3. Remove the old submodule from .gitmodules (if it was a submodule)
git submodule deinit -f path/to/submodule
git rm -f path/to/submodule
rm -rf .git/modules/path/to/submodule

# 4. Commit all changes together
git add -A && git commit -m \
  "cleanup: old-repo submodule 제거 + 모든 참조 → target-repo 으로 업데이트 (레포 삭제됨)" && git push
```

**Files most likely to have stale references (check all):**
| 파일 | 예상 참조 |
|:-----|:---------|
| `index.md` | submodule 경로, Repo Map 테이블, Quick Reference |
| `AGENTS.md` | 구조도 submodule 경로 |
| `README.md` | submodules 테이블, 구조도 |
| `infra/gh-token.md` | Active Repos 목록 |
| `infra/environment.md` | Active Repos 라인 |
| `infra/obsidian-github-sync.md` | super repo submodule 목록 |
| `code/scripts.md` | 스크립트 저장소 참조 |
| `people/*.md` | 사용자 프로필 |

**Pitfall — double pipes in patches + stale tables.** When patching markdown tables with `patch()` tool, the old_string/new_string can introduce extra `|` characters if the match boundary is off by one character. GH markdown tables use `||` prefix format — the match boundary easily includes/excludes one pipe, producing `|||` garbage. Always `read_file()` to verify after patching. If mangled beyond repair, `write_file()` the whole thing.

**Pitfall — super repo has separate .gitmodules + tree.** `hermes-wiki-super` is a GitHub repo separate from `hermes-wiki`. Its submodule entry for the deleted repo lives in two places:
1. `.gitmodules` file — can be updated via `PUT /repos/.../contents/.gitmodules` (standard file API)
2. The submodule entry in the git tree — must be removed via the Git Data API (create new tree without the submodule entry → create commit → update ref)

The simple `curl PUT` can fix `.gitmodules`, but removing the submodule tree entry requires the full tree API dance described in §12's GitHub tree manipulation approach.

**Why this matters:**
- Prevents stale forks/old commits from confusing future work
- Keeps the README migration table as a discoverable reference
- One `git pull` on target-repo gives everything the old repo had of value
- The archived repo stays accessible for history but makes the new location obvious

### Check a Repo's Current State

```bash
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO \
  | python3 -c "
import sys, json
r = json.load(sys.stdin)
print(f\"Name:       {r['full_name']}\")
print(f\"Archived:   {r['archived']}\")
print(f\"Private:    {r['private']}\")
print(f\"Pushed:     {r['pushed_at'][:10]}\")
print(f\"Created:    {r['created_at'][:10]}\")
print(f\"Size:       {r['size']} KB\")
print(f\"Default:    {r['default_branch']}\")
print(f\"Desc:       {r.get('description','-')}\")
"
```

### List All Repos (Active vs Archived)

Use this when the user asks "what repos do I have" or "which ones are stale":

```bash
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/user/repos?per_page=100&sort=updated&type=all" \
  | python3 -c "
import sys, json, urllib.parse
repos = json.load(sys.stdin)
for r in sorted(repos, key=lambda x: x['name']):
    status = '🗄️ ARCHIVED' if r['archived'] else '✅ ACTIVE'
    priv = '🔒' if r['private'] else '🌐'
    pushed = r['pushed_at'][:10] if r['pushed_at'] else '-'
    desc = (r.get('description') or '-')[:50]
    print(f'{status} {priv} {r[\"name\"]:45s} pushed:{pushed}  {desc}')
```

⚠️ **Token scope issue**: For fine-grained tokens, the list API may return empty (`[]`) even when repos exist. Use direct repo-specific API calls (per-repo endpoint) as fallback.

### Check What Token Scopes You Have

```bash
curl -s -I \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/user \
  | grep -i x-oauth-scopes
```

The `repo` scope grants read/write access but **NOT delete**. Deleting repos requires `delete_repo` scope.

### Archive a Repo (Safe, Reversible)

Archiving works with the standard `repo` scope — no elevated permissions needed:

**With gh:**
```bash
gh repo archive owner/repo-name
```

**With curl:**
```bash
curl -s -X PATCH \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO \
  -d '{"archived": true}'
```

Archiving makes the repo read-only: no pushes, no issues, no PRs. It stays visible and cloneable. Unarchive by setting `"archived": false`.

### Delete a Repo (Permanent!)

**Requires the `delete_repo` scope** on the token — the standard `repo` scope is NOT enough.

**With gh** (recommended — handles scope automatically if auth'd with sufficient permissions):
```bash
gh repo delete owner/repo-name --yes
```

**With curl** (only works if token has `delete_repo` scope):
```bash
curl -s -X DELETE \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO
```

**If you get 403 "Must have admin rights to Repository":**
- The token lacks `delete_repo` scope — the user must either:
  - **Generate a new token** at https://github.com/settings/tokens with `delete_repo` scope, OR
  - **Delete manually** via GitHub web UI: repo → Settings → Danger Zone → Delete this repository

### Stale Repo Detection Workflow

When asked to clean up repos:

1. **List all repos** (see above) — note pushed dates and archived status
2. **Check each repo's contents** — does it have active, unique content?
3. **Cross-reference with hermes-wiki** — is it referenced in `.gitmodules` or `index.md`?
4. **Recommend**: archive if content might be referenced, delete if truly superseded
5. **Execute**: archive first (safe), delete only after user confirms

### GitHub Web UI Reference

For operations the token can't do, guide the user to:
- **Archive**: repo → Settings → Danger Zone → "Archive this repository"
- **Delete**: repo → Settings → Danger Zone → "Delete this repository" (type name to confirm)

---

## 13. Multi-Repo Rename/Refactor Workflow

When a file, script, or function name changes and needs updating **across multiple repos**, don't just change it in one place — you must chase every reference or the cron jobs and cross-repo links will break silently.

**Trigger example:** User says "X_v3.py는 모두 v3빼주고 관련된 것 전부 X로 바꾸기" — rename a core file and update all references across every related repo.

### Step 1: Map all locations

Identify every file and repo that references the old name:

```bash
# Search all related repos
for repo in ~/trading-agents-nuri* ~/.hermes/wiki; do
  [ -d "$repo" ] && grep -rl "old_name" "$repo" --include="*.py" --include="*.md" --include="*.sh" 2>/dev/null
done
```

Common locations for a script rename:
| Where | What to change |
|-------|---------------|
| **Server scripts dir** | Rename the actual file |
| **Cron references** | Any cron scripts that call the old name |
| **Symlinks** | If legacy cron still references old name, create symlink |
| **Source repo** | Git mv + update internal references |
| **Other repos** | README.md, docs/*.md, config files |
| **Hermes wiki** | `code/scripts.md`, `infra/gh-token.md`, `index.md` |

### Step 2: Execute rename on server

```bash
# Rename the actual file
mv old_name.py new_name.py

# Create symlink for backward compatibility (legacy cron)
ln -s new_name.py old_name.py

# Verify
ls -la old_name.py new_name.py
```

### Step 3: Commit + push to all affected repos

```bash
for repo in repo1 repo2 repo3; do
  cd ~/$repo
  git add -A
  git commit -m "rename: old_name → new_name"
  git push
done
```

### Step 4: Verify no stale references remain

```bash
# Search everything again — should return nothing
grep -rl "old_name" --include="*.py" --include="*.md" --include="*.sh" \
  ~/trading-agents-nuri* ~/.hermes/scripts/ ~/.hermes/wiki/ 2>/dev/null
```

**Pitfall — cron jobs may still reference the old filename.** The fair_value cron (job_id from `cronjob(action='list')`) was registered with the old filename. After renaming, the cron's script path is hardcoded to `old_name.py`. The symlink workaround (`old_name.py → new_name.py`) prevents this from breaking immediately, but the cron job config should ideally be updated too.

**Pitfall — README still references old name.** The README of each affected repo may mention the old name in descriptions or examples. Search specifically for the old name in README.md files because they're the most visible and most often forgotten.

**Pitfall — diff-based rename tracking.** `git mv` preserves rename history; `mv` + `git add -A` does not. For single-file renames, use `git mv old_name.py new_name.py` which GitHub will correctly show as `R` in diffs. For the server file, `mv` + `git add -A` is fine since the cron repo tracks file content, not history.

**Real example (2026-06-06):** `fair_value_v3.py` → `fair_value.py`. Changed on: server (`mv` + symlink), `trading-agents-nuri-cron` (`git mv`), `trading-agents-nuri` (docs), `trading-agents-nuri-scripts` (internal references). All 3 repos pushed. Symlink created so existing cron (registered with `fair_value_v3.py`) continued working.

---

## Quick Reference Table

| Action | gh | git + curl |
|--------|-----|-----------|
| Clone | `gh repo clone o/r` | `git clone https://github.com/o/r.git` |
| Create repo | `gh repo create name --public` | `curl POST /user/repos` |
| Fork | `gh repo fork o/r --clone` | `curl POST /repos/o/r/forks` + `git clone` |
| Repo info | `gh repo view o/r` | `curl GET /repos/o/r` |
| Edit settings | `gh repo edit --...` | `curl PATCH /repos/o/r` |
| Create release | `gh release create v1.0` | `curl POST /repos/o/r/releases` |
| List workflows | `gh workflow list` | `curl GET /repos/o/r/actions/workflows` |
| Rerun CI | `gh run rerun ID` | `curl POST /repos/o/r/actions/runs/ID/rerun` |
| Set secret | `gh secret set KEY` | `curl PUT /repos/o/r/actions/secrets/KEY` (+ encryption) |

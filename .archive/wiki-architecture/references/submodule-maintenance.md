# Submodule Maintenance for hermes-wiki

> Common repair patterns for submodules in the shared wiki repo (`~/.hermes/wiki/`).

## Pattern 1: Broken Submodule — Empty/Inaccessible Checkout

**Symptom:** `git pull` fails with `"Could not access submodule '<name>'"` or `git submodule status` shows `-` prefix (not checked out).

**Root cause:** The submodule directory exists on disk as a plain directory, but the `git submodule init` or gitlink record is corrupt — often from a partial clone, a manually-created directory, or `logs/` being created before the submodule was initialized.

**Fix:**

```bash
cd ~/.hermes/wiki

# 1. Deinitialize (may fail — that's OK, it means config is already gone)
git submodule deinit -f -- logs 2>&1 || true

# 2. Remove the conflicting directory
rm -rf logs/

# 3. Initialize the submodule fresh (clones + checks out)
git submodule update --init logs
```

After repair, verify:
```bash
cd logs && git log --oneline -1  # should show a real commit, not "Could not access"
```

## Pattern 2: Detached HEAD in Submodule — Pushing Changes

**Symptom:** After committing in the submodule, `git push origin main` fails with:
```
error: src refspec main does not match any
```

**Root cause:** Submodules clone in a detached HEAD state by default. The branch may not be `main` — some repos (including `hermes-logs`) use `master`.

**Discovery:**
```bash
cd ~/.hermes/wiki/logs
git branch -a
# Example output:
# * (HEAD detached from e833c91)
#   master          ← the actual branch
#   remotes/origin/HEAD -> origin/master
#   remotes/origin/master
```

**Fix: push detached HEAD to the correct branch:**
```bash
git push origin HEAD:master   # use actual branch name, not 'main'
```

**To convert to a named branch for convenience:**
```bash
git checkout -b master        # create local branch at current HEAD
git push origin master        # now works with normal push
```

## Pattern 3: Branch Mismatch — `master` vs `main`

**Symptom:** `git submodule update --init` succeeds but the submodule is on `master` while the parent repo's `.gitmodules` specifies `main`.

**Rule of thumb for hermes-wiki submodules:**
| Submodule | Branch | Notes |
|:----------|:-------|:------|
| `logs` | `master` | Points to `mybotagent/hermes-logs.git` — uses `master` |
| `subagents-library` | `main` | Uses default GitHub `main` |

**Fix the submodule's branch tracking** (in `.gitmodules` or via CLI):
```bash
cd ~/.hermes/wiki
git config -f .gitmodules submodule.logs.branch master
```

## Pattern 4: Re-registering a Submodule After Manual Removal

If you manually removed a submodule's directory and `.git/modules/<name>/` config:

```bash
cd ~/.hermes/wiki

# Remove stale gitlink from index
git rm --cached logs

# Remove stale module config
rm -rf .git/modules/logs

# Re-register and clone fresh
git submodule add https://github.com/mybotagent/hermes-logs.git logs
```

## Verification Checklist

After any submodule repair:
- [ ] `git submodule status` shows no `-` prefix (all checked out)
- [ ] `cd <submodule> && git log --oneline -1` shows a real commit
- [ ] `cd <submodule> && git status` is clean (no modified content)
- [ ] `git pull --ff-only` in parent repo succeeds
- [ ] `git push` from parent repo succeeds (updated submodule pointer committed)

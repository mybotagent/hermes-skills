# Repo Deletion & Recovery Workflow

> When the user rejects repos you created — undo everything cleanly.
> Real session from 2026-05-31: `claude-skill-library` (rejected), `agents-library` (rejected),
> then `subagents-library` (third attempt, accepted — different from first two).

## Signal Detection

The user might say:
- "지워줬으면 좋겠어" (I want it deleted) — **you created unwanted artifacts**
- "기존내용은 지워줘" (Delete the existing content) — **same, stronger urgency**
- "그거 말고" (Not that, something else) — **you misunderstood the task**
- "아니 X는 내가 지울게" (No, I'll delete X myself) — **worst case: you wasted their time so much they'd rather do it themselves**

All four signals mean: stop immediately, undo everything, and figure out what they actually want before creating anything new.

> **Important:** Only delete repos that were truly rejected. If the user corrects your direction
> (e.g. "내말은 서브에이전트 말하는거야"), the second attempt may be correct — don't delete that one too.
> In the 2026-05-31 session, `claude-skill-library` and `agents-library` were rejected and emptied,
> but `subagents-library` (the third attempt, which was what the user actually wanted) was kept.
> Know when to stop deleting and start building.

## Step-by-Step

### 1. Stop Creating

Stop any in-progress repo setup. Do not push more content to repos the user doesn't want.

### 2. Clean Up hermes-wiki Submodules

```bash
cd ~/.hermes/wiki

# Remove submodule references
git rm <path-to-submodule>     # e.g. git rm agents-library
git commit -m "cleanup: remove <name> submodule"

# Revert index.md — remove any Quick Reference table entries added for these repos
# Edit index.md manually to delete the added rows

git add index.md
git commit -m "docs: revert <name> from quick reference"
git push origin main
```

### 3. Empty GitHub Repos

GitHub tokens with `repo` scope CANNOT delete repos (need `delete_repo` scope).
Workaround: force-push empty content.

```bash
# For each unwanted repo:
TMPDIR=$(mktemp -d)
cd $TMPDIR
git init --initial-branch=main
echo "# <repo> - Removed" > README.md
echo "This repo was created by mistake and is no longer in use." >> README.md
git add README.md
git commit -m "cleanup: remove repo"
git remote add origin https://github.com/mybotagent/<repo>.git
git push -f origin main
rm -rf $TMPDIR
```

The repos will still exist on GitHub (visible to user) but will contain only a
"Removed" README. If the user wants them fully gone, they can delete via GitHub UI:
Settings → Danger Zone → Delete this repository.

### 4. Delete Local Clones

```bash
rm -rf ~/.hermes/<repo1> ~/.hermes/<repo2>
```

Also clean up any temp files created during setup:
```bash
rm -rf /tmp/<repo>  # if you cloned there for reading
```

### 5. Clear Memory

```bash
memory(action='remove', old_text='<unique substring of the memory entry>')
```

### 6. Confirm with User

Report what was deleted/reverted. One line per action is sufficient:
- ❌ `agents-library` repo — emptied and removed from hermes-wiki
- ❌ `subagents-library` repo — same
- ❌ hermes-wiki submodule references removed
- 🧠 Memory cleaned

## Prevention

Before creating ANY repo, clarify if the user's request is ambiguous:

> "'Agents' — do you mean agent frameworks like LangChain/AutoGen, or sub-agents
> that run inside Claude Code, or something else?"

A 10-second question prevents 30 minutes of cleanup.

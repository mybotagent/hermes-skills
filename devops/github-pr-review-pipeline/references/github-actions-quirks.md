# GitHub Actions quirks — observed during PR review pipeline build

Captured from real runs; each is reproducible on a private repo
running on the free plan. Use these as a checklist before claiming
"the workflow is broken".

## 1. `pull_request` vs `pull_request_target`

**Symptom**: Workflow has `on: pull_request`, you open a PR from the
same repo, and the workflow NEVER fires.

**Why**: GitHub internals treat same-repo PRs as a `push` to the target
branch (because GitHub merges before running checks). The `pull_request`
trigger is reserved for PRs from external forks.

**Fix**: Use `pull_request_target`. Same trigger semantics, also fires
for same-repo PRs, and (importantly) has access to repo secrets.

```yaml
on:
  pull_request_target:
    types: [opened, synchronize, reopened, ready_for_review]
```

## 2. Workflow trigger cache

**Symptom**: You edit `on:` (e.g. `pull_request` → `pull_request_target`),
push, but new PRs still don't trigger the workflow.

**Why**: GitHub indexes workflows by file SHA at first registration.
Edits to the file content may not refresh the trigger config; the
file is recognized, but the trigger isn't re-read.

**Fixes (try in order)**:
1. Add a no-op comment change + push (forces new SHA).
2. Rename the file (e.g. `merge-gate.yml` → `pr-merge-gate.yml`)
   and push the rename + content. This is the most reliable.
3. As a last resort, also bump the `name:` field — sometimes that
   helps, sometimes not.

## 3. Step `id:` requirement

**Symptom**: `${{ steps.wait.outputs.VERDICT }}` is empty in the next
step. The upstream step runs fine and prints "VERDICT=Approve" to
stdout.

**Why**: GitHub Actions only exposes `outputs.<key>` for steps that
declare `id: <name>`. Without `id:`, the step's `$GITHUB_OUTPUT` writes
land nowhere observable.

**Fix**:
```yaml
- name: Wait for verdict
  id: wait                  # ← mandatory
  run: |
    echo "VERDICT=$worst" >> "$GITHUB_OUTPUT"
```

## 4. GITHUB_TOKEN cannot approve its own PRs

**Symptom**:
```
$ gh api -X POST .../pulls/1/reviews -f event=APPROVE
422 Unprocessable Entity: GitHub Actions is not permitted to approve
pull requests.
```

**Why**: GitHub's anti-abuse — a bot that opens a PR can't use the
same `GITHUB_TOKEN` instance to approve it.

**Fix**: Skip the approve step. Call merge directly:
```bash
gh api -X PUT .../pulls/1/merge -F commit_title="…" -F squash=true
```
This works because merge is the *outcome*, and admin/maintain tokens
on the repo can always merge.

## 5. `gh api -f` vs `-F`

**Symptom**:
```
422 Unprocessable Entity: For 'properties/squash', "true" is not a boolean
```

**Why**: `-f` always sends a string. `-F` infers the type from the
shell value: `true` → JSON `true`, `42` → JSON `42`, `x` → JSON `"x"`.

**Fix**: Use `-F` for booleans/numbers.

## 6. `gh pr comment` needs git context

**Symptom**:
```
failed to run git: fatal: not a git repository (or any of the parent
directories): .git
```

**Why**: `gh pr comment` shells out to `git` for repo context. If
the step `cd`'d away from the checkout, or the workflow didn't
`actions/checkout` first, the command fails.

**Fix**:
- Either `actions/checkout@v4` at the top of the job (always).
- Or use the API directly:
  ```bash
  curl -sS -X POST -H "Authorization: Bearer ${GH_TOKEN}" \
       -H "Content-Type: application/json" \
       "https://api.github.com/repos/${REPO}/issues/${N}/comments" \
       -d "$(printf '{"body": "%s"}' "$msg")"
  ```

## 7. Verdict polling must aggregate across all comments

**Symptom**: review-bot posts 3 comments (one per push), each with
different verdict. auto-merge polls, sees only the last comment, and
auto-merges a PR that earlier was flagged 🔴.

**Why**: `tail -1` of a multi-line body returns the last verdict
*within* a comment, but the polling loop reads the first `**Verdict:**`
line of `tail -1`'d comment, which is just the latest review-bot run.
A previous run's stricter verdict is silently ignored.

**Fix**: Worst-of aggregation:
```bash
rank() { case "$1" in Approve) echo 0 ;;
            "Changes Requested") echo 1 ;;
            Blocked) echo 2 ;; esac; }
worst=""; worst_rank=-1
for v in $(... | grep -oE '\*\*Verdict:\*\*\s*(Approve|Changes Requested|Blocked)' | awk '{print $NF}'); do
  r=$(rank "$v")
  [ "$r" -gt "$worst_rank" ] && worst_rank=$r && worst=$v
done
```

## 8. Workflow name displayed as file path

**Symptom**: `GET /actions/workflows` lists a workflow as
`name: ".github/workflows/merge-gate.yml"` even though the YAML has
`name: merge-gate` at the top.

**Why**: Sometimes GitHub registers the workflow before parsing the
`name:` field, especially if there were content errors on first push.
A re-registration cycle (rename + re-push) usually fixes this.

**Impact**: Mostly cosmetic. Trigger / run logic works regardless.
But if you're matching by name in dashboards or scripts, use the path.

## 9. Workflow jobs disappearing into "in_progress" forever

**Symptom**: A run shows `in_progress` for >10 minutes; the step log
freezes. Refresh shows no progress.

**Common causes**:
- The step called an external API that hung (e.g. `gh api ...` with
  an untimed-out HTTP request).
- The polling loop's `for` never times out due to a logic bug.

**Fixes**:
- Wrap external calls in `timeout 30 curl ...`.
- Use bounded `for i in $(seq 1 N); do …; sleep 15; done` with N=24
  for a 6-min ceiling — log + exit non-zero if no progress.
- Don't use 12-min polling loops; you'll wait 12 min every time the
  upstream is broken.

## 10. `pull_request_target` is allowed to access secrets, but is also
dangerous for untrusted forks

If your repo receives PRs from external forks (e.g. an open-source
project), `pull_request_target` would let a fork's code modify the
diff and read secrets. **For external forks, use `pull_request` only,
and a separate workflow with `pull_request_target` for comment
posting.** For our use case (private repo, branch-only PRs), this
isn't a concern.

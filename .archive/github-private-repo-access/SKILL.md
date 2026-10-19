---
name: github-private-repo-access
description: "Diagnose '404 but the user says it exists' GitHub access failures — the private/collaborator case. Load IMMEDIATELY when user mentions collaborator/collabo/invitation/invite/accept alongside a GitHub URL, or pushes back on a 404 ('존재하는데?', '오너 다름', '왜접근불가', '너가해', '공개로 바꿈', 'I have access'). Covers 404 disambiguation, escape hatches (public/fork/PAT), and the user's common confusion points."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [GitHub, Private Repos, Collaborator, 404, Access Control, PAT]
    related_skills: [github-repo-management, github-auth]
---

# GitHub Private/Collaborator-Only Repo Access

A focused class-level skill for the recurring failure mode where the user hands you a `https://github.com/<owner>/<repo>` URL, claims they accepted a collaborator invite, but you get HTTP 404 from every angle. This skill covers the **diagnosis recipe** and the **three escape hatches** to surface in the first reply — before wasting turns re-running the same checks.

**Companion to `github-repo-management`** (which covers cloning, forking, settings in general). This skill is specifically about the access boundary case.

---

## When to Load This Skill

Trigger when **any** of these signals appear:

- User says "방금 accept했어 / I just accepted the invite / I have collaborator access"
- User hands you a URL and asks you to clone/work with it, but `git clone` returns 404
- `curl https://github.com/<owner>/<repo>` returns HTTP 404 with title `"Page not found · GitHub"`
- API `GET /repos/<owner>/<repo>` returns 404 or empty results
- `gh search repos` returns nothing
- User asks "왜접근이 불가하지 / why can't you access it?" after you report a 404
- User says "공개로 바꿈 / I made it public / fork해줘 / fork it" in response to an access failure
- User asks to **flip visibility** for a repo: "public으로 전환 / private으로 / make public / 공개 전환"
- User asks to **clean before going public**: "공개할거 검수 / public으로 가기전 정리 / 알아서 정리 / 권장 정리 / gitignore 처리"
- User sees 403 on `PATCH /repos/...` with `"Resource not accessible by personal access token"` (visibility/admin endpoints need elevated PAT)

---

## Why This Failure Mode Is So Common

The fundamental issue: **GitHub returns the same HTTP 404 for "private repo you can't see" as for "repo that doesn't exist."** It deliberately does not distinguish these cases for non-authenticated callers.

So when the user says "초대 accept했어" and you get 404, three things are simultaneously true:
1. The user has access via their logged-in browser session.
2. You do **not** have access because you're not authenticated as them.
3. The repo looks identical to "doesn't exist" from your vantage point.

The user, who can see the repo fine, reads your "not found" report as a factual error → frustration loop ("존재하는데?" / "왜접근이 불가하지" / "오너 다름").

---

## Diagnosis Recipe — Run Before Giving Up

### Step 0: Do you already have a token? Check FIRST.

**Critical lesson (2026-07-05):** If `~/.git-credentials` contains a GitHub token and you're still getting 404 from anonymous probes, **you probably need to *use* the token, not get a new one.** GitHub returns 404 (not 401) for anonymous raw fetches of private repo content — this silently masks a "working token, just not sent" situation as a "missing repo" problem.

```bash
# Check ~/.git-credentials (multi-format possible)
cat ~/.git-credentials 2>/dev/null
# Expected formats:
#   https://mybotagent:ghp_XXXX@github.com
#   https://x-access-token:ghp_XXXX@github.com
#   https://oauth2:ghp_XXXX@github.com

# Extract the active token (handles all three formats)
TOKEN=$(grep -E 'github\.com' ~/.git-credentials 2>/dev/null \
  | head -1 \
  | sed -E 's|^https?://[^:]+:||; s|@github\.com.*||')
echo "token: ${TOKEN:0:8}... (len=${#TOKEN})"

# Verify the token actually authenticates
curl -s -H "Authorization: token $TOKEN" "https://api.github.com/user" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('login:', d.get('login'), '| id:', d.get('id'))"
```

If `login` matches your expected owner → token works. If 401 → token expired/revoked (rotate via Option C). If no token at all → skip to step 1 of the diagnosis recipe.

**Once authenticated, send the token on EVERY GitHub API / raw fetch.** Anonymous raw.githubusercontent.com fetches of private content return 404 by design — easy to misdiagnose as "repo missing."

### Step 1-4: Anonymous diagnosis (only meaningful if no token)

```bash
# 1. Confirm HTTP 404 (not network error / DNS / something else)
curl -sL -o /dev/null -w "HTTP: %{http_code}\n" "https://github.com/$OWNER/$REPO"

# 2. Get the 404 page title — "Page not found · GitHub" confirms "definitely not here"
curl -sL "https://github.com/$OWNER/$REPO" | grep -oE "<title>[^<]+</title>" | head -1

# 3. Owner sanity check — does the owner have ANY public repos at all?
curl -sL "https://api.github.com/users/$OWNER/repos?per_page=5" | python3 -c "
import sys, json
d=json.load(sys.stdin)
if isinstance(d, dict): print('msg:', d.get('message'))
else:
    print(f'public repos visible: {len(d)}')
    for r in d[:3]: print(f'  - {r[\"name\"]}')"

# 4. Search the owner for the repo by name (search also hides private)
curl -sL "https://api.github.com/search/repositories?q=$REPO+user:$OWNER" \
  | python3 -c "import sys,json; print('search hits:', json.load(sys.stdin).get('total_count',0))"
```

If all four show no results → **private repo, you don't have access from this machine.** Stop searching and pivot to escape hatches.

---

## The Three Escape Hatches — Present in First Reply

| # | Escape hatch | User effort | When to suggest first |
|---|---|---|---|
| **A** | **Make it public** — Settings → General → Danger Zone → "Make public" | 30 sec | Repo is non-sensitive; user has admin rights |
| **B** | **User forks it to their own account, gives you the URL** | 30 sec | User wants to keep it private; doesn't want to share a token |
| **C** | **User generates a PAT** (classic, `repo` scope) and pastes it | 1 min | Fastest path; user is OK with paste-and-revoke |

**Always present all three** and let the user pick. Don't iterate one at a time.

### Option A — Make it public (simplest)

Walk the user through:
1. https://github.com/<owner>/<repo> (they can see it; you can't)
2. Settings tab (top right area)
3. Scroll all the way down to **Danger Zone**
4. Click **"Make public"** → confirm → wait 30–60s for GitHub propagation

After they confirm, re-run step 1 of the diagnosis recipe. You should see HTTP 200 + repo title in the page title tag.

#### Option A.1 — Pre-Public Content Audit (REQUIRED before flipping visibility)

**Hard lesson (2026-07-14):** When the user says "공개로 전환해줘" / "make it public", do NOT just flip the toggle. **Audit the repo contents first.** A repo that has been happily private for months usually contains:

| Category | Examples | Why it leaks |
|----------|----------|--------------|
| **Editor/IDE state** | `.obsidian/workspace.json`, `.vscode/settings.json`, `.idea/workspace.xml` | Absolute paths, recent file lists, OS username, project tree |
| **Personal tool config** | `.claude/settings.json`, `.claude/hooks/*` (often contains `bash '/Users/<name>/...'` in hook commands) | User identity, MacBook absolute paths, working directory leaks |
| **External content / clippings** | `Clippings/`, `bookmarks/`, `readlater/`, downloaded PDFs, scraped articles | Copyright risk + personal curation patterns |
| **`.gitmodules` pointers** | URL list of all submodules | Reveals what other private repos exist in the ecosystem (content stays private, but names leak) |
| **`.env*`, secrets**, **local scripts with hardcoded tokens** | obvious | Token/credential exposure |
| **Personal notes / journals** | Anything in `notes/`, `journal/`, `daily/` | Internal thinking, plans, people |

**Audit recipe (run this before PATCH):**

```bash
# 1. Clone fresh into /tmp
git clone https://github.com/<owner>/<repo>.git /tmp/<repo>-audit
cd /tmp/<repo>-audit

# 2. List everything tracked
git ls-files | wc -l
git ls-files

# 3. Hunt for identity leaks (Linux paths, usernames, MacBook paths)
git ls-files | xargs -I{} sh -c 'echo "=== {} ==="; cat "{}"' 2>/dev/null \
  | grep -nE "(/Users/[a-z]+|/home/[a-z]+|/Users/sanghee|MacBook|C:\\Users)" | head -20

# 4. Hunt for secrets / tokens
git ls-files | xargs grep -lE "(ghp_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,}|AKIA[A-Z0-9]{16})" 2>/dev/null

# 5. Check for copyrighted scraped content
git ls-files | xargs file 2>/dev/null | grep -E "(PDF|HTML|markdown)" | grep -iE "(clippings|bookmarks|scraped|readlater)"

# 6. Check submodule pointers
cat .gitmodules
```

**Clean recipe — `.gitignore` + `git rm --cached`:**

```bash
# 1. Update .gitignore to block these categories going forward
cat >> .gitignore <<'EOF'

# Pre-public cleanup (2026-07-14)
.obsidian/
.claude/
Clippings/
*.swp
EOF

# 2. Remove from git tracking but KEEP local files on disk
git rm --cached -r .obsidian/ .claude/ Clippings/

# 3. Verify staged deletions
git status | grep "deleted:"

# 4. Commit + push (so the audit-clean version is what's visible after the flip)
git add .gitignore
git commit -m "chore: gitignore sensitive paths before public release"
git push origin main
```

**Then flip visibility** (PATCH /repos/{owner}/{repo} with `{"private": false}`) — the user or browser session does this since **PATs without admin scope get 403** (see below).

#### Option A.2 — PAT 403 on Visibility PATCH (agent-side hard limit)

```bash
# This WILL 403 with a normal `repo`-scope PAT:
curl -X PATCH -H "Authorization: Bearer $TOKEN" \
  -d '{"private": false}' \
  https://api.github.com/repos/<owner>/<repo>
# → {"message":"Resource not accessible by personal access token","status":"403"}
```

**Why:** GitHub's API requires `repo` scope **AND** admin-level access on the target repo for visibility changes. Classic PATs (`ghp_*`) typically lack the elevated admin grant; fine-grained PATs need `Administration: Write`. The same applies to `gh repo edit --visibility public` (it uses the same API).

**Fallback (the only option from the agent):** Tell the user to flip it manually in the browser. Provide the exact URL and step list:

```
👉 https://github.com/<owner>/<repo>/settings
   → scroll to Danger Zone (bottom)
   → "Change repository visibility" → "Make public"
   → type repo name to confirm → password prompt
```

**Don't burn turns trying token rotation, re-PATCHing with different scopes, or `gh` CLI flags** — they're all going to 403 for the same reason. Once the user confirms the flip, verify with `gh repo view <owner>/<repo> --json visibility` (read-only, works with any token).

### Option B — User forks, gives you the URL

1. User opens https://github.com/<owner>/<repo> in their browser
2. Clicks **Fork** (top right)
3. Selects their own account as destination
4. Waits ~5s for the fork to complete
5. Sends you the fork URL: `https://github.com/<their-account>/<repo>`

You can now `git clone` the fork directly — public forks are visible to everyone.

### Option C — PAT (Personal Access Token)

1. User goes to https://github.com/settings/tokens/new
2. **Generate new token (classic)**
3. Note: anything (e.g. `hermes-clone`)
4. Expiration: user's choice
5. Scopes: **`repo`** (required for clone of private repos)
6. Generate → copy the token (shown once)
7. Pastes token to you

You then clone via token-embedded URL:
```bash
git clone https://<TOKEN>@github.com/$OWNER/$REPO.git
```

**Use the token minimally.** Clone only — never push to the user's repos unless they explicitly request it. Discard from memory when the task is done.

---

## Anti-Patterns — Things to NOT Do

- ❌ **Re-run the same 404 check multiple times in different forms.** After 1 curl + 1 API search, pivot to escape hatches. Each redundant check burns a turn and frustrates the user.
- ❌ **Tell the user "the repo doesn't exist"** when you mean "I can't see it." Present it as a question: "I get 404 from my side. Could the repo be private?"
- ❌ **Ask the user to re-accept the invite.** They already did — that's why they're confused.
- ❌ **Suggest `gh auth login` repeatedly** if they already tried it on their end. The issue isn't your auth; it's the access boundary.
- ❌ **Spend 4+ turns on this** before pivoting to escape hatches. The pivot should happen on turn 1 or 2.

---

## Confirmation Pattern — When User Says "공개로 바꿈 / I made it public"

After the user flips the visibility:

```bash
# Quick re-check — should now be 200
curl -sL -o /dev/null -w "HTTP: %{http_code}\n" "https://github.com/$OWNER/$REPO"

# Title check — repo title now appears (not "Page not found")
curl -sL "https://github.com/$OWNER/$REPO" | grep -oE "<title>[^<]+</title>" | head -1
```

If still 404 after the user says they changed it:
- GitHub propagation can take 30s–2min
- Ask them to hard-refresh the browser and verify the repo shows 🌐 (Public) icon in their repo list
- If the icon still shows 🔒 (Private), they may have toggled the wrong repo

**Confirmed pattern (2026-07-03):** User said "방금 invitation accept했어" → I ran 4+ turns of 404 + API search + variant URL checking ("오너 다름", "다른 오너") before the user said "공개로 바꿈" and the diagnosis flipped. The pivot to escape hatches should have been turn 1, not turn 5.

---

## Quick Decision Tree

```
User hands you a GitHub URL → try clone
├─ ✅ Works → proceed normally
└─ ❌ 404
   ├─ Already tried gh auth / set token? → No: ask them to set token (Option C)
   └─ Yes
      ├─ Repo is meant to be private?
      │  ├─ User can flip to public (non-sensitive)? → Suggest Option A first
      │  └─ Must stay private? → Suggest Option B (fork) — keeps repo private
      └─ Still ambiguous? → Present all three, let user pick
```

## Real-Session Failure Mode (load this skill on turn 1, not turn 5)

The session that produced this skill followed a 5-turn loop that exactly matched the frustration pattern:

| User turn | What user said | What I should have done | What I did instead |
|---|---|---|---|
| 1 | "sh-ai-x/analyze-trust-suite 데이터 분석 테스트" | **Load this skill immediately** — invite/collabo signal present | Cloned URL → 404, retried variant URLs |
| 2 | "다시해볼래? invitation 지금 accept함" | **Pivot to escape hatches** (Option A/B/C) | Re-ran the same probes |
| 3 | "오너 다름" | Confirmed ambiguity; present all 3 options | Searched API for owner |
| 4 | "왜접근이 불가하지 pm prd fast는 잘 됬잖아" | **Stop and apologize** — explain private/collaborator boundary | Explained why public works vs private doesn't |
| 5 | "포크해서 하면 되지않음?" / "너가해" | "I don't have auth on your account; please Fork and paste URL" | Explained I can't fork on their behalf (this IS the right answer, but came too late) |
| 6 | "공개로 바꿈" | Quick re-check → 200 → proceed | Quick re-check → 200 → proceed ✅ |

**Net cost: 4 wasted turns between message 1 and the right diagnosis.** The pivot to escape hatches belongs in message 2, not message 6.

## Trigger phrases to scan for in EVERY user turn that mentions a GitHub URL:

- "accept했어" / "방금 초대" / "invitation"
- "콜레보레이터" / "collabo" / "collaborator"
- "오너 다름" / "다른 사람" / "private인데"
- "존재하는데?" / "왜접근이 불가하지" / "왜 404"
- "너가해" / "fork해줘" / "공개로 바꿈"
- "pm prd fast는 잘 됬잖아" / "다른 레포는 됐는데" (comparing public success to private failure)
- "어제 push 됐는데" / "GitHub에 보이는데" / "다른 세션에서는 됐는데" (recent successful push but new fetch fails — token NOT being sent)
- **Visibility flip / pre-public audit signals:** "public으로 전환" / "private으로" / "make public" / "공개 전환" / "공개할거 검수" / "알아서 정리" / "권장 정리" / "gitignore 처리" / "publish 전 정리"
- **Admin endpoint 403:** "Resource not accessible by personal access token" on PATCH/DELETE → elevated PAT required

If ANY of these appear, this skill applies — load it and pivot to escape hatches on the next turn, no more probes.

## Related References

- [references/verify-after-push.md](references/verify-after-push.md) — After `git push`, the 4-layer verification recipe (ls-remote → API contents → raw byte check → vision_analyze) for confirming artifacts actually landed and render correctly on GitHub. Covers the "anonymous raw fetch returns 404 even with valid token" trap.
- [references/pre-public-audit-2026-07-14.md](references/pre-public-audit-2026-07-14.md) — Verbatim transcript of the hermes-wiki-super pre-public audit. Concrete leak checklist (`.obsidian/workspace.json`, `.claude/settings.json`, `Clippings/processed/*`), the exact `gitignore + git rm --cached` recipe used, and the user's tone signal ("알아서 정리해" = executive-mode green light, don't re-ask).
# Pre-Public Audit Session — 2026-07-14

Source session: hermes-wiki-super visibility flip request.

## Verbatim user-message sequence

```
[user] hermes-super-wiki만 public repo로 전환
[user] 사실 그냥 레포 공개 가능한데 문제있나 공개하며 안되는 내용이 포함되었다던지 검수해봐
[user] 권장 정리 -> 또는 Clippings -> gitignore 처리  아아서 정리해
[user] 알아서 정리
```

## What I did right

1. Loaded `~/.git-credentials` and used `Bearer` token (not the `x-access-token:` URL-embedded form that breaks `gh CLI`).
2. Full repo listing (`gh api user/repos?per_page=100`) — found 37 repos, 9 public.
3. **Audited before flipping** — went into `hermes-wiki-super` tree via `GET /git/trees/HEAD?recursive=1`, then `GET /contents/<file>` for sensitive-looking paths.
4. Listed exactly what would leak: `.obsidian/workspace.json` (sanghee + MacBook paths + 38 recently-opened files), `.claude/settings.json` (hook with `/Users/sanghee/...`), `Clippings/processed/*` (11 copyrighted scrapes).
5. Presented the audit + 3 options (proceed / cleanup / abandon) as `clarify` options. User picked "권장 정리 + 알아서 정리해".
6. Clean recipe: `gitignore` + `git rm --cached -r` → commit `932c5c3` → push succeeded.
7. Tried `PATCH /repos/{owner}/{repo} private:false` → 403. **Did NOT burn extra turns** trying alternate scope flags or token rotation — went straight to "user does the Danger Zone flip manually."

## What I should have done better

- I did NOT present the "PAT 403" reality check in the first reply. Should have pre-warned: "I'll handle the cleanup, but the visibility flip itself must be done in your browser because PATs lack admin scope." This would have saved the post-cleanup "what now?" question.
- I used `clarify` to ask permission for cleanup when user had ALREADY said "알아서 정리해" in the prior turn. One redundant turn.

## Concrete leak checklist for future pre-public audits

When auditing a private repo for public-readiness, scan for these filenames FIRST (they almost always leak):

| Path pattern | What leaks |
|--------------|------------|
| `.obsidian/workspace.json` | OS username, MacBook absolute paths, every open tab title, recently-opened file list (38 in this case) |
| `.obsidian/app.json` / `appearance.json` / `graph.json` | Vault metadata, theme, graph layout |
| `.obsidian/plugins/*/data.json` | Plugin config (which plugins you use, sync settings) |
| `.claude/settings.json` | Hook commands with `/Users/<name>/...` paths baked in |
| `.claude/commands/*.md` | Personal slash-command prompts (often OK to publish but worth asking) |
| `Clippings/processed/*` | Copyright risk + personal curation patterns |
| `.gitmodules` | Names of all sibling private repos (content safe, names leak) |
| `*.html` / `*.pdf` / `*.json` at root with no clear purpose | Often leftovers from web scraping / API debugging |
| `google_client_secret.json` / `google_token.json` / `*.pem` / `id_rsa*` | OAuth credentials, SSH keys — ALWAYS remove |
| `venv/`, `node_modules/`, `__pycache__/` | Usually already gitignored but worth checking |

## Verification recipe post-cleanup

```bash
# 1. Local files still exist (--cached doesn't delete disk)
ls -la .obsidian/ .claude/ Clippings/

# 2. Git no longer tracks them
git ls-files | grep -E "(\.obsidian|\.claude|Clippings)" || echo "✅ clean"

# 3. .gitignore covers them
grep -E "^(\.obsidian|\.claude|Clippings)" .gitignore

# 4. Push the audit-clean version before visibility flip
git push origin main
```

## User's tone signal worth keeping

User said "알아서 정리해" — **executive-mode green light**. When the user has explicitly delegated ("알아서", "너가 알아서", "그냥 해", "네가 결정해"), do NOT use `clarify` again to ask for permission. Just run the safe recipe and report back. The clarification has already happened.

The exception: when the action is irreversible (visibility flip, force push, secret deletion, paid API call) — those still need explicit confirmation even in "알아서" mode. Visibility flips fall into this category, so the right move is "audit + cleanup autonomously, but ask one final time before the irreversible flip itself."

## What "권장 정리" means in this user's lexicon

"권장 정리" (recommended cleanup) = "I'll defer to your judgment on what to remove." Combined with the follow-up "알아서 정리해", this is a CLEAR signal that:
- Don't ask again whether to remove things
- Pick the conservative option (gitignore, not delete)
- Keep local copies intact
- Commit + push + report what was removed

The gitignore-preserve-on-disk recipe (`git rm --cached -r`) is the exact technical pattern that fits this directive.
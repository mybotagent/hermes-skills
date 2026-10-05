# GitHub Pages Stuck-Build Diagnosis — 2026-07-03 Reproduction Recipe

> Companion to `deck-portfolio-site` SKILL.md §Pitfalls → "Pages build stuck — diagnose with five signals".
> This file captures the exact session transcript where a clean git push produced zero CDN update, and the five-step probe that turned a mystery into a known GitHub incident.

## Symptom

After `git push origin main`, the user reports "변화 없음" (no change visible). Symptoms:

- `git ls-remote origin main` returns the new commit hash ✅ (repo is fine)
- `curl -I https://<user>.github.io/<repo>/<deck>/index.html` shows `last-modified: <GMT 2+ hours BEFORE push>`
- `age:` counter keeps incrementing → CDN is serving an old build
- Multiple empty commits + timestamp markers in `index.html` → no change in CDN behavior

## Diagnosis (Five-Step Probe)

Run these in order. **Stop trying to fix the repo if step 3 returns positive.**

### Step 1 — Confirm git is fine

```bash
git ls-remote origin main
# Output: <new-commit-sha>	refs/heads/main
```

If the SHA matches your local HEAD, your repo push succeeded. Move on.

### Step 2 — Inspect build state via GitHub API

```bash
TOKEN=$(grep "mybotagent:" ~/.git-credentials | sed 's|https://mybotagent:||' | sed 's|@github.com||')
curl -s -H "Authorization: token $TOKEN" \
  "https://api.github.com/repos/<owner>/<repo>/pages/builds/latest"
```

Fields to read:

| Field | Meaning |
|---|---|
| `status: queued` | Build hasn't started. Trigger another. |
| `status: building` + `duration: 0` | Build started but stuck (CPU < 1ms). Hang. |
| `status: building` + `duration > 30000` | Build running normally. Wait. |
| `status: errored` + `error.message: "Page build failed."` | Build started and crashed. Check HTML syntax. |
| `status: built` + `duration > 1000` | Successful build. CDN should refresh. |

### Step 3 — Check GitHub-wide incident

```bash
curl -s https://www.githubstatus.com/api/v2/summary.json | python3 -c "
import sys, json
d = json.load(sys.stdin)
for c in d.get('components', []):
    if c.get('name') == 'Pages':
        print('Pages status:', c.get('status'))
        break
print()
for inc in d.get('incidents', []):
    print('[{}] {}'.format(inc.get('status'), inc.get('name')))
    for u in inc.get('incident_updates', [])[:1]:
        print('  →', u.get('body','')[:200])
"
```

Output from the actual 2026-07-03 session:

```
Pages status: degraded_performance

[investigating] Incident with Pages
  → We are investigating reports of slow and failing Pages deployments. Access to Pages is unaffected.
```

**This is the smoking gun.** When you see `degraded_performance` + active incident, the issue is **NOT your repo**. Stop. Report to user.

### Step 4 — Last-resort trigger (use sparingly)

If steps 1-3 show repo OK + Pages incident OR genuine local hang, ONE trigger is OK:

```bash
TOKEN=$(grep "mybotagent:" ~/.git-credentials | sed 's|https://mybotagent:||' | sed 's|@github.com||')
curl -s -X POST -H "Authorization: token $TOKEN" \
  "https://api.github.com/repos/<owner>/<repo>/pages/builds"
# Output: {"status": "queued", "url": "..."}
```

**Then poll the result.** Don't fire-and-forget:

```bash
sleep 30
curl -s -H "Authorization: token $TOKEN" \
  "https://api.github.com/repos/<owner>/<repo>/pages/builds/latest" | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print(f'status={d.get(\"status\")} duration={d.get(\"duration\")}')"
```

If it stays `building` with `duration: 0` → GitHub Pages is genuinely stuck. Another trigger won't help. Report and stop.

### Step 5 — Report to the user

Template that worked (2026-07-03):

```markdown
✅ 작업 완료 요약

저장소: mybotagent/hermes-architecture-deck
Commit: ff48536 — push 성공
파일: decks/memory-pipeline/index.html (9793 → 10086 bytes, +37 / -41 lines)

### 로컬 검증 (모두 통과)
- 채니봇: 0건
- 한글: 0건
- html lang: en
- '끝' 슬라이드: 0건
- 새 슬라이드 'End-to-End': 있음

### ⚠️ GitHub Pages 배포
- Commit은 push 완료: ff4853620b
- GitHub API commit SHA 일치 확인
- GitHub Pages CDN은 여전히 옛 버전 (9793 bytes) 서빙 중
- last-modified: Thu, 02 Jul 2026 14:08:07 GMT (commit은 16:49:52Z)

### 🚨 진단 결과 (GitHub 측 incident)
- Components[name=Pages].status = degraded_performance
- Active incident: "Incident with Pages" (investigating)
- 출처: https://www.githubstatus.com

→ 사용자 측에서 해결 불가. GitHub Pages 인프라 일시적 장애.
```

**Key elements**:
1. Lead with what you actually completed (commit SHA, file diff stats, `git ls-remote` hash).
2. Be explicit about what is blocked on infrastructure vs what is in your control.
3. Cite https://www.githubstatus.com so the user can verify themselves.
4. **Do not apologize** for the platform. State facts.
5. Suggest a wait window (typical incident recovery: 30 min - 2 hours).

## Token Extraction (security-safe pattern)

⚠️ **Important**: Don't embed the PAT in a `curl -H "Authorization: token ghp_..."` command — Hermes's security scanner will redact it and the call will fail with 401. Always read from git credentials:

```bash
# Extract from .git-credentials (POSIX-safe)
grep "github.com" ~/.git-credentials | head -1 | \
  sed 's|https://[^:]*:\([^@]*\)@.*|\1|'

# Or from .env if you keep one
grep "^GITHUB_TOKEN=" ~/.hermes/.env | head -1 | cut -d= -f2 | tr -d '\n\r'
```

Store in a shell variable, then reference `$TOKEN` in subsequent calls.

## Lessons Embedded in deck-portfolio-site SKILL.md

1. **Pitfall: "Pages build stuck — diagnose with five signals"** — the recipe above, condensed.
2. **CDN header sanity-check** — what `last-modified` / `cache-control` / `age` / `x-proxy-cache` actually mean.
3. **Reporting template** — what to lead with when telling the user "platform issue, not your issue".

These get reapplied automatically the next time any deck-portfolio-site session hits a stuck-Pages symptom.
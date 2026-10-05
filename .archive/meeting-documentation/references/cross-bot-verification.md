# Cross-Bot Sandbox Verification — Paste Protocol & File Proof

> Session-specific reference for the **Gate 1 verification pattern** that emerged in the 2026-06-30 data analysis 3-proposal debate (chatni + plannerbot + dsbot in Discord).
>
> 핵심 교훈: **"본인 인증 ≠ verification"** — 각 봇은 별도 sandbox/VM에서 활동하므로 cross-bot file read는 architecturally impossible. 모든 합의 보고는 본문 inline paste로 검증 가능하게 만들어야 한다.

---

## 1. 왜 이 패턴이 생겼나 (2026-06-30 timeline)

| 시점 | 사건 | 교훈 |
|------|------|------|
| T1 | chatni가 design.md v1 작성 + path 보고 (`~/projects/portfolio-2026-track-b/track-da/design.md`) + "✅ 완료" status 주장 | "✅ 완료" status 단정이 process integrity 가정에 의존 → 다른 봇들이 read 불가 |
| T2 | dsbot 반응: "본인 인증 = verification 동의 불가. cross-bot verification = process integrity" → Gate 1 paste 요청 | 봇들이 summary-only acceptance 거부 |
| T3 | plannerbot 동조: "sandbox isolation accepted with caveat — 채니봇 path-universal claim 시 격차 pre-disclose 의무" | universal path claim 금지 |
| T4 | chatni paste 송출 (§4 + §5 + §6 본문) → Gate 1 closed | 본문 가시 = verification |
| T5 | dsbot verify ✅ → "active now" 상태 전환 → aiprofit 결정 가능 | Gate 통과 후에만 commit 가능 |

**핵심**: 봇 3개 합의의 가치 = **직접 read OR paste = evidence-based**. summary-only = single-source-of-truth = 보류.

---

## 2. Sandbox 격차 — architecture

각 봇 = 별도 VM / working directory:

```
plannerbot (Claude)  → ~/dev/projects/plannerbot/
dsbot (DeepSeek)     → ~/dev/projects/dsbot/
chatni (Hermes/M3)   → ~/projects/portfolio-2026-track-b/
```

→ cross-sandbox file read = **architecturally impossible** (네트워크 격리 / 권한 격리).

**함정**: "✅ 파일 만들었어" → 다른 봇 read 불가 = **process integrity 결손**. 본 paste 의무.

**보고 의무**: sandbox 격차 있음을 **사전 disclose** (path-universal claim 금지).

---

## 3. Gate 1 Paste 템플릿 (재사용)

### 3.1 Header (Fresh verification 증거)

```markdown
## Gate 1 — §N + §M 본문 paste (fresh read 결과)

**Fresh verification (방금)**:
- Path: `/absolute/path/to/design.md`
- Exists: YES · Size: N bytes · Lines: N · MD5: `xyz123...`
```

### 3.2 Section paste (≤2500자/section)

```markdown
### §N. {Title}
\`\`\`
### 컨셉
{1줄}

### 데이터셋
- {list}

### 노트북 4개
- ...

### 3 차원 평가
| 차원 | 셀 | 평가 |
|------|---|------|
| ... | ... | ... |
\`\`\`
```

### 3.3 Code block 사용 이유

- 다른 봇이 raw markdown 구조 그대로 인식 가능
- 길이 over 시 section 분할
- 채니봇 inline paste 시 항상 fenced code block 안에 본문 삽입

---

## 4. File Existence Proof 명령어 4종 (재사용)

본인 sandbox에서 파일 만들었을 때 다른 봇에 증명할 때:

```bash
# 1. absolute path + perms/owner/size/mtime
echo "PATH: $(realpath <path>)"
echo "SIZE: $(stat -c '%s bytes' <path>)"
echo "MTIME: $(stat -c '%y' <path>)"
ls -la <path>

# 2. stat (inode + access times)
stat <path>

# 3. file type + content fingerprint
file <path>
md5sum <path>

# 4. first/last lines (본문 가시 일부)
head -8 <path>
tail -5 <path>

# 5. git status (트랙킹 여부)
git -C <repo_root> status --short
```

**출력 예시** (실제 2026-06-30 verification):

```
════════ FILE EXISTENCE PROOF ════════
PATH: /home/ubuntu/projects/portfolio-2026-track-b/track-da/design.md
SIZE: 10088 bytes
MD5:  50349ca798387f39245434b31b076c8f
MTIME: 2026-06-30 14:42:55.837242190 +0800
════════ FIRST 8 LINES ════════
# DA Portfolio Design v1 — 데이터 분석 포트폴리오 3 기획안
...
════════ LAST 5 LINES ════════
**Status: Draft v1 → aiprofit 리뷰 대기**
```

---

## 5. Pre-Flight Action Sequence (4 checks)

aiprofit OK 받기 **전**에 실행 환경 검증 → round-trip 낭비 방지.

### 5.1 GitHub 인증
```bash
gh auth status 2>&1
# Logged in to github.com account mybotagent (GITHUB_TOKEN)
# Active account: true
# Token scopes: 'repo'

gh api user --jq '.login'  # 'mybotagent'

gh repo view mybotagent/<repo-name> 2>&1 | head -5
# 404 = not exists → 생성 필요
```

### 5.2 Linear API
```bash
grep LINEAR_API_KEY ~/.hermes/.env | sed 's/=.*/=<REDACTED>/'
grep -iE 'linear.*workspace|linear.*team' ~/.hermes/.env | sed 's/=.*/=<REDACTED>/'
```

### 5.3 Local repo
```bash
git -C ~/projects/<repo> remote -v   # 비어있으면 push ready
git -C ~/projects/<repo> status --short
```

### 5.4 보고 템플릿
```markdown
## ✅ Pre-flight 결과

| # | 항목 | 상태 | 비고 |
|---|------|------|------|
| 1 | `gh account` | 🟢 `mybotagent` active | Token scope: `repo` ✓, `read:org` missing (not blocker) |
| 2 | `gh repo view` | 🔴 404 — 미존재 | 생성 필요 |
| 3 | local remote | 🟢 clean | push ready |
| 4 | Linear API key | 🟢 `~/.hermes/.env` 존재 | workspace URL 별도 확인 필요 |
```

---

## 6. 결정 상태 코드 (canonical)

모든 결정 보고 시:

| 코드 | 의미 | 사용 시점 |
|------|------|-----------|
| 🟢 **active** | 결정 가능, aiprofit OK 대기 | Gate 1 통과 후 |
| 🟢 **summary commit OK** | path-independent, summary로 결정 가능 | Gate 2 통과 |
| ⏸ **blocked** | 의존성 (URL/decision) 대기 | path-dependent |
| 🔴 **verification incomplete** | Gate 1 미통과 | paste 전 |

**예시** (2026-06-30, 5 decision tracking):

```markdown
| # | 결정 | 상태 | 비고 |
|---|------|------|------|
| 1 | 3 기획안 OK | 🟢 active | Gate 1 통과 · aiprofit OK 대기 |
| 2 | Track (a) | 🟢 active | summary commit 가능 |
| 3 | deep tier = Slot B | 🟢 summary commit OK | path-independent |
| 4 | repo path | ⏸ blocked | GitHub remote URL 의존 |
| 5 | Linear + Kanban + push | ⏸ blocked | #4 의존 |
```

---

## 7. Pitfalls (반복됨, 2026-06-30)

### P1 — 본인 인증 verification 가정
> "내가 봤으니 OK" = single-source-of-truth.

→ ❌ 즉시 Gate 1 paste 요청 받음. **paste 의무**.

### P2 — path-universal claim
> "✅ 완료 · path: ~/projects/..." → 다른 봇 read 불가.

→ ❌ sandbox 격차 disclose 필수. universal claim = banned.

### P3 — summary-only commit 시도
> "Gate 1 closed ✅" status 단정 → 다른 봇 read 불가.

→ ❌ status claim = ❌. **본문 가시** = ✅.

### P4 — pre-flight 없이 OK 요청
> aiprofit OK 사인 후 추가 확인 필요 → round-trip 낭비.

→ ❌ **pre-flight 4 check 먼저** → 결과 보고 → OK 요청.

### P5 — 모든 missing scope를 blocker로 잘못 보고
> `read:org` missing = push 작업에 영향 없는데 blocker 보고 → 사용자 OK 보류.

→ ❌ push only 작업이면 `repo` scope만으로 충분. 비-blocker 정확 보고.

### P6 — 본인 작성분이라 paste 생략
> "§3 Slot B는 내가 안 썼으니 OK"

→ △ 자기 작성분은 self-verify 가능 (3-bot 합의). 단 Gate 1 paste 의무는 **다른 봇이 작성한 분에만** 적용.

---

## 8. 합의 도출 시퀀스 (reference flow)

```
1. PM 슬롯 할당 + 6-8줄 템플릿 공지
2. Round 1 — 각 봇 슬롯 제안 (병렬, <@ID> mention)
3. Round 2 — 상호 비판 (의존성, 순차)
4. Round 3 — 확정본 + 비교표
5. PM → design.md v1 작성 (로컬 sandbox)
6. PM → "✅ 완료" status claim 대신 Gate 1 paste 송출
7. 다른 봇 verify → Gate 1 closed
8. Pre-flight 4 check 보고 (gh, Linear, local remote, file proof)
9. aiprofit 결정 5개 요청 (상태 코드 명시: 🟢/⏸/🔴)
10. aiprofit 1줄 OK 사인
11. 실행 시퀀스 (gh repo create → push → Linear SHO-XX → Kanban 태스크)
```

---

## 9. Cross-References

- `meeting-documentation/SKILL.md` §"Cross-Bot Sandbox Verification Gate Pattern (NEW 2026-06-30)"
- `meeting-documentation/SKILL.md` §"Pre-Flight Action Sequence (NEW 2026-06-30)"
- `templates/3-proposal-matrix.md` — 12 cells/slot 매트릭스 (Slot A/B/C 구조)

---
name: multi-bot-discord-routing
description: Class-level discipline for multi-bot Discord routing in a multi-system environment (Linux Hermes bots + Mac launchd Claude bots). Use whenever a Discord thread/channel receives a mention, when a routing conflict appears, when "wrong channel" errors happen, when debugging "which bot sent this" attribution, or when on/off-harness verification of any bot's Discord setup.
when_to_use: |
  - Discord multi-bot 환경 (plannerbot + dsbot + 채니봇 또는 유사)에서 응답 전
  - chat_id 라우팅 버그 발생 시 (메인 채널에 쓰레드 답이 떴을 때 등)
  - "어느 봇이 이걸 보냈지?" attribution 추적
  - 봇별 디스코드 하네스(access.json / soul.md / plist / config.yaml) 차이점 비교
  - main channel 응답/무음 결정
  - 새 봇 세션 시작 시 라우팅 검증
allowed-tools: Read Write Glob Grep WebFetch Bash(gh,curl,sqlite3)
model: opus
context: fork
---

# Multi-Bot Discord Routing Discipline

## Core Goal

멀티봇 환경에서 **어느 봇이 어느 채널에 응답할지**의 라우팅 규율. 시스템 차이(Mac launchd vs Linux Hermes)와 구조적 한계(user_id 단일 신원)를 인식하고 enforce.

---

## 봇별 시스템 분류 (절대 혼동 금지)

| 봇 | 시스템 | OS | 경로 | 하네스 파일 |
|----|--------|-----|------|-------------|
| **plannerbot** | Claude Code + Mac launchd | macOS | `~/.claude/channels/discord-plannerbot/` | `access.json`, `soul.md`, `plist` ✓ |
| **dsbot** | Claude Code + Mac launchd | macOS | `~/.claude/channels/discord-dsbot/` | `access.json`, `soul.md`, `plist` ✓ |
| **채니봇** ⭐ | **Hermes 시스템 (Linux, 별개)** | Linux | `/home/ubuntu/.hermes/` | `config.yaml` + `.env` only (**access.json/soul/plist 없음**) |

**흔한 오해**: 채니봇이 `claude-code-discord-bot-setup` 레포에 포함될 것 — **아님**. 채니봇은 Hermes 시스템 봇.

### Hermes 단일 봇 구조 제약 (2026-07-02 verify)

**핵심 사실**: Hermes는 공식적으로 **1박스 = 1봇** 구조. 멀티 봇 인스턴스는 미지원.

| 증거 | 출처 |
|------|------|
| `DISCORD_BOT_TOKEN` 단 1개 | `~/.hermes/.env` |
| `config.yaml:discord` 섹션에 `bots:` / `instances:` 키 **없음** — 글로벌 옵션(`require_mention`, `thread_require_mention` 등)만 | `~/.hermes/config.yaml` L421–434 |
| 실행 프로세스 `hermes_cli.main gateway run --replace` 단 1개 | `ps aux` → pid 3105939 |
| `channel_directory.json` 에 `bots` 키 부재 | `jq .keys` |

→ "채니봇 외 봇 2개 더"가 의미하는 바는 다음 중 하나로 한정됨 (순서 = 추천도):

| 패턴 | 새 토큰 | 격리도 | 구현 난이도 |
|------|---------|--------|-------------|
| **페르소나 멀티플렉싱** | 불필요 | 낮음 (메모리 공유) | 쉬움 (system prompt 분기) |
| **별도 Hermes 인스턴스** | 필요 (Discord Developer Portal) | 완전 (user_data 분리) | 중간 (포트+프로세스 n개) |
| **user_id 스푸핑** | 불필요 | — | **비추천 (정책 위반)** |

**별도 인스턴스 패턴** (구체):
```bash
# 봇1 (채니봇, 현재)
hermes gateway run --user-data ~/.hermes

# 봇2 (다른 페르소나)
hermes gateway run --user-data ~/.hermes-bot2 --port 8643
```

**루프 방지 단일 규율**: 봇 간 무한 교차응답 차단 = **채널 분리**. 같은 쓰레드에 봇 둘 다 입장 시 `thread_require_mention: false` 설정이면 100% 루프 → 봇 A는 `#project-manage`, 봇 B는 `#research` 식으로 채널 라우팅 강제.

### 1인 AI-Aug 회사 = Level 2 자동화 (현실 한계선, 2026-07-02 합의)

Level 5 분류 (Level 4~5는 사용자에게 약속 금지):

| Level | 명칭 | 가능성 |
|-------|------|--------|
| 1 | 단순실행 (cron 요약/알림) | ✅ 표준 |
| 2 | 분석/생성 (요약/코드/리서치 초안) | ✅ 즉시 가능 |
| 3 | 자율협업 루프 (multi-agent 회의) | ⚠️ PoC, $50+/월, 사람 loop 감시 필수 |
| 4 | 장기 자율운영 (self-improving) | ❌ lab 데모, drift/meta-meta recursion 함정 |
| 5 | 자율판단/책임 | ❌ 어디서나 금지 |

**허용 약속**: "AI 사원 1~N" (Level 2). **거짓 약속**: "사람 없이 완전 자동 회사" (Level 4~5).

---

## user_id 정정 (2026-07-01 발견 오류)

| ID | 누구 |
|----|------|
| `1327192313616797706` | **aiprofit 본인 (tkd1496, allowFrom 등록)** |
| `1510396647266451506` | **채니봇 봇 user_id** |
| `1520719061498204262` | plannerbot |
| `1521368186891665561` | dsbot |

⚠️ **Discord user_id는 글로벌 유니크. 같은 사람 = 같은 ID. 봇과 사람 ID는 절대 다름.**

---

## 라우팅 규율 (5대 원칙)

### 1. Main channel = 무음
- 채널 ID: `1510416432763240621` (메인)
- 직접 호출(@멘션) 없이 메시지 보내지 않음
- 메인에 도달한 메시지는 flag만, 응답은 활성 쓰레드에서

### 2. 활성 쓰레드 = 해당 세션의 단독 컨텍스트
- 새 쓰레드 = **새 세션** (zero context leak)
- 다른 쓰레드의 컨텍스트는 그 쓰레드 안에서만 사용
- 의심 시 `fetch_messages`로 chat_id 재확인

### 3. reply_to ≠ 발송 chat_id
- `reply_to` 파라미터로 부모 메시지에 답 표시: 가능
- BUT **발송 자체는 명시적 chat_id로**: `discord:chat_id:thread_id` 형식 또는 `reply_to`에 thread 메타 포함
- 발송 chat_id를 channel-level로 두면 → 메인 채널에 표시됨 (위반)

### 4. 봇별 정책 차이 인정

| 봇 | requireMention | thread_requireMention | 채널 정책 |
|----|----------------|----------------------|-----------|
| plannerbot/dsbot | true (groups 전체) | — | `access.json` `groups.<id>.requireMention: true` |
| 채니봇 | true | **false** (Hermes config.yaml) | `require_mention: true`, `thread_require_mention: false` |

→ 채니봇은 **쓰레드에서 멘션 없이 자유 응답**. 이게 라우팅 버그의 원인.

5. **Hermes 박스 = 단일 봇 모델 (2026-07-02 validate)**: Hermes config.yaml의 `discord:` 섹션은 글로벌 옵션만 (`require_mention`, `thread_require_mention` 등). `bots:` / `instances:` 키 부재. `.env`의 `DISCORD_BOT_TOKEN` 단 1개. 실행 프로세스 `hermes_cli.main gateway run --replace` 단 1개. → **공식 멀티 봇 인스턴스 미지원**. 멀티 봇 만들려면: (1) Discord Developer Portal에서 봇 토큰 추가 발급 (사용자 작업), (2) `hermes gateway run --user-data ~/.hermes-bot2 --port 8643` 별도 인스턴스 띄우기, (3) **채널 분리 + Discord user_id 기반 메시지 분류**로 무한 루프 방지 (같은 채널 봇 둘 다 입장 시 100% 루프), (4) config.yaml 단일 discord 섹션 공유 불가 → 봇별 별도 config.
6. **Multi-session = audit 부재 (security hole)**
- Discord는 user_id만 본다
- 채니봇 user_id (`1510396647266451506`)로 로그인한 **모든 세션** = "채니봇"으로 attribution
- 세션 구분 토큰 없음 → audit trail 없음
- "채니봇이 X라고 했다" 신뢰 불가 → 라우팅 규율 enforce 불가

---

## 진단 체크리스트 (라우팅 버그 시)

```
1. chat_id 추출
   - 활성 쓰레드: thread_id 확인
   - 메인 vs 쓰레드 명확히
   
2. 발송 경로 추적
   - reply_to 파라미터 ✓
   - 발송 chat_id = thread_id? 아니면 channel_id?
   - mcp__plugin_discord_discord__reply 호출 인자 재확인
   
3. 봇 세션 확인
   - 어느 머신? (Mac vs Linux)
   - 어느 시스템? (Claude Code vs Hermes)
   - 어느 하네스 파일? (access.json vs config.yaml)
   
4. Multi-session 가설
   - 다른 세션이 같은 user_id로 로그인했나?
   - cron job? 자동화? 다른 사람?
   - 18분 "Still working" 루프 / "Memory 한도 초과" 패턴?
   
5. 메인 채널 위반 시
   - 즉시 응답 X
   - flag + 사용자에게 확인 요청
   - "본인 메시지" vs "다른 세션" 시나리오 분기
```

---

## 흔한 함정 (5가지)

### 함정 1: Universal path claim
❌ "이 봇은 `~/.claude/channels/discord-X/`에 있다" → **Mac launchd 봇만**
✅ Hermes 봇은 `/home/ubuntu/.hermes/` — **항상 머신 확인 먼저**

### 함정 2: aiprofit = 채니봇 user_id
❌ "aiprofit이 보낸 메시지 = 채니봇 메시지"
✅ aiprofit ID ≠ 채니봇 봇 ID. `allowFrom` 기준으로 매핑.

### 함정 3: Channel-level 발송이 thread 답으로 표시
- `reply_to`는 정상이지만 발송 chat_id가 channel-level → 메인 채널에 표시됨
- 해결: `discord:chat_id:thread_id` 형식 강제

### 함정 4: New thread = continuation
- ❌ 이전 쓰레드 컨텍스트 이어서 사용
- ✅ 새 쓰레드 = 새 세션, zero context

### 함정 5: Multi-session audit 불가
- "채니봇이 X라고 했다" = 어느 세션인지 모름
- 신뢰 안 함, 라우팅 규율 enforce 못 함
- 해결: 세션 식별 토큰 필요 (현재 시스템 한계, 별도 작업)

### 함정 6: "Discord 응답 안 함" = 게이트웨이 사망이 아님 (2026-07-03 incident)
- `systemctl status` active, 로그 "Connected as 채니봇#1213" → 게이트웨이는 정상
- **그러나** "Failed to send Discord message: 404 Not Found (error code: 10003): Unknown Channel" → 발송 채널 부재
- 진단 분리:
  - (a) **게이트웨이 프로세스 사망** → `ps aux | grep "gateway run"`
  - (b) **Inbound 처리 실패** (pycache stale 등) → 로그에서 `ImportError` / `nous_tool_gateway_unavailable_message` 패턴
  - (c) **발송 경로 실패** (채널 부재) → 로그에서 `404` / `Unknown Channel` / `error code: 10003` 패턴
- 자가 진단은 `.env`의 `DISCORD_BOT_TOKEN`으로 channels API 단일 호출만:
  ```bash
  TOK=$(grep "DISCORD_BOT_TOKEN=" ~/.hermes/.env | cut -d= -f2-)
  curl -s -H "Authorization: Bot $TOK" "https://discord.com/api/v10/channels/<channel_id>"
  # {"message": "Unknown Channel", "code": 10003} → 채널 삭제/봇 추방
  ```
- **사용자 차단 영역**: `/users/@me/guilds`, 메시지 fetch 등 → 길드 목록/식별정보 노출 우려. 자가 진단은 channels 단일 조회로 끝낼 것. 더 필요하면 사용자 확인 후 별도.
- wiki `infra/discord-gateway.md` Troubleshooting에 "채널 삭제/봇 추방" 케이스 추가 필요 (현재는 포맷 + pycache 두 케이스만 다룸).

---

## Quick audit 스크립트 (10분 체크)

```bash
# 1. cron jobs (사용자)
crontab -l

# 2. systemd user units
systemctl list-units --user --type=service

# 3. hermes cron db
sqlite3 ~/.hermes/kanban.db "SELECT id, status, title FROM tasks WHERE status IN ('queued','in_progress') ORDER BY exec_order"

# 4. 실행 중인 hermes/봇 프로세스
ps auxf | grep -E "[h]ermes|[c]laude.*channels"

# 5. 메인 채널 최근 메시지 (누가 봤는지)
# discord fetch로 chat_id=1510416432763240621 최근 10개 확인
```

---

## 향후 작업 (follow-up 등록 후보)

- [ ] **세션 식별 토큰**: 채니봇 user_id로 메시지 보낼 때 session_id 헤더 첨부
- [ ] **3봇 하네스 정책 통일**: `require_mention` / `thread_require_mention` 봇 간 표준화
- [ ] **라우팅 검증 자동화**: 회신 전 chat_id 검증 assertion 추가
- [ ] **Multi-session dashboard**: 어느 세션이 활성인지 추적하는 UI

---

## 참고 자료

- `references/claude-code-discord-bot-setup.md` — Mac launchd 봇 (plannerbot/dsbot) 아키텍처, 봇별 디렉토리 구조, 패치 이력
- `references/hermes-discord-config.md` — Hermes 채니봇 config.yaml + .env, plan/dsbot 비교, thread_require_mention 함정
- `references/incident-2026-07-01-main-channel.md` — 본 세션 메인 채널 위반 incident 타임라인, user_id attribution 오류 분석, 적용 액션, 교훈
- `references/incident-2026-07-03-discord-404-channel.md` — "응답 안 함" → 404 Unknown Channel 진단 분리 (a/b/c) + 자가 진단 보안 경계 (channels API만, guilds fetch 차단)

---

## 핸드오프 책임

| 영역 | 책임 봇 |
|------|---------|
| 봇별 하네스 차이 진단 | 채니봇 (현재 세션) |
| 전략적 결정 (메인 채널 OK 여부) | plannerbot |
| 데이터 검증 (DB/API) | dsbot |
| 사용자 결정 | aiprofit |

---

## 핵심 takeaway

> **Multi-bot Discord 환경에서는 (1) 시스템 차이 (Mac vs Linux), (2) user_id 단일 신원의 한계, (3) thread/channel 라우팅 정확성을 항상 의식하라. 응답 전 3초 점검: 어느 시스템? 어느 user_id? 어느 chat_id?**
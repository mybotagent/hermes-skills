# Incident: 2026-07-01 메인 채널 위반 + user_id Attribution 오류

## 요약

메인 채널 `1510416432763240621` 11:36:31에 status 메시지 도달. 봇 routing 규율 위반으로 flag됨. 조사 결과 **multi-session 자동화 + 메모리 user_id 오류**의 합성 사고.

## 타임라인 (재구성)

```
11:25:39 — 초기 메시지 (메인 채널에 status loop 시작)
11:27:32 / 11:30:32 / 11:33:33 — "Still working... (12/15/18 min, iteration 6/60, terminal)"
11:30:40 — ls/cat/read_file 호출 (`~/.hermes/wiki/index.md`, `project-harness.md`)
11:36:08 — "Memory 한도 초과 — wiki에 저장합니다"
11:36:13 — "이미 통합 위키 페이지 존재 — 읽고 일관성 유지합니다"
11:36:31 — 위반 post ("main channel 진행 OK")
```

## 핵심 발견

### 1. user_id Attribution 오류 (메모리)

❌ **잘못된 메모리**: "aiprofit = 1510396647266451506"
✅ **올바른 매핑**:
- `1327192313616797706` = aiprofit (tkd1496, `allowFrom` 등록)
- `1510396647266451506` = 채니봇 봇 user_id

메모리 정정됨 (2026-07-01).

### 2. Multi-session 가설 (가장 가능성 높음)

메인 채널 11:36:31 메시지가 채니봇 user_id로 attribution되었다면:

| 시나리오 | 가능성 | 근거 |
|---------|--------|------|
| aiprofit 본인 (다른 세션) | ❌ | user_id 불일치 |
| plannerbot/dsbot cron | ❌ | 다른 user_id |
| **채니봇 Linux cron/auto-task** | 🟢 **HIGH** | 동일 user_id, "Memory 한도 초과" hermes 패턴 |
| 다중 채니봇 인스턴스 | 🟡 | systemd/launchd multi-instance 가능성 |

18분 "Still working" 루프 + "Memory 한도 초과" 메시지 = **hermes 시스템의 장시간 cron job 또는 자동화 task**의 시그니처.

### 3. 경로 검증 실패

- plannerbot (Mac): `~/.claude/channels/discord-plannerbot/` 존재
- 채니봇 (Linux): `/home/ubuntu/.hermes/` 존재
- **각자 다른 머신, 다른 OS** — universal path claim 불가능

### 4. 봇별 하네스 파일 차이

| 봇 | access.json | soul.md | plist | config.yaml |
|----|-------------|---------|-------|-------------|
| plannerbot | ✓ (7ch) | ✓ | ✓ | — |
| dsbot | ✓ (7ch, 📊) | ✓ | ✓ | — |
| 채니봇 | ❌ | ❌ | ❌ | ✓ (Hermes) |

## 적용된 액션

1. ✅ 메모리 정정: aiprofit user_id = `1327192313616797706`
2. ✅ skill 생성: `multi-bot-discord-routing` (devops 카테고리)
3. ⏳ multi-session 추적: 미실행 (follow-up 등록 권장)
4. ⏳ 3봇 하네스 라우팅 통일: 미실행 (별도 epic 권장)

## 교훈 (재발 방지)

### 교훈 1: 응답 전 3초 점검
- 어느 시스템? (Mac launchd vs Linux Hermes)
- 어느 user_id? (봇 vs 사람)
- 어느 chat_id? (channel vs thread)

### 교훈 2: user_id 혼동 금지
- 봇 user_id ≠ 사람 user_id
- `allowFrom` 등록된 ID = 사람 (허용자)
- 봇 ID는 별도, 글로벌 유니크

### 교훈 3: Multi-session 의심
- 18분+ "Still working" 루프
- "Memory 한도 초과" 메시지
- 동일 user_id로 여러 출처 → 의심

### 교훈 4: Universal path claim 금지
- `~/.claude/` = Mac launchd 봇
- `/home/ubuntu/.hermes/` = Linux Hermes 봇
- 머신 확인 후 경로 단언

## 후속 작업 (follow-up)

- [ ] chat_id 라우팅 assertion 추가 (메인 채널 발송 시 경고)
- [ ] 세션 식별 토큰 도입 (메시지 헤더에 session_id 첨부)
- [ ] 3봇 하네스 정책 통일 epic 등록
- [ ] meeting notes에 F-1, F-2로 등록 (multi-session 추적, 라우팅 통일)

## 관련 파일

- `~/.hermes/config.yaml` (Hermes 채니봇 Discord 라우팅)
- `~/.hermes/.env` (DISCORD_BOT_TOKEN 등)
- 레포 `sh-ai-x/claude-code-discord-bot-setup` (Mac launchd 봇)
- 메모리 (정정됨)
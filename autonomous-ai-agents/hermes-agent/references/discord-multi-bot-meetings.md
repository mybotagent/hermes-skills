# Discord Multi-Bot Meeting Protocol (aiprofit context)

## Participants

| Role | Bot/User | Discord ID |
|------|----------|------------|
| 의사결정자 | aiprofit | <@1510396647266451506> |
| 실행/기술 | 채니봇 (Hermes) | <@1510396647266451506> |
| 의제/우선순위 | plannerbot (Claude) | <@1520719061498204262> |

## Prerequisites

- `DISCORD_ALLOW_BOTS=mentions` in `~/.hermes/.env` (required for multi-bot meetings)
- plannerbot must be configured to respond only on @mention (not all messages)
- @mentions use Discord user IDs (`<@ID>`), NOT display names — text @name does not trigger notifications

## Meeting Lifecycle

### 1. Prepare (채니봇, pre-meeting)
Before the meeting invite is sent:
- Sync Kanban ↔ Linear (daily cron handles this; manual: `hermes kanban ls` + Linear wrap)
- Check Kanban DB for current task status
- Review Linear backlog for outstanding items
- Compress memory if near capacity

### 2. Invite (aiprofit)
```text
@plannerbot @채니봇 회의 시작하자
회의 안건: <한 줄 설명>
```

### 3. Discuss (all)
- 채니봇 presents data-driven analysis first (current state, options, trade-offs)
- plannerbot provides strategic perspective (prioritization, risks, sequencing)
- aiprofit redirects if off-track — redirects are quick and decisive
- Keep responses concise. aiprofit's preference: 극도로 간결 축약 한국어
- When a decision is reached, move to conclusion

### 4. Record (채니봇, post-meeting)
Three storage layers — all needed, roles differ:

| Storage | Role | Format |
|---------|------|--------|
| **Wiki** | Context preservation | `hermes-wiki/projects/<topic>.md` — 합의 배경/근거/옵션 분석 |
| **Kanban/Linear** | Execution tracking | Linear issue with subtasks, wiki reference |
| **Skill** | Reusable asset | Only if the topic is a CLASS-level pattern (not one-off) |

**Order:** Wiki first (정당화) → Linear task references wiki (실행) → Skill last (구현완료 후 재사용 자산화)

### 5. Finish
- aiprofit says "마무리" or "끝" → stop discussion immediately
- No over-explaining. No unnecessary follow-ups.
- aiprofit has final approval authority only — 채니봇 has full Linear/Kanban execution authority

## Communication Rules

- **aiprofit:** 극도로 간결. 즉시 실행 기대. 방향 전환 빠름. "투자" 주제 논의 금지 (예외: aiprofit이 먼저 꺼낼 때만)
- **채니봇:** 분석 우선 → 옵션 제시. plannerbot 호출로 전략 보강. Multi-bot 회의에서 PM 역할.
- **plannerbot:** 전략/우선순위/리스크 분석. @멘션으로만 응답. 의제 구성 담당.
- All bots use `<@ID>` mentions, never text @name (text @name does not trigger Discord notifications)

## Pitfalls

- plannerbot's `replyToMode=all` with `mentionPatterns` must be configured correctly
- If plannerbot misses a call, retry with bare `<@ID>` + short prompt
- 3-bot 회의에서 서로 @멘션 계속 하면 스레드가 길어짐 — 적당히 마무리
- Recording: task without wiki = 사후 정당화 불가. Wiki without task = 실행 부재.

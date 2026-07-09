# Discord Multi-Bot Meeting Pattern

## Setup: aiprofit + plannerbot + 채니봇 (Hermes)

|역할|주체|설명|
|---|---|---|
|**PM / 실행자**|채니봇 / Hermes|Kanban 읽기, 회의 진행, **모든 태스크 직접 실행** (assignee=hermes)|
|**참고 의견 제공**|plannerbot (ID: 1520719061498204262)|Claude Discord 봇 — 구조화된 제안/의견, **의사결정권 없음**|
|**최종 의사결정자**|aiprofit (ID: 1510396647266451506)|모든 결정의 최종 승인권자. plannerbot 의견은 참고만|

## ⚠️ Pre-Meeting Sync Check (🔥 필수 선행)

회의 시작 전 **반드시** 아래 순서대로 실행:

1. **Kanban DB 조회:**
   ```bash
   sqlite3 ~/.hermes/kanban.db "SELECT id, title, status, priority, assignee FROM tasks WHERE status NOT IN ('archived','done') ORDER BY priority;"
   ```
2. **Linear 조회:**
   ```bash
   cd ~/.hermes/skills/productivity/linear/scripts
   python3 linear_api.py list-issues --team SHO --limit 30
   ```
3. **동기화 검증:**
   - Kanban 태스크 body의 Linear ID (SHO-XX)가 Linear에 있는가?
   - Linear에 Kanban에 없는 추가 이슈가 있는가?
   - Priority, status 일치하는가?
   - **불일치 발견 시 수정 후 회의 시작.**
4. **백로그 리포트 준비:** ready/todo/in_progress 개수, P0~P2 분포
5. **회의 시작.**

## ⚠️ Prerequisites — Gateway Config

**회의 시작 전** Discord 게이트웨이가 다른 봇의 메시지를 허용하는지 확인:

1. `~/.hermes/.env` 에 다음 설정 확인:
   ```
   DISCORD_ALLOW_BOTS=mentions
   ```
   - `"none"`(기본값) = 다른 봇 무시 → **회의 진행 불가**
   - `"mentions"` = 다른 봇이 @멘션할 때만 응답 ✅
   - `"all"` = 모든 봇 메시지 허용 (스팸 위험)
2. 게이트웨이 재시작: `hermes gateway restart`
3. `thread_require_mention: false` (기본값) 확인 — 이미 참여한 스레드에서 추가 멘션 없이 작동

## 의사결정 규칙 (🔥 중요)

1. **plannerbot 의견 = INPUT.** 참고 자료. 실행 결정 근거로 사용하되 단독 실행 금지.
2. **최종 승인 = aiprofit.** plannerbot이 정리/추천해도 aiprofit의 명시적 OK 필요. "최종승인은 내가하는거야."
3. **모든 실행 = Hermes.** plannerbot이 assignee 추천해도 무시. "모든 실행은 너가 하는거고" → assignee 전부 hermes.
4. **회의 흐름:** 내가 데이터 제시 → plannerbot 의견/추천 → aiprofit 최종 결정 → 내가 실행

## Bot-to-Bot Communication on Discord

Hermes can mention other bots via `send_message()` using Discord snowflake IDs:

```python
send_message(
    target="discord:THREAD_SNOWFLAKE_ID",
    message="<@1520719061498204262> 회의 시작합니다. ..."
)
```

**Critical rules:**
- `<@USER_ID>` format is **required** — plain text `@name` in bot messages does NOT trigger a real mention
- **모든 회의 메시지에 반드시 @plannerbot 멘션 포함** — PM이 보내는 모든 메시지(첫 메시지 + 질문 + 후속/요약 메시지)에 `<@1520719061498204262>` 포함. aiprofit님이 명확히 요구한 규칙.
- The other bot must be in the same thread/channel to see the message
- If the other bot doesn't auto-respond, the user acts as relay

## Meeting Flow

1. **사전 체크:** Kanban DB + Linear 동기화 검증. `DISCORD_ALLOW_BOTS=mentions` 확인.
2. **PM reads kanban DB** — `sqlite3 ~/.hermes/kanban.db \"SELECT id, title, status, priority, assignee FROM tasks ORDER BY priority DESC, created_at;\"`
3. **PM checks Linear** — `python3 linear_api.py list-issues --team SHO --limit 30`
4. **PM sends sync report + kanban agenda** via `send_message()` with proper `<@>` mention of both plannerbot and aiprofit.
   **Agenda structure (섹션 순서):**
   ```
   ✅ Completed (done)
   🔴 Priority 1 — Ready (미할당)
   🟡 Priority 2 — Ready (미할당)
   ──────────────────────────────
   의제:
   1) 동기화 리포트 (매칭/불일치)
   2) P1 assignee 배정
   3) P2 진행/보류 결정
   4) 신규 태스크 필요?
   5) 실행 순서
   ```
   각 태스크마다 plannerbot에게 **구체적인 질문** 포함.
5. **plannerbot 응답 형식** (예상): 표/테이블 형태의 structured recommendation. 태스크별 담당 추천, 의존성 순서, 신규 제안 포함.
6. **aiprofit 최종 결정 대기** — plannerbot 의견만으로 실행 금지. aiprofit의 OK 필요.
7. **PM updates kanban** — aiprofit 결정 후 Kanban DB assignee/priority/order 업데이트. SQLite UPDATE 직접 사용:
   ```sql
   UPDATE tasks SET assignee = 'hermes', exec_order = 1 WHERE id = 't_xxx';
   ```
8. **Linear priority 동기화** — Kanban 결정을 Linear priority에도 반영.
9. **PM sends closing summary** — 최종 결정표, assignee/priority 변경사항, 실행 순서를 정리. 모든 메시지에 `<@plannerbot>` 멘션 포함.

## Pitfalls

- **Mention format:** Text `@claudebot` does NOT work from a bot. Must use `<@USER_ID>`.
- **Nickname variant:** Some bots only respond to `<@!USER_ID>`. Try both if one fails.
- **Display name in text matters:** Write `@plannerbot` in visible text alongside `<@ID>` so both Discord system and bot text parser catch it.
- **Thread targeting:** Always send to the correct thread via `target=\"discord:THREAD_ID\"`.
- **Bot must be in the thread:** Cannot see messages in threads it hasn't been added to.
- **No auto-relay:** Hermes cannot read other bots' responses — user must copy them.
- **게이트웨이 재시행 필수:** .env 변경 후 `hermes gateway restart` 필요.
- **Kanban DB 직접 조작:** kanban_create 툴 없어도 SQLite 직접 INSERT/UPDATE 가능. `strftime('%s','now')`로 created_at 생성.
- **절대 plannerbot 의견만으로 실행 금지:** 항상 aiprofit의 최종 승인을 받을 것.
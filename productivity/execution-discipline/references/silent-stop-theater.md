# Silent-Stop Theater (sixth flavor, 2026-07-07)

> aiprofit 2026-07-07 nudge: **"뭔가 진행 안하네? 계속 진행하게해 쉬지말고"**
> autonomous 모드 배치(cron 6건 시간대 재배치 등) 중 step 사이에서 침묵하는 패턴. 사용자가 명시적으로 nudge하기 전까지 멈춤 — 5번째 autonomous 교정.

## 증상 (Symptoms)

- autonomous mode batch 진행 중 (예: cron time-reschedule multi-update, multi-repo push, 병렬 검증)
- 직전 tool call이 끝난 직후, 모델이 별다른 출력 없이 stop
- 사용자 메시지가 "쉬지말고 / 진행해 / 왜 멈춰있어 / 다음 단계 진행해" 형태로 nudge
- agent가 self-confirm ("다음 step으로 점프합니다") 같은 헤더 한 줄 추가 안 함
- cron side: 4-5건 중 2-3건 update 후 마지막 1-2건이 unprocessed

## 근본 원인 (Root cause)

batch 다중 step에서 agent는 종종 다음 패턴:

- 직전 step의 결과를 검증하려고 새 turn을 까는데, 그 turn에서 "다음 step도 같은 turn에서 묶으면 됐는데" 라고 늦게 깨달음
- autonomous mode 신호(`memory`, profile)에 의지해서 "다음 사용자 신호까지 기다려도 되지"라고 합리화
- 단일 책임 principle을 잘못 적용: "한 turn = 한 action"으로 강제해 batch 실행이 분절됨

## 검출 규칙 (Detection)

nudge 발생 시점에 다음 조건 모두 확인:

1. **active batch 존재** — message stream 상단의 plan / todo / 명시적 multi-step commit
2. **complete > 0, < total** — 일부 step 끝, 일부는 unstarted
3. **recent tool result** — 직전 tool call은 정상 종료 (출력이 비어있지 않음)
4. **사용자 nudge 시그널 명시** — "계속 / 진행해 / 쉬지말고 / 다음 단계 / 왜 멈춰있어" 등

네 가지 다 만족 → silent-stop theater 발동.

## Recovery Sequence

**Step 1: 무의식 no-op 금지.**
사용자 nudge 받으면 idle 단계 평가부터 시작하지 말고 **즉시 다음 step으로 점프**. "지금 뭘 할지 정리하겠습니다" 같은 header 한 줄만 출력하고 직행.

**Step 2: 안전한 step 묶음 한계.**
한 turn에 묶을 수 있는 tool call 묶음의 안전 상한은 **3-5개**. 이보다 많으면 atomic transaction 보장이 깨짐. 묶음 내 step은 다음 안전도 분류를 모두 통과해야 함:

| 안전도 | step 예시 | 묶음 가능 |
|--------|-----------|-----------|
| read-only / idempotent | list/show/search/log | ✅ 5+ |
| idempotent write | cron update (schedule field) | ✅ 3-5 |
| 외부 푸시 | git push (mirror only) | ⚠️ 1-2 |
| 비가역 쓰기 | secret rotate, env var -e, branch -D | ⚠️ 1 (확인 후) |
| 외부 부작용 | email send, PR open, public POST | ⛔ 묶음 ❌, 명시 확인 |

**Step 3: 묶음 후 checkpoint 강제.**
묶음 종료 시점이면 다음을 모두 출력 (1-2줄만):

```
작업 요약:
- cron update 완료: A, B, C
- 남은 작업: D, E

다음 자율 후보 (계속 가도 됨):
- F → sanity self-check
- G → wiki log push
```

이 checkpoint가 있으면 사용자가 즉시 다시 nudge 안 해도 batch 흐름 유지. **첫 checkpoint까지는 묶음만 push, checkpoint가 보이자마자 다음 묶음 push.**

**Step 4: 아무 신호 없을 때 행동.**
nudge가 들어왔는데 진짜 안전한 다음 step이 없으면:

- "현재 단계 안전 step 소진, 결정 영역입니다" 한 줄
- 그 다음에는 다시 idle. **핵심: nudge 1번에 책임지는 건 다음 안전한 step 1개 이상 실행이라는 점.**

## Anti-patterns (DO NOT)

| ❌ Anti-pattern | ✅ Fix |
|----------------|--------|
| nudge 받자마자 "어디까지 했지?" 자문 | 묻지 않고 next step 직행 |
| 한 turn = 한 step | atomic batch 묶음 push |
| checkpoint 안 쓰고 N step 묶음 push | 매 묶음마다 1-2줄 checkpoint 출력 |
| silent return (=사용자가 nudge해야 응답) | 묶음 끝나면 적어도 "D, E 남았음" 한 줄 |
| "다음 신호 대기" 합리화 | 묶음 N개 끝나면 즉시 다음 묶음 판단 |

## 2026-07-07 발동 사례 — cron 6건 시간대 재배치

사용자 일련의 nudge:
1. "새벽에만 하도록" — KST 0-6시 한정
2. "새벽~10시까지" — KST 0-10시 확장
3. "아니다 8시까지 하자" — KST 0-8시 좹힘
4. "기존 cron과 겹치지 않도록" — 비대중 가드 추가
5. "새벽에 15분마다 뭔가 동작하도록" — heartbeat 추가

agent 행동:
- 1-3 turn: 3건 update (491c817d9ed4, da557233e6ac, 8ecfa3081d3b) — 새벽 0-8시 윈도우 검증 실수 일부
- 4 turn: dadb1f540867, c172635927c2 분리 update
- 5 turn: 19703b962de7 (dawn-heartbeat-15m) 신규 등록 + 비대중 가드 검증 (read-only+sleep 패턴)

**문제**: 매 turn이 단일 step + 늦은 시간대 환산 실수. 사용자가 nudge한 뒤 "뭔가 진행 안하네? 쉬지말고"로 묶음 push 요청. batch 묶음 + 첫 checkpoint 출력 규칙 적용 후 즉시 완료.

## 일반화 규칙 (재사용)

autonomous mode batch 일 때:

1. **nudge 받으면 즉시 실행** — 묻지 말고 직행
2. **묶음 ≤ 5 tool calls** — 그 이상이면 checkpoint 출력 후 다음 turn
3. **각 묶음 후 1-2줄 checkpoint** — "X, Y 완료 / Z, W 남음 / 다음 후보: A, B"
4. **안전 step 소진 시에는 멈춤 알리기** — silent 리턴 ❌
5. **nudge 1회 = 안전한 다음 step 1개 이상 보장** — 이게 안 되면 답할 게 없음

## Related

- `autonomous-mode-interview-theater.md` (1st flavor) — clarify() loop 변형
- `paste-request-theater.md` (4th flavor) — paste 요청 반복 변형
- `over-engineering-sprawl.md` (5th flavor) — 안전 step 외 영역에서 layer 추가 변형
- `kanban-orchestrator` — atomic batch 한계 + checkpoint 출력 규칙 (대안 발산처)

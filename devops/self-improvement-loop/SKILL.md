---
name: self-improvement-loop
description: Class-level methodology for self-reflective improvement cycles using the WHAT⇒WHETHER⇒WHAT⇒HOW framework. Use whenever proposing improvements to a running system (cron, config, agents), reviewing weekly/monthly operations, defining metrics, or designing meta-cognition loops. Anchored on the user's 단일공식 preference (single formula, no branching) and 가치 검증 선행 philosophy.
when_to_use: |
  - 사용자가 "시스템 개선/리뷰/자기반성" 루프를 원할 때
  - cron/agent 운영을 주기적으로 self-audit 해야 할 때
  - 메트릭/지표가 정말 가치를 측정하는지 의심할 때
  - "해야 할 것 같은 느낌" 항목을 걸러내야 할 때 (사용자 핵심 원칙)
  - Level 4 self-improving agent를 욕심내려 할 때 (반드시 한 발짝 물러서게)
allowed-tools: Read Write Glob Grep WebFetch Bash
model: opus
context: fork
---

# Self-Improvement Loop (자가 개선 루프)

## 핵심 철학 — 사용자 원칙

| 원칙 | 의미 |
|------|------|
| **단일공식 선호** | 4-phase 단일 공식. 예외/조건문 금지 |
| **가치 검증 선행** | 실행 전에 "이게 진짜 필요한가?" 평가부터 |
| **shiny object 거름** | "해야 할 것 같은 느낌" 항목 명시적 거부 |
| **Phase 독립** | 한 Phase = 한 사이클 = 한 사이즈 |
| **최종 승인 = 인간** | cron push 전 aiprofit 승인 필수 |

## 🔁 4-Phase 공식: WHAT ⇒ WHETHER ⇒ WHAT ⇒ HOW

```
T₀ = cron trigger (주 1회 또는 월 1회)
    │
    ▼
┌─────────────────────────────────────────────────┐
│  PHASE 1 · WHAT  (지난 주 실제로 일어난 일)       │
│  ──────────────────────────────────────────────  │
│  • cron 실행 이력 (id, 실행횟수, 성공률, 비용)    │
│  • delegate_task 호출 이력                        │
│  • Linear/Kanban 상태 변화                        │
│  • Discord 발송량 / 사용자 반응                    │
│  • 산출물 (wiki 갱신, 리포트, 알림)                │
│  ⇒ "quantified reality" — 감 없이 숫자로만        │
└─────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────┐
│  PHASE 2 · WHETHER  (측정 자체가 옳은가)          │
│  ──────────────────────────────────────────────  │
│  • 우리가 측정하는 KPI가 진짜 가치 신호인가?       │
│  • "해야 할 것 같은" 항목이 metrics에 들어있나?    │
│  • 사용자(aiprofit)가 실제로 얻은 가치는?         │
│  • missing metric: 우리가 안 보는 게 더 중요?     │
│  ⇒ "질문 없는 답 거부" — 단일공식이어도 metric은 의심 │
└─────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────┐
│  PHASE 3 · WHAT  (진짜로 측정/해야 할 것)         │
│  ──────────────────────────────────────────────  │
│  • 옳은 정의/메트릭 재진술                         │
│  • 폐기 지표 (정직하게 삭제)                       │
│  • 추가 지표 (검증된 신호만)                       │
│  • 단일공식 재확인 또는 진화                        │
│  ⇒ "shiny object 거름망" 통과 후만 채택           │
└─────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────┐
│  PHASE 4 · HOW  (다음 주 구체 실행안)             │
│  ──────────────────────────────────────────────  │
│  • 변경 대상 (cron_id / SOUL / config)            │
│  • 변경 내용 (diff-level 한 줄)                   │
│  • 검증 방법 (kpi delta 측정 어떻게)              │
│  • 리스크 평가 (blast radius)                     │
│  • 비용 (tokens/월) 추정                          │
└─────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────┐
│  GATE · 너의 결정 (자동 적용 X)                   │
│  ──────────────────────────────────────────────  │
│  □ 전부 적용                                      │
│  □ 부분 적용 (선택)                               │
│  □ 보류 (다음 주 재검토)                          │
│  □ 폐기 (반대로 가야 함)                          │
│  ⇒ HUMAN-IN-THE-LOOP — 자동 적용은 Level 4 함정  │
└─────────────────────────────────────────────────┘
```

## 🚦 5-Level 자동화 분류 (Level 4~5 금지 약속)

| Level | 명칭 | 가능성 | 사용자 약속 가능 |
|-------|------|--------|------------------|
| 1 | 단순실행 (cron 요약/알림) | ✅ 표준 | ✅ |
| 2 | 분석/생성 (요약/코드/리서치 초안) | ✅ 즉시 가능 | ✅ (이게 진짜 타겟) |
| 3 | 자율협업 루프 (multi-agent 회의) | ⚠️ PoC, $50+/월 | ⚠️ 가치 검증 후 |
| 4 | 장기 자율운영 (self-improving) | ❌ lab 데모 | ❌ 약속 금지 |
| 5 | 자율판단/책임 | ❌ 어디서나 금지 | ❌ 약속 금지 |

## 구현 매핑 (Hermes 인프라에 그대로 얹기)

| 컴포넌트 | 도구 | 너 자산을 어떻게 쓰나 |
|---------|------|---------------------|
| **Trigger** | `cronjob` tool | 매주 일 21:00 KST 또는 매월 1일 07:00 KST |
| **Phase 1: WHAT** | `terminal` + `read_file` | `state.db`, `kanban.db`, `agent.log`, Linear history |
| **Phase 2: WHETHER** | `delegate_task(goal="critic")` | critic subagent 호출 |
| **Phase 3: WHAT** | `delegate_task(goal="redefine")` | redefine subagent 호출 |
| **Phase 4: HOW** | `delegate_task(goal="redefine")` | config diff / cron 변경안 |
| **Gate** | Discord 배너 + Kanban | 자동 push X, 인간 승인 대기 |
| **Wiki 갱신** | `wiki_save` skill | 변경 이력 영속화 |

## Subagent 2종 정의 → see `templates/critic.md` and `templates/redefine.md`

## 📊 Skill 사용 빈도 측정 (idle hygiene의 Phase 1 핵심 데이터)

SQLite `state.db`에서 skill_view 호출을 정확히 카운트하는 검증된 쿼리 + 통합 used 결정 절차 + 함정 정리. See `references/skill-usage-measurement.md`.

📊 **메모리 사용량 정밀 측정** (memory_alert.py, 2026-07-07 검증): `wc -m` (codepoint count) 사용 → byte count의 ±25% 오차 제거. memory tool 응답과 `wc -m` 결과 완전 일치 검증. 같은 reference 파일의 "메모리 사용량 정밀 측정" 섹션 참조.

📊 **Tool-as-Memory 패턴** (memory_query.py, 2026-07-07 검증): 단순 압축 ❌ → 구조 재설계 ✅. memory.md = KEY만 (306 chars / 13.9%) + 별도 tool로 위키 본문 lazy fetch. 21 keys × 21 wiki pages. 상세: `hermes-ecosystem-audit/references/memory-tool-as-memory.md`.

📊 **Disk + Cron + Script Cleanup** (2026-07-07 검증): ~4.3GB 회수 (pip/uv cache + WAL checkpoint + snapshot gzip). cron `last_run=NEVER` 판정 절차 + orphan script detection. 상세: `hermes-ecosystem-audit/references/disk-and-script-cleanup-2026-07-07.md`.

## 📋 산출물 템플릿

```
═══════════════════════════════════════════════════
🔁 자체개선 루프 — YYYY-Wnn (YYYY-MM-DD ~ YYYY-MM-DD)
═══════════════════════════════════════════════════

[1] WHAT — 실제 작동량
─────────────────────
• Cron N건, 평균 X회/일 실제 발화, Y건 한 번도 안 돌음
• Delegate 호출 N건, 평균 Xk tokens/건, max Yk (한 건 spike)
• Linear 태스크 N건 중 M건 완료, 평균 X일 lag
• Discord 발송 N회, 사용자 반응률 X%
• 토큰 사용 Xk t/day 평균, $Y/일

[2] WHETHER — 메트릭 의심
──────────────────────────
✗ "[메트릭명]"은 신호 아님 — [이유]
✓ 진짜 신호 후보: [후보]
✗ 빠진 신호: [missing metric]

[3] WHAT — 진짜 정의
────────────────────
옳은 지표:
• [지표 1 — 정의]
• [지표 2 — 정의]

폐기 후보: [메트릭 목록]

[4] HOW — 이번 주 변경안
────────────────────────
① [변경 대상] →
   [변경 내용 한 줄]
   [blast-radius: low/medium/high, 검증: kpi delta]

② [변경 대상] →
   [변경 내용 한 줄]
   [blast-radius: ...]

③ ❌ 신규 — [제안] [보류]
   (데이터 N일 더 필요)

[5] 너의 결정 (필수)
────────────────────
□ a/b 모두 적용
□ ①만 적용
□ ①+② 적용
□ 모두 거절

═══════════════════════════════════════════════════
출처: [데이터 출처]
예상 토큰비: $X.XX
═══════════════════════════════════════════════════
```

## ⚠️ 5대 함정 (피할 것)

1. **자기개선 루프 = Level 4 함정**: ground-truth 없이 LLM이 자기 자신을 평가 → drift
2. **메타-메타-메타 recursion**: what ⇒ whether ⇒ what ⇒ whether... 무한. **단일 사이클 = 4단계 고정**, 깊이 제한
3. **메모리 비대화**: 사이클 누적으로 지표가 폭증 → pruning 필요 (월 1회)
4. **자동 적용**: cron push를 자동화 = Level 4. **반드시 인간 승인 게이트**
5. **과잉 약속**: "사람 없이 완전 자동 회사" 약속 → 신뢰 손상. **Level 2까지만 약속**

## 🛡️ Autonomous Mode 위험 분류 매트릭스 (2026-07-07 합의)

사용자가 "알아서 해라 / 위험한 것 제외 모든 권한 줌" 류 발언 시, 자동화 가능한 단계와 절대 dry 유지 단계를 정렬한 매트릭스. `daily-repo-orchestrator` v1.3부터 적용.

| 동작 단계 | 위험도 | Autonomous mode default | 사용자 confirm 후 enable |
|---|---|---|---|
| Read (GET), search, scan | 0 | ✅ always OK | (영원히 dry 불필요) |
| Issue/task create (idempotent + external system) | 중 | ✅ mirror-only prod는 OK | `DRY_RUN_MIRROR=0` |
| Local DB patch (Kanban, Linear, wiki) | 중 | ✅ default OK | `DRY_RUN_MIRROR=0` |
| GitHub new branch / push / PR open | **높** | ❌ default dry | `DRY_RUN_FIX=0` 사용자 명시 |
| SMTP send (himalaya) | 중-**높** | ❌ default dry | `DRY_RUN_EMAIL=0` 사용자 명시 |
| Secret / PAT 추가/변경 | **최고** | ❌ 항상 dry (manual confirm) | 자동화 불가 |
| 외부 Collaborator 추가 | **높** | ❌ 항상 dry | 자동화 불가 |
| 결재/지급/payment | **최고** | ❌❌ 자동화 불가 | ❌❌ |

**판정 규칙 (자율 운영 시)**:
- 0~중 위험 + idempotent 가능 → 자동화 OK
- 높 위험 + 사용자 confirm 없음 → default dry = 절대 실행 금지
- 항상 dry = 자동화 layer에서 mask (사용자 confirm 받아도 cron 등록 안 함)

→ `daily-repo-orchestrator` 의 STAGE별 dry 분리 (`DRY_RUN_{HARVEST,MIRROR,FIX,EMAIL}`) 가 이 매트릭스의 코드 구현. cross-ref: `daily-repo-orchestrator` SKILL.md, `references/stage-flags-and-modes.md`.

## Quick start (가장 작은 첫 사이클)

```
1. Trigger: 일요일 21:00 KST (위키 자동갱신 cron과 같은 시각)
2. 첫 subagent: critic만 (redefine는 추후)
3. 첫 입력: 이번 주 너 워크플로우 (1주만 분석)
4. 첫 산출: [1][2] 만. [3][4]는 두 번째 사이클부터
5. 결정은 너: 자동 push X
```

**단일 공식**: "한 번에 한 사이클". 사이클 자체를 단일 공식화하지.

## 🆕 Idle-time 자율 hygiene 워크플로우 (2026-07-07 합의)

사용자가 "작업 없을 때 알아서 수정할 것 계속 수정해달라"고 명시적으로 권한을 줬을 때 발동. **자가개선 루프의 즉시 실행형 변형** — 4-phase 전체를 도는 게 아니라, "지금 보이는 작은 위생(hygiene) 작업"을 즉시 처리하고 보고.

### 사용자 명시 scope (2026-07-07 합의)

| 영역 | 권한 | 비고 |
|---|---|---|
| **Kanban ready/backlog** | ✅ 자율 처리 | false-positive close, 중복 de-dup, 명확한 close |
| **Linear 백로그** | ✅ 자율 조회 + 진행 | 단, Linear 이슈 close는 사용자 confirm 후 |
| **시스템 lint** (wiki/cron/git/memory) | ✅ 자율 처리 | read + 로컬 patch, 외부 시스템은 mirror-only |
| **Calendar** | ❌ **절대 손대지 않음** | 사용자 본인 작성 영역, 봇이 임의 변경 금지 |
| **Survey 응답** | ❌ 사용자 본인이 직접 | cron 리마인더만 봇이 보냄 |
| **Wiki push** (GitHub commit) | ⚠️ mirror-only | `daily-repo-orchestrator-mirror` 모드만 |
| **이메일 발송** | ❌ dry default | 명시 신호 없으면 절대 발송 금지 |

### 처리 가능 작업 (자율 OK)

1. **False-positive close** — 자동 감지가 잘못 만든 태스크. 검증 후 close:
   ```bash
   ls <claimed_missing_path>  # 실재 확인
   hermes kanban complete <id> --summary 'false-positive: <path> exists' --metadata '{"resolution":"false-positive"}'
   ```
2. **명확한 중복 de-dup** — 동일 본문/생성시각의 태스크가 2개 이상:
   - 둘 중 1개만 유지 (ID 알파벳순 큰 쪽 또는 더 오래된 본문 close)
   - 남기는 쪽은 손대지 않음
   - close summary에 "duplicate of `<other_id>`" 명시
3. **1분짜리 audit 액션** — audit 액션 중 LOW/1min 표시 → 검증 후 close:
   - 예: "X 스킬 archive" → `ls ~/.hermes/skills/ | grep X` → 부재 확인 → close
4. **로그 작성** — 처리 결과를 `~/mybotagent/hermes-logs/logs/YYYY/YYYY-MM-DD-HHMM-*.md`에 영구 기록 (git push는 별도)

### 처리 보류 (사용자 결정 영역)

자동으로 처리하지 않고, 후보로 보고만:

- **시간차 중복** (created 날짜가 다른데 같은 작업) — 사용자가 의도적으로 분리했을 수 있음
- **메타 작업** (다른 중복 정리를 다루는 태스크) — 예: "Kanban P1 중복 정리" 자체는 자동 close 금지
- **외부 시스템 변경** (GitHub push, 이메일, payment) — 자율 운영 매트릭스 그대로
- **Phase 3+ 자가개선 안건** — idle hygiene로 처리 ❌

### 워크플로우

```
[사용자 신호] "알아서 수정할 것 해줘"
   ↓
1. scope 확정 (사용자 발언에서 OK/NG 영역 추출)
   ↓
2. Kanban + Linear + 시스템 lint 병렬 스캔
   - hermes kanban list (ready/backlog)
   - Linear API: issues filter state ∈ {unstarted, started, backlog}
   - 위키/cron/memory sanity check
   ↓
3. 후보 분류:
   - [즉시 처리] false-positive / 명확 중복 / 1분짜리 audit 액션
   - [보고 보류] 시간차 중복 / 메타 작업 / 외부 시스템
   ↓
4. 즉시 처리 항목 close + summary 작성
   ↓
5. 로그 파일 작성 (영구 기록)
   ↓
6. 보고 (처리 N건 + 잔여 후보 + 다음 idle 시 자동화 가능한 후속)
```

### 보고 포맷 (Discord 짧은 버전)

```
## ✅ 자율 정리 완료 — [scope]

### 처리한 작업 (N개 close)
| 작업 | 처리 | 사유 |
|---|---|---|
| `t_xxx` | ❌ close (false-positive) | <path> 존재 확인 |
| `t_yyy` | ❌ close (dup) | `t_zzz`와 동일 |

### 결과
- ready: A → B, backlog C
- 로그: ~/mybotagent/hermes-logs/logs/YYYY/YYYY-MM-DD-HHMM-*.md

### 잔여 후보 (사용자 결정 권장)
- `t_a1` ≡ `t_a2` (시간차 N일) — 자동 처리 보류
- `t_meta` (메타 작업) — 자동 처리 보류

### 다음 idle 시 자동 후보
- `t_audit_N` [...]
```

### Pitfalls

1. **scope 무시 = 신뢰 손상**: 사용자가 "캘린더 손대지 마" 했는데 cron schedule을 건드리면 즉시 신뢰 손상. 사용자 발언의 scope 경계를 정확히 파싱할 것.
2. **자동 de-dup이 메타 작업을 덮어쓰는 함정**: "Kanban P1 중복 정리" 같은 태스크는 자동 close 금지 — 사용자가 보고 결정할 영역.
3. **Linear 동기화 누락**: Kanban close는 했지만 Linear 이슈(SHO-XX)가 미러링돼 있을 수 있음. `kanban_linear_mapping.json` 확인 후 SHO도 같이 close할지 결정 — 기본값은 Kanban만 close, Linear는 보고 (사용자가 명시 요청 시에만 SHO close).
4. **로그 파일 git push**: `mybotagent/hermes-logs`는 submodule인데 .git이 없는 경우 있음. `git status`로 확인 후 push 가능하면 push, 아니면 파일 작성만.
5. **명확한 증거 없는 close 금지**: "이거 중복인 것 같아서" 추측으로 close ❌. `hermes kanban show`로 본문/생성시각 비교 후 동일성 확인 후에만.
6. **시간차 중복은 사용자가 의도적으로 분리했을 수 있음**: 7/2와 7/3에 같은 watchdog 작업이 있으면, 사용자가 1차→2차로 분리한 것일 수 있음. 무조건 de-dup ❌.

### Self-consistency hook

이 워크플로우 자체가 self-improvement-loop의 **Phase 1 (WHAT) 결과를 자동 hygiene로 즉시 적용하는** 변형임을 명시. **Phase 2 (WHETHER) + Phase 3-4는 여전히 인간 승인 게이트**. idle hygiene는 **측정/관찰(WHAT)**에 한정 — 메트릭 정의 변경이나 시스템 구조 변경은 사용자에게 보고만.

---

## 🆕 실전 운영 cron (2026-07-07 합의, 검증된 3종)

자가개선 루프를 **운영 자동화**로 만든 3개 cron. 각자 read-only라 안전.

| cron_id | 스케줄 | 스크립트 | 용도 |
|---|---|---|---|
| `a79d072b2447` | 매일 22:00 UTC = 07:00 KST | `daily_repo_orchestrator_mirror.sh` | daily-repo-orchestrator (mirror-only prod) — Phase 1 WHAT의 일일 자동화 |
| `1387af94df7d` | 매주 일 12:00 UTC = 21:00 KST | `verdict_analyzer_weekly.sh` | PR verdict 분포/keyword 주간 분석 — Phase 1 WHAT의 자동 데이터 |
| `4076b821ac31` | 매주 일 23:00 UTC = 22:00 KST | `memory_auto_curator.sh` | wiki/memory 상태 점검 + 추세 감지 |

**연결 원리**:
- 매일 cron이 **WHAT (raw 데이터)** 자동 수집
- 주간 cron이 **Phase 1 WHAT** 분산 환경에서 자동 누적
- `[2] WHETHER` 메트릭 평가는 여전히 인간 + (또는 LLM critic subagent) 게이트
- `[3][4]` 는 사람 또는 사용자 confirm 후에만

**위험 분리 원칙**: raw 데이터 자동 수집은 read-only라 안전 → cron 가동 가능.
해석/판단은 인간 + 명시 명령이 필요 (Level 4 함정 회피).

→ `daily-repo-orchestrator` v1.3 (mirror-only prod 운영 모드) cross-ref

## 핵심 takeaway

> **자가개선 = sharp advisor, CEO는 아님. 최종 결정 = 너.**
> **WHAT ⇒ WHETHER ⇒ WHAT ⇒ HOW. 4단계 고정, 자동 적용 금지, 가치 검증 통과만 채택.**
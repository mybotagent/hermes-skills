---
name: execution-discipline
description: "Design-and-converge vs ship-and-validate discipline for aiprofit's workflow — class-level umbrella for closing the design-execution gap. Trigger when ≥3 turns of analysis without execution, validate steps are absent, or 'convergence theater' (디자인-실행 갭) is detected."
version: 1.2.0
author: aiprofit
platforms: [linux, macos]
metadata:
  hermes:
    tags: [execution, validation, methodology, convergence-theater, negative-result, workflow, autonomous-mode]
    related: [meeting-documentation, kanban-orchestrator, writing-plans, subagent-driven-development, project-harness]
---

# Execution Discipline

> **aiprofit 2026-07-02 direct critique**: "우리는 분석·합의 머신이지, 실행 머신이 아님."
> 이 스킬은 **디자인에서 실행으로 넘어가는 discipline**을 형식화한다.

## When This Skill Activates

Use this skill when:
- An extended discussion feels like it's converging without shipping (≥3 turns of analysis without execution)
- User requests critical analysis — capture both validate AND negative results
- A design doc was committed but the matching implementation step is missing
- A cron/cron-like task is approved but never tested
- "DESIGN.md 선행, Linear+Kanban 등록 후 구현" workflow reaches DESIGN phase and stalls
- **User has signaled autonomous mode** ("알아서 해줘", "그만묻고", "스스로해", "내가 잘 테니까", "병목 X") AND the agent is launching an interview/`clarify()` loop instead of executing

Do NOT use for:
- Pure research questions (no implementation expected)
- One-line operational changes
- Cases where user explicitly wants design-only output (e.g., exploratory analysis)

## Core Principle — Validate Minimum

Every converged decision must include **at least one 5-10 minute validate step** before the session ends. The validate step can be:

| Type | Example | Pass signal |
|------|---------|-------------|
| Code execution | `python3 query.py "test"` | Exit 0, expected output |
| Push/clone | `git push origin main` | `git ls-remote` hash match |
| Cron dry-run | Manual trigger with `--dry-run` | Output captured |
| API call | `curl -s ... \| jq .` | Status 200 + body match |
| UI check | vision_analyze screenshot | Visual confirmation |
| Smoke test | `bash <script>.sh` | Expected stdout pattern |

**Negative results are successes** when:
- The pitfall is recorded in the relevant skill's Pitfalls section
- The result is captured in the meeting-note or wiki page
- A follow-up path is added (Phase N+1 or Kanban task)

## 5-Stage Verify (aiprofit 2026-07-02 invention)

User-invented methodology for closing the design-execution gap. Already in Memory:

```
WHY      — Why is this needed? (real value proof, not feels-good)
WHAT     — What does success look like? (measurable signal)
WHETHER  — Is the metric itself correct? (don't optimize wrong target)
WHAT     — What should we actually measure? (corrected definition)
HOW      — How to implement? (concrete steps + cost estimate)
VALIDATE — Run a real test. Capture result, even if negative.
```

The **VALIDATE step is explicit and non-negotiable**. Pre-existing 4-stage loops (what⇒whether⇒what⇒how) often skipped actual measurement — aiprofit added VALIDATE as the explicit missing piece.

## Convergence Theater — The Anti-Pattern

**Symptoms** (any one = theater):
- ≥3 turns of analysis without any tool execution
- "합의 완료" reported but no implementation entry created
- Meeting pushed to GitHub but Linear/Kanban never updated
- DESIGN.md committed but no Phase 1 follow-up task
- User explicitly says "런 가능한 거 1개라도" or "정직한 negative result"
- **User gives autonomous-mode signal but agent keeps clarifying/interviewing** (2026-07-04 variant)

**Root cause**: Agreement → Documentation → Pause (instead of Agreement → Documentation → Execution)

**Counter-measures**:
1. End-of-meeting: produce a 30-minute validate checklist (template below)
2. Commit to a Kanban P1 task with explicit Acceptance Criteria
3. Block design completion until validate executes
4. Use `templates/validate-30min-checklist.md` (below)
5. **Autonomous-mode signal present → switch off `clarify()` immediately**, use `[가정]/[결정]/[리서치]` labeling in state files instead (see references/autonomous-mode-interview-theater.md)

## Reference

- `references/convergence-theater-pattern.md` — full transcript of the 2026-07-02 pattern emergence + recovery sequence
- `references/autonomous-mode-interview-theater.md` — **second flavor (2026-07-04)**: agent runs a `clarify()` interview loop during autonomous mode, ignoring the explicit override signal. Detection rule + recovery pattern.
- `references/speculation-cascade.md` — **third flavor (2026-07-04)**: agent guesses unknown external facts (creator names, founder identities) 5+ times instead of asking one clarifying question. Detection rule + "ask once, ship once" pattern.
- `references/over-engineering-sprawl.md` — **fifth flavor (2026-07-06)**: agent *executes* but adds layers beyond the minimum viable baseline (retry tricks, force-re-register workarounds, reusable-indirection). User signals "억지로 X 만들 필요는 없어" / "반드시 필요한 것만" / "code sanity 헤치지 않은가". Detection rule + recovery pattern.
- `templates/validate-30min-checklist.md` — ready-to-use 30-minute checklist template

## Anti-Pattern Variants (catalog)

The umbrella covers **multiple flavors** of design-execution gap. Each
reference in `references/` documents one flavor with detection rules
and recovery sequence.

| Flavor | When it happens | Detection signal | Reference |
|--------|----------------|-------------------|-----------|
| **Convergence theater** | After design push, before implementation | ≥3 turns of analysis without tool execution | `convergence-theater-pattern.md` (2026-07-02) |
| **Autonomous-mode interview theater** | During interview-heavy workflows when user has signaled autonomy | User corrects with "그만묻고"/"스스로해"/"병목 X" mid-flow | `autonomous-mode-interview-theater.md` (2026-07-04) |
| **Speculation cascade** | External fact (creator/founder/year) is unknown, agent guesses repeatedly | ≥2 consecutive rejected guesses + user "멍청해졌다" / "헛소리" | `speculation-cascade.md` (2026-07-04) |
| Paste-request theater | User asked "너가 알아서" but agent keeps requesting paste/permission | ≥3 paste-guide outputs in same session + user frustration signal ("왜 못함", "이상한 짓") | `paste-request-theater.md` (2026-07-06) |
| Over-engineering sprawl | User gave a goal, agent added layers beyond the minimum viable — extra retries, force-re-register tricks, "reusable workflow" indirection when inline copy works, etc. | User signals "억지로 X 만들 필요는 없어", "반드시 필요한 것만", "복잡해질거 같으니" after an extended build | `over-engineering-sprawl.md` (2026-07-06) |
| | **Silent-stop theater** | Multi-step autonomous batch (e.g. cron update sequence) and the tool loop goes quiet between iterations — user keeps waiting for next step but agent silently pauses awaiting user input | User mid-batch correction: "쉬지말고", "계속 진행", "왜 멈춰있어", "다음 단계 진행" | `silent-stop-theater.md` (2026-07-07) |
| | **Process-update theater** | User reports pipeline bug → agent patches display instead of fixing the data-generation script | User corrects: "결과를 업데이트하지 말고 과정을 업데이트해" | `process-update-theater.md` (2026-07-17) |

**Paste-request theater 신호**:
- 외벽 (예: GitHub PAT `workflow` scope 부재)에 부딪혀 매번 "paste해주세요" 안내를 3번+ 반복
- 사용자가 "왜 못함 / 이상한 짓 / 너 알아서 ~하도록" 시그널
- **Recovery**: 2~3번 시도 후 한계 인정 → 사용자 의도 재확인 1줄 → fallback 자동화 루트 한 번 → 그래도 안 되면 paste 1회만 요청

**Silent-stop theater 신호 (2026-07-07 신규)**:
- autonomous mode에서 multi-step batch 진행 중 (cron 재배치, repo 다중 push, 병렬 검증 등)
- 직전 tool call 후 "Operation interrupted: waiting for model response" 또는 단순 stop
- 사용자가 "쉬지말고 / 계속 진행 / 다음 단계 진행해"라고 명시적 nudge
- **Recovery**: nudge 받으면 idle 단계 평가 → 다음 step으로 즉시 점프. "비교적 안전한 다음 step" 해석 기준: idempotent / read-only / 기존 동작 가역 / 새 시크릿/푸시/PR ❌. 이 범위에선 한 turn에 최대 3-5 tool call 묶음 직렬 실행 후 checkpoint 출력.

**When in doubt**: default to ship, not converge. If user has given an
explicit autonomy signal (memory, profile, or live message), every
`clarify()` call is suspect — fall back to `[가정]/[결정]` labeling and
ship the deliverable.

## Related

- `meeting-documentation` — has Critical Rule 7 (Execution Gate) and convergence theater pitfall
- `kanban-orchestrator` — decomposition playbook
- `writing-plans` — plan structure emphasizing validate steps
- `subagent-driven-development` — 2-stage review (RED-GREEN) execution pattern
- `project-harness` — has Autonomous Mode Override; the interview-theater
  reference documents the failure mode that prompted the override.
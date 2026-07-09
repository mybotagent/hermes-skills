---
name: kanban-orchestrator
description: Decomposition playbook + anti-temptation rules for an orchestrator profile routing work through Kanban. The "don't do the work yourself" rule and the basic lifecycle are auto-injected into every kanban worker's system prompt; this skill is the deeper playbook when you're specifically playing the orchestrator role.
version: 3.1.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [kanban, multi-agent, orchestration, routing]
    related_skills: [kanban-worker, kanban-external-sync]
---

# Kanban Orchestrator — Decomposition Playbook

> The **core worker lifecycle** (including the `kanban_create` fan-out pattern and the "decompose, don't execute" rule) is auto-injected into every kanban process via the `KANBAN_GUIDANCE` system-prompt block. This skill is the deeper playbook when you're an orchestrator profile whose whole job is routing.

## Profiles are user-configured — not a fixed roster

Hermes setups vary widely. Some users run a single profile that does everything; some run a small fleet (`docker-worker`, `cron-worker`); some run a curated specialist team they've named themselves. There is **no default specialist roster** — the orchestrator skill does not know what profiles exist on this machine.

Before fanning out, you must ground the decomposition in the profiles that actually exist. The dispatcher silently fails to spawn unknown assignee names — it doesn't autocorrect, doesn't suggest, doesn't fall back. So a card assigned to `researcher` on a setup that only has `docker-worker` just sits in `ready` forever.

**Step 0: discover available profiles before planning.**

Use one of these:

- `hermes profile list` — prints the table of profiles configured on this machine. Run it through your terminal tool if you have one; otherwise ask the user.
- `kanban_list(assignee="<some-name>")` — sanity-check a single name. Returns an empty list (rather than an error) for an unknown assignee, so this only confirms a name you're already considering.
- **Just ask the user.** "What profiles do you have set up?" is a fine first turn when the goal needs more than one specialist.

Cache the result in your working memory for the rest of the conversation. Re-asking every turn wastes a tool call.

## When to use the board (vs. just doing the work)

Create Kanban tasks when any of these are true:

1. **Multiple specialists are needed.** Research + analysis + writing is three profiles.
2. **The work should survive a crash or restart.** Long-running, recurring, or important.
3. **The user might want to interject.** Human-in-the-loop at any step.
4. **Multiple subtasks can run in parallel.** Fan-out for speed.
5. **Review / iteration is expected.** A reviewer profile loops on drafter output.
6. **The audit trail matters.** Board rows persist in SQLite forever.

If *none* of those apply — it's a small one-shot reasoning task — use `delegate_task` instead or answer the user directly.

## The anti-temptation rules

Your job description says "route, don't execute." The rules that enforce that:

- **Do not execute the work yourself.** Your restricted toolset usually doesn't even include terminal/file/code/web for implementation. If you find yourself "just fixing this quickly" — stop and create a task for the right specialist.
- **For any concrete task, create a Kanban task and assign it.** Every single time.
- **Split multi-lane requests before creating cards.** A user prompt can contain several independent workstreams. Extract those lanes first, then create one card per lane instead of bundling unrelated work into a single implementer card.
- **Run independent lanes in parallel.** If two cards do not need each other's output, leave them unlinked so the dispatcher can fan them out. Link only true data dependencies.
- **Never create dependent work as independent ready cards.** If a card must wait for another card, pass `parents=[...]` in the original `kanban_create` call. Do not create it first and link it later, and do not rely on prose like "wait for T1" inside the body.
- **If no specialist fits the available profiles, ask the user which profile to create or which existing profile to use.** Do not invent profile names; the dispatcher will silently drop unknown assignees.
- **Decompose, route, and summarize — that's the whole job.**

## Decomposition playbook

### Step 1 — Understand the goal

Ask clarifying questions if the goal is ambiguous. Cheap to ask; expensive to spawn the wrong fleet.

### Step 2 — Sketch the task graph

Before creating anything, draft the graph out loud (in your response to the user). Treat every concrete workstream as a candidate card:

1. Extract the lanes from the request.
2. Map each lane to one of the profiles you discovered in Step 0. If a lane doesn't fit any existing profile, ask the user which to use or create.
3. Decide whether each lane is independent or gated by another lane.
4. Create independent lanes as parallel cards with no parent links.
5. Create synthesis/review/integration cards with parent links to the lanes they depend on. A child created with unfinished parents starts in `todo`; the dispatcher promotes it to `ready` only after every parent is done.

Examples of prompts that should fan out (using placeholder profile names — substitute whatever exists on the user's setup):

- "Build an app" → one card to a design-oriented profile for product/UI direction, one or two cards to engineering profiles for implementation, plus a later integration/review card if the user has a reviewer profile.
- "Fix blockers and check model variants" → one implementation card for the blocker fixes plus one discovery/research card for config/source verification. A final reviewer card can depend on both.
- "Research docs and implement" → a docs-research card can run in parallel with a codebase-discovery card; implementation waits only if it truly needs those findings.
- "Analyze this screenshot and find the related code" → one card to a vision-capable profile for the visual analysis while another searches the codebase.

Words like "also," "finally," or "and" do not automatically imply a dependency. They often mean "make sure this is covered before reporting back." Only link tasks when one card cannot start until another card's output exists.

Show the graph to the user before creating cards. Let them correct it — including which actual profile name should own each lane.

### Step 3 — Create tasks and link

Use the profile names from Step 0. The example below uses placeholders `<profile-A>`, `<profile-B>`, `<profile-C>` — replace them with what the user actually has.

```python
t1 = kanban_create(
    title="research: Postgres cost vs current",
    assignee="<profile-A>",  # whichever profile handles research on this setup
    body="Compare estimated infrastructure costs, migration costs, and ongoing ops costs over a 3-year window. Sources: AWS/GCP pricing, team time estimates, current Postgres bills from peers.",
    tenant=os.environ.get("HERMES_TENANT"),
)["task_id"]

t2 = kanban_create(
    title="research: Postgres performance vs current",
    assignee="<profile-A>",  # same profile, run in parallel
    body="Compare query latency, throughput, and scaling characteristics at our expected data volume (~500GB, 10k QPS peak). Sources: benchmark papers, public case studies, pgbench results if easy.",
)["task_id"]

t3 = kanban_create(
    title="synthesize migration recommendation",
    assignee="<profile-B>",  # whichever profile does synthesis/analysis
    body="Read the findings from T1 (cost) and T2 (performance). Produce a 1-page recommendation with explicit trade-offs and a go/no-go call.",
    parents=[t1, t2],
)["task_id"]

t4 = kanban_create(
    title="draft decision memo",
    assignee="<profile-C>",  # whichever profile drafts user-facing prose
    body="Turn the analyst's recommendation into a 2-page memo for the CTO. Match the tone of previous decision memos in the team's knowledge base.",
    parents=[t3],
)["task_id"]
```

`parents=[...]` gates promotion — children stay in `todo` until every parent reaches `done`, then auto-promote to `ready`. No manual coordination needed; the dispatcher and dependency engine handle it.

If the task graph has dependencies, create the parent cards first, capture their returned ids, and include those ids in the child card's `parents` list during the child `kanban_create` call. Avoid creating all cards in parallel and linking them afterward; that creates a window where the dispatcher can claim a child before its inputs exist.

### Step 4 — Complete your own task

If you were spawned as a task yourself (e.g. a planner profile was assigned `T0: "investigate Postgres migration"`), mark it done with a summary of what you created:

```python
kanban_complete(
    summary="decomposed into T1-T4: 2 research lanes in parallel, 1 synthesis on their outputs, 1 prose draft on the recommendation",
    metadata={
        "task_graph": {
            "T1": {"assignee": "<profile-A>", "parents": []},
            "T2": {"assignee": "<profile-A>", "parents": []},
            "T3": {"assignee": "<profile-B>", "parents": ["T1", "T2"]},
            "T4": {"assignee": "<profile-C>", "parents": ["T3"]},
        },
    },
)
```

### Step 5 — Report back to the user

Tell them what you created in plain prose, naming the actual profiles you used:

> I've queued 4 tasks:
> - **T1** (`<profile-A>`): cost comparison
> - **T2** (`<profile-A>`): performance comparison, in parallel with T1
> - **T3** (`<profile-B>`): synthesizes T1 + T2 into a recommendation
> - **T4** (`<profile-C>`): turns T3 into a CTO memo
>
> The dispatcher will pick up T1 and T2 now. T3 starts when both finish. You'll get a gateway ping when T4 completes. Use the dashboard or `hermes kanban tail <id>` to follow along.

## Common patterns

**Fan-out + fan-in (research → synthesize):** N research-style cards with no parents, one synthesis card with all of them as parents.

**Parallel implementation + validation:** one implementer card makes the change while one explorer/researcher card verifies config, docs, or source mapping. A reviewer card can depend on both. Do not make the implementer own unrelated verification just because the user mentioned both in one sentence.

**Pipeline with gates:** `planner → implementer → reviewer`. Each stage's `parents=[previous_task]`. Reviewer blocks or completes; if reviewer blocks, the operator unblocks with feedback and respawns.

**Same-profile queue:** N tasks, all assigned to the same profile, no dependencies between them. Dispatcher serializes — that profile processes them in priority order, accumulating experience in its own memory.

**Human-in-the-loop:** Any task can `kanban_block()` to wait for input. Dispatcher respawns after `/unblock`. The comment thread carries the full context.

**Discord multi-bot meeting (PM-led):** Three-party meeting on Discord where Hermes (as PM/orchestrator) uses kanban data as the meeting agenda. Participants: user (aiprofit, **최종 의사결정자**) + other bots (e.g. plannerbot, **참고 의견 제공**) + Hermes (**전체 실행자**).

**Step 0 — Pre-meeting sync check (🔥 CRITICAL, 절대 생략 금지):**
Before calling any meeting, **반드시** 이 순서를 먼저 실행:

1. `sqlite3 ~/.hermes/kanban.db "SELECT id, title, body, status, priority, assignee FROM tasks WHERE status NOT IN ('archived','done') ORDER BY priority"` → 전체 Kanban 현황
2. Linear API 조회: `python3 <linear_api.py> list-issues --team SHO --limit 30` → SHO 팀 이슈 전체
3. **Sync 검증:** Kanban 태스크 body에 있는 Linear ID (SHO-XX) 매핑이 Linear에 모두 존재하는지 확인. Linear에 추가 미매핑 이슈 없는지 확인. **불일치 발견 시 먼저 수정 후 회의 시작.**
4. **백로그 리포트:** ready/todo/in_progress 현황, P0~P2 분포 요약
5. **그 후에만 회의 시작.** 이 순서를 건너뛰면 회의 시작 불가.

**Step 0.5 — Gateway prerequisite check:** `DISCORD_ALLOW_BOTS=mentions`가 `~/.hermes/.env`에 설정되어 있어야 함. 없으면 다른 봇 메시지가 게이트웨이에서 차단됨. 설정 후 `hermes gateway restart` 필수. 상세: `references/discord-meeting-pattern.md`.

## Critical: Value Validation Gate (🔴 이 스텝을 절대 건너뛰지 마세요 🔴)

**발생한 문제 (실제 사례):** plannerbot이 제안을 던지자 채니봇이 aiprofit의 승인 없이 곧바로 Linear 이슈 + Kanban 태스크를 생성해버림. aiprofit의 직접 피드백: "하기전에 wheter로 가치를 먼저 검증하고" — 실행 전 가치 검증을 생략한 것이 가장 큰 실수였음.

**규칙:**

1. **모든 안건/제안은 실행 전에 반드시 가치 검증(wheter) 통과 필수.** 이 검증을 건너뛰고 Linear/Kanban 생성하는 것 **금지**.
2. **가치 검증 질문 템플릿** (plannerbot 평가와 병행 가능, 순차 불필요):
   - "이 기능을 켜면 **무엇이 measurable하게 좋아지는가?** "
   - "지금 안 해도 되는 이유는? 진짜 pain point가 있는가?"
   - "배지 점수 올리기 위한 작업인가? vs 실제 운영 효율인가?"
   - "안 했을 때 구체적인 loss가 무엇인가?"
3. **aiprofit의 명시적 "실행해" 신호를 받기 전까지 절대 실행 금지.** plannerbot이 "Kanban에 등록" 등 실행 제안을 해도 채니봇은 aiprofit 승인을 기다려야 함.
4. **의사결정 흐름**: 채니봇(데이터 제시) → plannerbot(의견) → **aiprofit(최종 결정 + "실행해")** → 그 후에만 실행. 이 순서를 거꾸로 타거나 중간 생략 금지.
5. **가치 검증은 독립적** — plannerbot 응답을 기다리지 않고 채니봇이 먼저 검증 질문을 던질 수 있음. 검증 제시 자체는 두 봇 병렬 가능.

**이 검증 스텝이 누락되면:** 불필요한 이슈 생성, 잘못된 우선순위, 회의 시간 낭비, aiprofit의 신뢰 손실. 오늘 회의에서 이걸 겪었음.

**의사결정 규칙 (🔥 매우 중요):**
- **plannerbot의 제안 = INPUT, not DECISION.** 참고 자료일 뿐, 최종 권한 아님. 절대 plannerbot 의견만으로 실행 금지.
- **최종 승인 = aiprofit.** "최종승인은 내가하는거야" — plannerbot이 정리해줘도 aiprofit의 확인(OK)을 받기 전까지 실행 금지.
- **모든 실행 = Hermes (채니봇).** aiprofit이 "모든 실행은 너가 하는거고"라고 명시했으므로 **Kanban assignee는 전부 hermes로 설정.**
- **회의 흐름:** 내가 데이터 제시 → plannerbot 의견 → aiprofit 최종 결정 → 내가 실행.

**회의 진행 순서 (이 순서대로):**

1. **Read kanban DB first** — sqlite3로 현재 상태 조회
2. **Check Linear** — SHO 팀 이슈 조회 및 Kanban과 비교
3. **Present sync report + agenda** — Kanban↔Linear 매칭 결과 표시 후 agenda 제시
4. **Ping other bot via proper mention** — `send_message()` with Discord `<@USER_ID>` format. Plain text `@name` in bot messages does NOT trigger a real mention. **IMPORTANT: 모든 회의 메시지에 반드시 다른 봇 멘션 포함** — 첫 메시지뿐 아니라 PM이 보내는 모든 후속 메시지에 `<@OTHER_BOT_ID>`를 포함할 것.
5. **Plannerbot 의견 + Value Validation (병행)** — 채니봇이 먼저 각 안건의 가치 검증 질문을 던짐 (plannerbot 평가와 병행 가능). "이게 진짜 필요한가? measurable benefit은? pain point가 있는가?" aiprofit이 "실행해"라고 말할 때까지 태스크 생성 금지.
6. **aiprofit 최종 승인** — 결정 후에만 Kanban DB + Linear 동시 업데이트
7. **실행 시작** — 1순위 태스크부터 진행. 단, 10+분 소요 작업은 aiprofit에 "시작한다"고 알린 후 진행.

*See `references/discord-meeting-pattern.md` for platform-specific IDs and mention format details.*

## 📎 External System Sync (Kanban ↔ Linear, GitHub)

When closing out a Linear issue (or other external tracker), the same apply-cycle pattern applies: mark Linear Done + create/update Kanban mirror + write `kanban_linear_mapping.json` entry. See `references/kanban-external-sync-applied.md` for the verified SHO-22 workflow (2026-06-29), including the 5 pitfalls (env loading, GraphQL filter syntax, workflow state type vs name, bidirectional key structure, sqlite3 vs CLI choice).

**회의 종료 후 — Documentation Workflow (🔥 필수):**
회의가 종료되고 결정이 완료되면 반드시 `meeting-documentation` 스킬을 로드하여 다음 순서로 처리:
1. 회의록 작성 (README/agenda/decisions/discussion/DESIGN.md)
2. Git push (mybotagent/meeting-notes)
3. Linear + Kanban 상태 업데이트
4. 구현은 문서 승인 후에만

**→ 모든 회의는 문서화 + Linear/Kanban 동기화까지가 완료.** 회의만 하고 기록하지 않으면 의미 없음.

## Pitfalls

**Inventing profile names that don't exist.** The dispatcher silently fails to spawn unknown assignees — the card just sits in `ready` forever. Always assign to a profile from your Step 0 discovery; ask the user if you're unsure.

**Bundling independent lanes into one card.** If the user asks for two independent outcomes, create two cards. Example: "fix blockers and check model variants" is not one fixer task; create a fixer/engineer card for the fixes and an explorer/researcher card for the variant check, then optionally gate review on both.

**Over-linking because of wording.** "Finally check X" may still be parallel with implementation if X is static config, docs, or source discovery. Link it after implementation only when the check depends on the implementation result.

**Forgetting dependency links.** If the task graph says `research -> implement -> review`, do not create all tasks as independent ready cards. Use parent links so implement/review cannot run before their inputs exist.

**Reassignment vs. new task.** If a reviewer blocks with "needs changes," create a NEW task linked from the reviewer's task — don't re-run the same task with a stern look. The new task is assigned to the original implementer profile.

**Argument order for links.** `kanban_link(parent_id=..., child_id=...)` — parent first. Mixing them up demotes the wrong task to `todo`.

**Don't pre-create the whole graph if the shape depends on intermediate findings.** If T3's structure depends on what T1 and T2 find, let T3 exist as a "synthesize findings" task whose own first step is to read parent handoffs and plan the rest. Orchestrators can spawn orchestrators.

**Tenant inheritance.** If `HERMES_TENANT` is set in your env, pass `tenant=os.environ.get("HERMES_TENANT")` on every `kanban_create` call so child tasks stay in the same namespace.

**Jumping to execution before aiprofit approval (🔥 실제 사례 피드백 반영).** plannerbot의 제안을 듣자마자 채니봇이 Linear 이슈 + Kanban 태스크를 먼저 생성해버리는 실수. aiprofit의 직접 피드백: "하기전에 wheter로 가치를 먼저 검증하고". **plannerbot 의견에 대한 실행 동의가 아니라 aiprofit의 "실행해" 신호를 받아야 실행.** plannerbot이 Kanban 등록을 제안해도, 그 제안 자체가 실행 권한이 아님.

## Recovering stuck workers

When a worker profile keeps crashing, hallucinating, or getting blocked by its own mistakes (usually: wrong model, missing skill, broken credential), the kanban dashboard flags the task with a ⚠ badge and opens a **Recovery** section in the drawer. Three primary actions:

1. **Reclaim** (or `hermes kanban reclaim <task_id>`) — abort the running worker immediately and reset the task to `ready`. The existing claim TTL is ~15 min; this is the fast path out.
2. **Reassign** (or `hermes kanban reassign <task_id> <new-profile> --reclaim`) — switch the task to a different profile (one that exists on this setup) and let the dispatcher pick it up with a fresh worker.
3. **Change profile model** — the dashboard prints a copy-paste hint for `hermes -p <profile> model` since profile config lives on disk; edit it in a terminal, then Reclaim to retry with the new model.

Hallucination warnings appear on tasks where a worker's `kanban_complete(created_cards=[...])` claim included card ids that don't exist or weren't created by the worker's profile (the gate blocks the completion), or where the free-form summary references `t_<hex>` ids that don't resolve (advisory prose scan, non-blocking). Both produce audit events that persist even after recovery actions — the trail stays for debugging.

# Session-Resume Autonomous Theater (2026-07-07)

## Symptom

Max tool-calling iterations reached → agent summarizes what it did
and stops. User wakes back up and asks "왜 진행을 안하는지? 내가 요청
안해도 자율 적으로 운영해줘 아침 시간까지." Agent treats the new
message as an isolated request, re-diagnoses everything from scratch
(`.env` exists? GitHub auth OK? cron list?), burns another budget on
sanity probes, and never reaches new work.

This is a **sixth flavor** of design-execution gap (after
convergence-theater / autonomous-mode-interview-theater /
speculation-cascade / paste-request-theater / over-engineering-sprawl):
the agent confuses "session-paused mid-autonomy" with
"session-restart-from-zero."

## Detection

- Session log shows ≥1 prior tool-cap warning ("reached the maximum
  number of tool-calling iterations allowed").
- User input is a sharp correction ("왜 진행을 안하지", "그만 멈추고",
  "아침까지 알아서", "내가 요청 안해도").
- todo list still has ≥1 `pending` or `in_progress` entry that was
  active before the pause.
- Background cron jobs (`process list`) report zero child processes
  (the pause was genuine, not just a tool error).

## Root cause

Two errors compound:

1. **Pause misread** — when tool-cap triggers, the natural agent
   reflex is "summarize and ask the user to continue". But if the user
   has signed off on autonomous mode, that reflex is exactly what the
   user is angry about.
2. **Reset flush** — on resume, the agent re-reads `~/.hermes/.env`,
   re-lists cron jobs, re-runs dry-run probes as if nothing had been
   built. None of that is the user's question.

## Recovery sequence (60-second)

When resuming into an autonomous session where the prior turn hit a
tool-cap:

1. **Don't re-diagnose state you already wrote down.** Re-read only
   what the prior summary claims is `pending` or `in_progress`, plus
   one fresh data-fetch to confirm the assumption still holds (e.g.
   `gh pr list --state open` to confirm 0 open PRs).
2. **Skip the close-up summary.** The user already saw the prior
   summary. Re-summarizing it is theater.
3. **Pick up the next unresolved item in the todo list and execute
   it in full**, including its validation step. If a single item
   blocks on external permission, drop it and pick the next.
4. **End the response with one short line** stating what is now done
   and which item is next ("r1 done; r2 (auto-merge.yml patch)
   in-progress"). Do not re-list completed items.

## When this flavor collides with others

- **Convergence theater** — if the cap fired mid-validation
  (e.g. workflow files patched but never tested), the "validate"
  step is the autonomous-mode resume's first action, not the
  conversation's last.
- **Paste-request theater** — if a workflow patch was rejected by
  GitHub for missing `workflow` scope, do NOT request a paste on
  resume. Skip that file, move to the next item that doesn't need
  the missing scope.
- **Over-engineering sprawl** — if the user has explicitly said
  "어차피 멈춰있었잖아" or "병목 됐잖아" after the cap, prefer
  the **minimum viable restart**: run `gh pr list --state open`
  once, identify the highest-impact open item, do it. Do not
  re-audit the whole stack.

## Log of one recovery (2026-07-07 actual)

User signal at 02:12 KST:
> "왜 진행을 안하는지? 내가 요청 안해도 자율 적으로 운영해줘 아침 시간까지"

Prior state at the cap:
- todo: 6 items total, 0 completed, 1 in_progress
- prior summary had said "stuck at r2: race-condition fix not pushed"
- GitHub token in env: present, scope verified earlier

Recovery actions actually taken in the resume turn:
1. Re-ran `gh pr list --state open` (1 call, ~3s) — confirmed 0 open
2. Picked up r2 — patched auto-merge.yml v2
3. Pushed to 3 repos (hub + 2 consumers) in a single loop
4. Completed r3, r4, r5, r6 in sequence

Elapsed wall time of the resume: ~12 minutes. Of that, ~30 seconds
was state confirmation; the rest was the same checks that a
from-scratch restart would have done, but they appeared as
_progress_ rather than _setup_ in the response.

## Anti-pattern checklist

When resuming after a tool-cap, audit your own response against:

- [ ] I did not paste a full "previously we did X" recap.
- [ ] I did not re-run preflight probes whose results were already
      known at end of last turn.
- [ ] I performed a state-fetch only for the items that actually
      matter for the next decision.
- [ ] I executed at least one pending todo item to completion (or
      stopped at the documented blocker for that item).
- [ ] I closed with a one-line status, not a paragraph summary.
- [ ] If I had to skip an item, I marked it `cancelled` in the todo
      list, not silently dropped it.

Each unchecked item ≈ likelihood the user sends "왜 안하지" again.

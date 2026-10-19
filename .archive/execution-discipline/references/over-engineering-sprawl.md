# Over-engineering Sprawl (2026-07-06)

The fifth anti-pattern variant. Distinct from convergence theater: agent
**does** ship, but ships a much larger system than the goal requires.

## Symptoms

- User gave a single concrete goal; the agent produced 3-5 architectural
  layers (e.g. "reusable workflow" indirection, retry-with-backoff tricks,
  force-re-register experiments, alternative-base-url normalization) when
  the working baseline already existed
- Each layer adds a PR + commit + retry + debug cycle
- User signals land late: **"억지로 X 만들 필요는 없어 / 반드시 필요한 것만 /
  복잡해질거 같으니 / Code Sanity 헤치지 않은가"**
- The original goal works long before the sprawl is finished
- Skill texts accumulate over-broad claims ("X never fires") that the
  current session later has to retract

## Real example (this session)

User asked for a PR auto-review + auto-merge gate. After ~10 PRs of work the
hub ran correctly. **Then** the agent kept adding:

- `merge-gate.yml` → `pr-merge-gate.yml` rename (twice) trying to force
  workflow re-registration
- `review-bot.yml` → `anthropics/claude-code-action@v1` swap (failed, GitHub
  App not installed) → `claude -p` swap (also unviable) → back to direct
  MiniMax API (which had worked from minute 1)
- `reusable workflow + secrets: inherit` indirection (failed: cross-repo
  private) → eventually each consumer copies the script inline
- Two cron jobs added without user confirmation

User intervention: **"억지로 github action review를 만들 필요는 없어 반드시
필요한 ci setup을 해야해. 1차적으로 이슈 -> PR 시에 가치를 먼저 검토하고 이 PR이
오버엔지니어링이나 불필요한 코드를 만들지 않은가 Code Sanity를 해치지 않은가
반드시 필요한 것인가를 너가 1차적으로 검증 후에 해야해."**

The user's correction is the **canonical over-engineering sprawl signal**.

## Detection rule

After **3+ commits / PRs / scripts added beyond the minimum viable baseline**,
self-audit:

1. **Was the original baseline + 1 verify step enough to ship the goal?**
   If yes, the additions are over-engineering until proven otherwise.
2. **Does the user have a known preference for minimal solutions?**
   aiprofit's `value-first` / `code-sanity` / `단일공식` preferences all
   point this direction. Skill memory: no-branching, no exceptions, no
   conditions.
3. **Did any of the additions come from an external conversation (dev-harness-kit,
   claude-code-action, etc.) rather than the user's stated goal?** If yes,
   they were probably imported reflexively, not because the goal demanded
   them.
4. **Have any of the inherited "claims" in the skill been validated in this
   session?** Claims like "same-repo PR trigger never fires on free plan" can
   harden into self-imposed constraints that fight reality.

## Recovery pattern

When the user signals sprawl (or you self-audit and detect it):

1. **Stop adding layers.** Don't open more PRs to test more workarounds.
2. **Self-audit loudly**: list what was added beyond the minimum, why each was
   added, and which can be reverted.
3. **Re-validate the minimal baseline end-to-end** before any new PR.
4. **Patch the skill(s)** that seeded the sprawl with corrected, narrower
   claims. Don't leave stale "never fires" / "always X" assertions in
   skills — they corrupt future sessions.
5. **Park remaining add-ons** in a "Phase 2 / Phase 3" todo with explicit
   value-first gate ("이게 필요한가?" 체크 먼저). Don't silently stop;
   surface the parked work.

## Why this isn't just "convergence theater"

Convergence theater = no execution. Over-engineering sprawl = excess
execution. Same meta-pattern (agent ignoring the user's stated boundary),
opposite failure modes. Both benefit from a `[가정]/[결정]` discipline
loop where every added layer requires an explicit value justification.

## Related

- `repo-intent-reading` — read the asset's contract before importing layers.
  Most sprawl in this session came from reflexively importing dev-harness-kit's
  workflows before checking whether the user's hub actually needed that
  shape.
- `value-validation-skill` (sibling concept, may not be a separate skill)
  — the "이게 필요한가?" gate the user explicitly demanded before further work.

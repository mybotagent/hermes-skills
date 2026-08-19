# Pending Patch: hermes-config-management + model-switcher (2026-08-18)

These patches are BLOCKED in the review-session context. Main-session agent must apply.

## Patch 1: hermes-config-management/SKILL.md

**Add after the "⚠ Critical pitfall" block (after "Use `hermes config set` CLI. Never..."):**

```markdown
## 🚨 Gateway cannot restart itself from inside (2026-08-18)
Running `hermes gateway restart` or `systemctl --user restart hermes-gateway` from **inside the gateway process** always fails with:
> Cannot restart or stop the gateway from inside the gateway process. Run `hermes gateway restart` from a separate shell outside the running gateway.

**Workaround — use `delegate_task` to spawn a leaf subagent:**
```
delegate_task(
  goal="Restart the hermes-gateway systemd service and confirm it started successfully.",
  context="Run: systemctl --user restart hermes-gateway && sleep 3 && systemctl --user status hermes-gateway"
)
```
The subagent runs in an isolated context outside the gateway process, so it can signal restart without SIGTERM self-termination.
```

## Patch 2: model-switcher/SKILL.md

### 2a. Update "모델 전환 (메인 ↔ 보조)" section
Replace current Option 1 with:
```bash
# 1) MiniMax-M2.5 (cheapest) to main, DeepSeek flash as fallback
hermes config set model.provider minimax
hermes config set model.default MiniMax-M2.5
hermes config set model.base_url https://api.minimax.io/v1
hermes config set fallback_providers '["deepseek"]'
```

Replace current Option 2 with:
```bash
# 2) DeepSeek flash to main, MiniMax-M2.5 as fallback
hermes config set model.provider deepseek
hermes config set model.default deepseek-v4-flash
hermes config set model.base_url https://api.deepseek.com/v1
hermes config set fallback_providers '["minimax"]'
```

### 2b. Update "모델별 가이드" table
Replace DeepSeek row with:
| DeepSeek V4 Flash | deepseek | https://api.deepseek.com/v1 | deepseek-v4-flash only |

### 2c. Update the pro-ban section
Replace the "🚫 deepseek-v4-pro 사용 금지" section with:

```markdown
## 🚫 deepseek-v4-pro 사용 금지 (2026-08-18 정책)

**aiprofit 정책: deepseek-v4-pro는 절대 사용 금지. deepseek는 flash만 허용.**

Current enforced state (2026-08-18):
- `providers.deepseek.model`: deepseek-v4-flash ✅
- `providers.deepseek.available_models_json`: deepseek-v4-flash only ✅
- `fallback_providers`: `[]` (no deepseek fallback) ✅ — updated today
- Default model: MiniMax-M2.5 (cheapest MiniMax) ✅ — updated today

Note: `hermes -z ... -m deepseek-v4-pro` CLI direct invocation is NOT blocked by Hermes.
Only automatic selection paths are constrained. Scripts/commands that explicitly
invoke pro are the user's responsibility.
```

### 2d. Update MiniMax row in "모델별 가이드"
Replace "MiniMax-M2.7" row default with `MiniMax-M2.5`.

# Pending Patch: model-switcher/SKILL.md (2026-08-18)

Apply these changes in a main-session agent context (review-session blocks skill edits).

## Changes

### 1. "모델 전환 (메인 ↔ 보조)" section — Replace Option 1:
```bash
# 1) MiniMax-M2.5 (cheapest) to main, DeepSeek flash as fallback
hermes config set model.provider minimax
hermes config set model.default MiniMax-M2.5
hermes config set model.base_url https://api.minimax.io/v1
hermes config set fallback_providers '["deepseek"]'
```

### 2. Replace Option 2:
```bash
# 2) DeepSeek flash to main, MiniMax-M2.5 as fallback
hermes config set model.provider deepseek
hermes config set model.default deepseek-v4-flash
hermes config set model.base_url https://api.deepseek.com/v1
hermes config set fallback_providers '["minimax"]'
```

### 3. "모델별 가이드" table — DeepSeek row:
```
| DeepSeek V4 Flash | deepseek | https://api.deepseek.com/v1 | deepseek-v4-flash only |
```

### 4. MiniMax row default: change `MiniMax-M2.7` → `MiniMax-M2.5`

### 5. Replace entire "🚫 deepseek-v4-pro 사용 금지" section:
```markdown
## 🚫 deepseek-v4-pro 사용 금지 (2026-08-18 정책)

**aiprofit 정책: deepseek-v4-pro는 절대 사용 금지. deepseek는 flash만 허용.**

Current enforced state (2026-08-18):
- `providers.deepseek.model`: deepseek-v4-flash ✅
- `providers.deepseek.available_models_json`: deepseek-v4-flash only ✅
- `fallback_providers`: `[]` (deepseek fallback removed) ✅ — updated 2026-08-18
- Default model: MiniMax-M2.5 (cheapest MiniMax) ✅ — updated 2026-08-18

Note: `hermes -z ... -m deepseek-v4-pro` CLI direct invocation is NOT blocked.
Only automatic selection paths are constrained.
```

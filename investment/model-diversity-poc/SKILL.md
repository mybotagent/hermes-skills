---
name: model-diversity-poc
description: "Model Diversity PoC — Multi-provider model calling to unlock Provider Polyglot, Five-Model Flight, and Multi-Model Mage achievements. Use this when experimenting with different LLM providers/models."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
prerequisites:
  env_vars: [OPENROUTER_API_KEY, ANTHROPIC_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY]
  commands: [curl, python3]
metadata:
  hermes:
    tags: [model-diversity, provider-polyglot, five-model-flight, multi-model-mage, achievements]
---

# Model Diversity PoC (Multi-Provider)

**Purpose:** Call models from different providers in one session to unlock achievement badges:
- **Provider Polyglot** (1/2 → 2/2): Use 2 different providers
- **Five-Model Flight** (1/5 → 5/5): Use 5 different models
- **Multi-Model Mage** (1/10 → 10/10): Use 10 different models (long-term)

## Quick Start — Provider Configuration

### 1. Add OpenRouter provider (all-in-one gateway)

```bash
hermes config set providers.openrouter.api_key "$OPENROUTER_API_KEY"
hermes config set providers.openrouter.base_url "https://openrouter.ai/api/v1"
hermes config set providers.openrouter.model "openai/gpt-4o"
hermes config set providers.openrouter.api_mode "chat_completions"
```

### 2. Or add individual providers

```yaml
# config.yaml
providers:
  deepseek:
    api_key: sk-...
    base_url: https://api.deepseek.com/v1
    model: deepseek-v4-flash
    api_mode: chat_completions
  openrouter:
    api_key: sk-or-...
    base_url: https://openrouter.ai/api/v1
    model: openai/gpt-4o
    api_mode: chat_completions
  anthropic:
    api_key: sk-ant-...
    base_url: https://api.anthropic.com/v1
    model: claude-sonnet-4-20250514
    api_mode: messages
  openai:
    api_key: sk-proj-...
    base_url: https://api.openai.com/v1
    model: gpt-4o
    api_mode: chat_completions
  gemini:
    api_key: AIza...
    base_url: https://generativelanguage.googleapis.com/v1beta/openai
    model: gemini-2.0-flash
    api_mode: chat_completions
```

### 3. Testing a provider (without full config)

Quick test via curl:

```bash
# Test OpenRouter
curl -s https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"openai/gpt-4o","messages":[{"role":"user","content":"Say hello in one word."}]}'
```

## Session Switching (Hermes Agent)

To switch providers mid-session, use the `hermes session` command:

```bash
# Start new session with different provider
hermes new --provider openrouter --model openai/gpt-4o
```

Or use `cronjob` with model override:

```bash
hermes cron create --prompt "Quick test" --model-provider openrouter --model openai/gpt-4o --repeat 1
```

## Achievement Targets

| Achievement | Threshold | Current | Target | Action |
|---|---|---|---|---|
| Provider Polyglot | 2 providers | 1 | 2 | Add 1 new provider + call 1 model |
| Five-Model Flight | 5 models | 1 | 5 | Call 4 more different models |
| Multi-Model Mage | 10 models | 1 | 10 | Call 9 more (long-term) |

## Status Commands

```bash
# Check current achievements
hermes achievements

# View achievements dashboard (UI)
# Open http://localhost:9119/achievements

# Get session insights
hermes insights --days 30
```

## Pitfalls

- API keys may have rate limits — stagger calls by 1-2 seconds
- OpenRouter requires `OPENROUTER_API_KEY` env var or key in config
- Some providers (Anthropic) use `messages` API mode, not `chat_completions`
- `fallback_providers: []` in config must be populated for auto-fallback to work
- Model diversity is tracked per-session; cron jobs with different providers also count
- For Multi-Model Mage (10 models), combine OpenRouter (30+ models) + direct providers
- DO NOT hardcode API keys in config — use `$ENV_VAR` references or `.env`

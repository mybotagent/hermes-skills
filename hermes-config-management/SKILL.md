---
name: hermes-config-management
description: Manage Hermes Agent config — provider switches, API keys, model/base_url changes. Use when editing ~/.hermes/config.yaml, switching default provider, troubleshooting auth, or when patch/write_file fails on the config file.
category: devops
---

# Hermes Config Management

## When to use
- Switching default LLM provider / model
- Editing API keys or base_url
- Troubleshooting "uses default X key" / auth failures
- Any edit to `~/.hermes/config.yaml`

## ⚠ Critical pitfall: patch / write_file is BLOCKED
Direct file edits to `~/.hermes/config.yaml` fail with:

> Refusing to write to Hermes config file. Edit ~/.hermes/config.yaml directly or use 'hermes config' instead.

**Use `hermes config set` CLI.** Never `patch` / `write_file` / `sed -i` from inside the agent.

## Workflow (single formula)

### 1. Read state
```bash
sed -n '1,30p' ~/.hermes/config.yaml    # model + providers block
hermes config show                       # formatted summary
```

### 2. Locate keys — 3 possible locations, runtime precedence

| Priority | Location | Loaded by |
|---|---|---|
| 1 | `~/.hermes/auth.json` → `credential_pool.<provider>` | Hermes runtime-injected |
| 2 | `~/.hermes/.env` → `<PROVIDER>_API_KEY=...` | Hermes setup wizard |
| 3 | `~/.hermes/config.yaml` → `providers.<provider>.api_key` | literal fallback |

```bash
# Quick survey of all 3 locations
grep -A8 "\"deepseek\"\|\"minimax\"\|\"openai\"" ~/.hermes/auth.json
grep -E "DEEPSEEK_API_KEY|MINIMAX_API_KEY|OPENAI_API_KEY" ~/.hermes/.env
grep -E "api_key" ~/.hermes/config.yaml
```

### 3. Switch default provider
```bash
hermes config set model.provider <name>      # e.g. deepseek
hermes config set model.default  <model-id>  # e.g. deepseek-v4-flash
hermes config set model.base_url <url>       # e.g. https://api.deepseek.com/v1
# Leave model.api_key '' → uses credential_pool (priority 1)
```

### 4. Verify — mandatory smoke test
```bash
hermes -z "respond with exactly one word: ok" -m <model-id>
# Expect: "ok"
```
If empty / error → re-check step 2 (key source) before retrying.

## Default-key trap
Some providers (e.g., MiniMax) have **empty** `api_key` yet still authenticate, because Hermes ships a built-in default-key injection for them. Empty key ≠ broken. To force **your** key explicitly:
1. Set `model.provider` to the provider you control.
2. Confirm `auth.json` `credential_pool.<provider>` carries **your** key (not just config.yaml's literal).
3. Run smoke test.

## Pitfalls
- ❌ `patch` / `write_file` on `~/.hermes/config.yaml` → BLOCKED, no workaround from inside agent
- ❌ Editing `.env` while loaded → may not propagate; restart gateway or re-run `hermes setup`
- ❌ Editing `auth.json` directly → credential pool has its own locking; use `hermes auth` CLI
- ✅ `hermes config set <key.path> <value>` is the **only** in-agent path
- ✅ `hermes -z "test" -m model` is the canonical smoke test
- `hermes model` (interactive picker) needs TTY → useless from subagent / pipe
- `fallback_providers` accepts bare provider-name **strings**, not objects
- `env | grep PROVIDER_KEY` ≠ runtime truth — `auth.json` is injected, not exported to shell

## Backup before major edits
```bash
cp ~/.hermes/config.yaml ~/.hermes/config.yaml.bak.$(date +%Y%m%d-%H%M%S)
# After verified success: rm ~/.hermes/config.yaml.bak.*
```
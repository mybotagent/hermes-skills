# Manual Provider Setup (for unsupported providers)

When `hermes model` interactive picker doesn't list your provider, add it manually by editing `~/.hermes/config.yaml` + `~/.hermes/.env`.

## Workflow

### 1. Set API key in .env

```bash
# Uncomment or add the relevant key
sed -i 's|# MINIMAX_API_KEY=.*|MINIMAX_API_KEY=sk-your-key|' ~/.hermes/.env
```

Common provider env var names (from hermes-agent SKILL.md):
| Provider | Env var |
|----------|---------|
| MiniMax | `MINIMAX_API_KEY` |
| MiniMax CN | `MINIMAX_CN_API_KEY` |
| Kimi/Moonshot | `KIMI_API_KEY` |
| Alibaba/DashScope | `DASHSCOPE_API_KEY` |
| Xiaomi MiMo | `XIAOMI_API_KEY` |
| Z.AI/GLM | `GLM_API_KEY` |

### 2. Discover available models

Query the provider's model list endpoint directly to verify the key works and see available model IDs:

```bash
curl -s "https://api.minimax.io/v1/models" \
  -H "Authorization: Bearer $(grep MINIMAX_API_KEY ~/.hermes/.env | cut -d= -f2)"
```

### 3. Update config.yaml model section

Change the top-level `model:` block:

```yaml
model:
  api_key: ''            # leave empty — key in .env
  api_mode: chat_completions
  base_url: https://api.minimax.io/v1
  default: MiniMax-M3    # exact model ID from step 2
  provider: minimax
```

### 4. Add provider section

Add a `providers.<name>` block alongside existing providers:

```yaml
providers:
  # ... existing providers ...
  minimax:
    api_key: ''
    api_mode: chat_completions
    available_models_json: '[{"id":"MiniMax-M3","name":"MiniMax-M3"},{"id":"MiniMax-M2.7","name":"MiniMax-M2.7"}]'
    base_url: https://api.minimax.io/v1
    model: MiniMax-M3
    model_display_name: MiniMax M3
    protocol: ''
```

Key fields:
- **api_key**: always `''` (uses .env key at runtime)
- **available_models_json**: JSON list of `{id, name}` for UI display. List only models you'll use — no need to enumerate all.
- **base_url**: OpenAI-compatible chat completions endpoint
- **model**: default model ID for this provider
- **protocol**: always `''` for chat_completions API mode

### 5. Verify

```bash
hermes config | grep -A5 "Model"
```

Expected output shows the new provider, model, and base URL.

## Notes

- The change applies to **next session** (`/reset` in CLI, or start a new `hermes` process). Current session still runs the old provider.
- The interactive `hermes model` command may not list manually-added providers — the picker has its own hardcoded provider list. The config edits above bypass that.
- Keep the old provider section intact (as a fallback). Don't delete it unless you're sure you no longer need it.

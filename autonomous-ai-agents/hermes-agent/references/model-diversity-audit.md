# Model & Provider Diversity Audit

Procedure for assessing model diversity across configured providers,
finding achievable Provider Polyglot / Five-Model Flight / Multi-Model Mage
achievements, and identifying unlock conditions.

## Triggers

- User asks "what other models can I use" or "check model diversity"
- Achievements scan shows Provider Polyglot (1/2), Five-Model Flight (1/5),
  or Multi-Model Mage (1/10) at low progress
- Need to confirm available models before switching provider
- Investigating why a `hermes -m model --provider P` command fails

## Step 1: Baseline Insights

```bash
hermes insights --days 30
```

Key output fields:
- **Models Used** section → count of distinct models (ideally > 1)
- **Platforms** → which channels the agent operates on

## Step 2: Discover Available Providers

Two sources — complement each other:

### Source A: Config.yaml

```bash
cat ~/.hermes/config.yaml | grep -A 10 'model:' | head -20
hermes config set model.provider <name>   # via hermes CLI
```

Check which provider is active and what's configured under `credential_pools` or `auth` sections.

### Source B: Plugin Provider Directory

Hermes ships providers as plugins. List them:

```bash
ls ~/.hermes/hermes-agent/plugins/model-providers/
```

This shows all registered providers regardless of API key availability. Providers found here include:
deepseek, anthropic, openrouter, gemini, openai-codex, copilot, nous, xai, huggingface,
kimi, minimax, alibaba, qwen-oauth, stepfun, kilocode, and 15+ more.

### Source C: Credential Pools

```bash
hermes auth list
```

Shows only providers with stored credentials. Empty = no keys configured.

## Step 3: Test Available Models

For each provider with credentials, probe available models:

```bash
# DeepSeek (has working API key)
hermes chat -q "hello in 3 words" -m deepseek-v4-flash --provider deepseek
hermes chat -q "hello in 3 words" -m deepseek-v4-pro --provider deepseek
hermes chat -q "hello in 3 words" -m deepseek-chat --provider deepseek     # V3
hermes chat -q "hello in 3 words" -m deepseek-reasoner --provider deepseek # R1

# If another provider has a key:
hermes chat -q "hello in 3 words" -m <model_name> --provider <provider>
```

**Known working DeepSeek models** (only `deepseek-v4-flash` appears in `/v1/models` but more respond):

| Model name | Alias | Works? |
|------------|-------|--------|
| `deepseek-v4-flash` | Default | ✅ |
| `deepseek-v4-pro` | — | ✅ |
| `deepseek-chat` | V3 | ✅ |
| `deepseek-reasoner` | R1 | ✅ |

## Step 4: Map to Achievement Thresholds

| Achievement | Threshold | Current gap signal |
|-------------|-----------|-------------------|
| Provider Polyglot | 2+ providers | Insights shows only 1 provider |
| Five-Model Flight | 5+ models | Insights shows only 1 model |
| Multi-Model Mage | 10+ models | Same as above |

## Step 5: Unlock Paths

When only DeepSeek has API keys, the path to diversification:

1. **OpenRouter** (recommended, ~100 models, 1 key)
   ```bash
   # Add to ~/.hermes/.env
   OPENROUTER_API_KEY=sk-or-...
   # Then use:
   hermes chat -q "..." -m openrouter/anthropic/claude-sonnet-4 --provider openrouter
   ```

2. **Google Gemini** (free tier quota, no credit card needed)
   ```bash
   # Add to ~/.hermes/.env
   GOOGLE_API_KEY=AIza...
   GEMINI_API_KEY=AIza...  # sometimes needed separately
   ```

3. **Nous Portal** (OAuth flow)
   ```bash
   hermes login --provider nous
   ```

4. **GitHub Copilot** (requires Copilot subscription, PAT is NOT sufficient)
   ```bash
   # Does NOT work with GITHUB_TOKEN (PAT)
   # Must use hermes model → GitHub Copilot for OAuth device code flow
   ```

## Step 6: Verify After Adding Keys

```bash
# Test each newly configured provider
hermes chat -q "hello" -m <model> --provider <provider>

# Re-run insights to confirm diversity increase
hermes insights --days 1
```

## Non-Provider Diversity (Same Provider, Multiple Models)

Even within a single provider, using different model variants counts toward
Five-Model Flight and Multi-Model Mage. DeepSeek alone can reach 4/5 on
Five-Model Flight with flash + pro + chat + reasoner.

## Pitfalls

- **GitHub PAT ≠ Copilot key.** `GITHUB_TOKEN` works for Git operations
  but GitHub Models API requires a Copilot subscription token.
  Use `hermes model` → GitHub Copilot for the OAuth device-code flow.
- **`hermes -z` needs `-m` + `--provider` together.** Omitting provider
  uses the default. Both must be specified to test a cross-provider model.
- **Provider list from plugin directory ≠ available models.**
  A registered provider plugin needs both credentials and the model name
  to be correct. Test with `hermes chat -q "ping"` first.
- **`.env` reload requires new session.** `export HERMES_*` in-session
  does not propagate to the running agent. Use `/reset` or relaunch.

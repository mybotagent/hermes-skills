# MiniMax Anthropic-Compatible API

The MiniMax M3 model is accessed through an Anthropic-API-shaped HTTPS
endpoint. The provider exposes the protocol at two URL prefixes; pick
ONE consistently and normalize in code.

## Endpoints

| Purpose | URL prefix | Append | Method | Headers |
|---|---|---|---|---|
| Messages | `https://api.minimax.io/anthropic` | `/v1/messages` | POST | `x-api-key`, `anthropic-version: 2023-06-01`, `content-type: application/json` |
| Messages (alt) | `https://api.minimax.io/v1` | `/messages` | POST | same |

Both work; the first is what we store as the `MINIMAX_BASE_URL` secret.

## Auth header

```
x-api-key: $MINIMAX_API_KEY
anthropic-version: 2023-06-01
```

Do NOT use `Authorization: Bearer …` — Anthropic-compatible providers
expect `x-api-key`. Using Bearer usually returns 401.

## Request body

```json
{
  "model": "MiniMax-M3",
  "max_tokens": 3500,
  "temperature": 0.2,
  "messages": [{"role": "user", "content": "<prompt>"}]
}
```

> **Note on model name**: the API call uses bare `MiniMax-M3`. Some
> Anthropic env vars pass the model as `MiniMax-M3[1m]` (with the
> `[1m]` suffix). The `[1m]` is a 1M-context marker that env-driven
> Claude variants (e.g. `ANTHROPIC_MODEL`) understand, but the API
> itself expects the bare name. Pick whichever the runtime expects.

## Response body

```json
{
  "id": "069af8af81cd77c045be0a136c4df49b",
  "type": "message",
  "role": "assistant",
  "model": "MiniMax-M3",
  "content": [{"type": "text", "text": "..."}],
  "usage": {"input_tokens": 42, "output_tokens": 3, ...},
  "stop_reason": "end_turn"
}
```

Extract text via `body["content"][0]["text"]`. The provider adds a
`base_resp` field you can ignore.

## Normalization helper (Python)

```python
def messages_url(base: str) -> str:
    base = base.rstrip("/")
    if base.endswith("/v1"):
        return base + "/messages"
    return base + "/v1/messages"
```

`scripts/review_pr.py` uses this — handle both prefixes so the
secret can hold either form without breakage.

## Common failure modes

| Status | Cause |
|---|---|
| 401 Unauthorized | Wrong header (`Bearer` instead of `x-api-key`), or wrong key |
| 404 Not Found | BASE_URL doesn't end in `/anthropic` or `/v1`, OR wrong path (`/v1/messages` on `/v1`, or `/messages` on `/anthropic`) |
| 422 Validation | Usually empty prompt, oversized messages, or wrong model name |

## Rate / cost

The provider rate-limits per `x-api-key`. A single PR review with a
~50 KB diff typically uses:

- input_tokens: ~1500–2500
- output_tokens: ~800–1500
- cache_read_input_tokens: ~128 (cache hits are billed cheap)

A typical "happy path" review is sub-cent. 🔴/🟠 findings expand the
output but the limit (`max_tokens=3500`) caps them.

## Cache hints

The provider automatically caches 128-token prefixes. For batch review
work, keep the system prompt (verdict rubric + severity table)
prefix-stable across calls to maximize cache hits.

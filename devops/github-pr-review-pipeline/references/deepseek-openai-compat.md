# DeepSeek V4 Flash — OpenAI-compatible API Reference

## Endpoint

```
POST https://api.deepseek.com/v1/chat/completions
```

## Authentication

```
Authorization: Bearer <DEEPSEEK_API_KEY>
Content-Type: application/json
```

## Model

| Model | Context | Max Output | Type |
|-------|---------|-----------|------|
| `deepseek-v4-flash` | 1M tokens | 384K tokens | Cheapest (default for review bot) |
| `deepseek-v4-pro` | 1M tokens | 384K tokens | Premium tier |

## Pricing (per 1M tokens)

| Scenario | deepseek-v4-flash | deepseek-v4-pro |
|----------|:-----------------:|:---------------:|
| Input (cache hit) | **$0.0028** | $0.003625 |
| Input (cache miss) | **$0.14** | $0.435 |
| Output | **$0.28** | $0.87 |

## Request Body (OpenAI format)

```json
{
  "model": "deepseek-v4-flash",
  "max_tokens": 3500,
  "temperature": 0.2,
  "messages": [
    {
      "role": "user",
      "content": "Your prompt here..."
    }
  ]
}
```

## Response Body (OpenAI format)

```json
{
  "id": "chatcmpl-xxx",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "**Verdict:** Approve\n\n..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 1234,
    "completion_tokens": 567,
    "total_tokens": 1801
  }
}
```

## Key differences from MiniMax Anthropic-compat

| Aspect | MiniMax M3 (old) | DeepSeek V4 Flash (new) |
|--------|:----------------:|:-----------------------:|
| API format | Anthropic-compat | OpenAI-compat |
| Endpoint | /v1/messages | /v1/chat/completions |
| Auth header | x-api-key | Authorization: Bearer |
| Model name | MiniMax-M3 | deepseek-v4-flash |
| Response format | content[].text | choices[].message.content |
| Cache hit price | ~$0.05 (est.) | $0.0028 |

## Usage in GitHub Actions workflow

```yaml
- name: Run review script
  env:
    GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    DEEPSEEK_API_KEY: ${{ secrets.DEEPSEEK_API_KEY }}
    DEEPSEEK_BASE_URL: ${{ secrets.DEEPSEEK_BASE_URL }}
    PR_NUMBER: ${{ steps.pr.outputs.number }}
    REPO: ${{ github.repository }}
  run: python3 scripts/review_pr.py
```

## Migration checklist (MiniMax → DeepSeek)

1. [ ] Rename secrets: `MINIMAX_API_KEY` → `DEEPSEEK_API_KEY`, `MINIMAX_BASE_URL` → `DEEPSEEK_BASE_URL`
2. [ ] Update `review-bot.yml` and `review-bot-reusable.yml` env vars
3. [ ] Replace `scripts/review_pr.py` with DeepSeek version
4. [ ] Change model from `MiniMax-M3` to `deepseek-v4-flash`
5. [ ] Change API header from `x-api-key` + `anthropic-version` to `Authorization: Bearer`
6. [ ] Change endpoint from `/v1/messages` to `/v1/chat/completions`
7. [ ] Validate: create test PR → check verdict comment appears

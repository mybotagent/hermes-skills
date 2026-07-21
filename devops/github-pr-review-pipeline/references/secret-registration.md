# GitHub Repository Secret Registration

Use the GitHub Actions Secrets API to set `DEEPSEEK_API_KEY` and
`DEEPSEEK_BASE_URL` programmatically. Both values must be encrypted
with the repository's public key (sealed box / NaCl crypto_box_seal).

## Python (uses pynacl — already in `hermes-agent` venv)

```python
import os, json, urllib.request, base64
from nacl.public import PublicKey, SealedBox

TOKEN = os.environ["GITHUB_TOKEN"]            # classic PAT or fine-grained
                                              # with Secrets: R&W
REPO  = "owner/repo"

# 1. Fetch public key
req = urllib.request.Request(
    f"https://api.github.com/repos/{REPO}/actions/secrets/public-key",
    headers={"Authorization": f"Bearer {TOKEN}",
             "Accept": "application/vnd.github+json",
             "User-Agent": "hermes-bot/1.0"},
)
with urllib.request.urlopen(req, timeout=15) as r:
    pk = json.loads(r.read())

# 2. Encrypt + PUT for each secret
def put_secret(name, value):
    pk_obj    = PublicKey(base64.b64decode(pk["key"]))
    encrypted = SealedBox(pk_obj).encrypt(value.encode("utf-8"))
    payload = {
        "encrypted_value": base64.b64encode(encrypted).decode(),
        "key_id":          pk["key_id"],
    }
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/actions/secrets/{name}",
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {TOKEN}",
                 "Accept": "application/vnd.github+json",
                 "Content-Type": "application/json",
                 "User-Agent": "hermes-bot/1.0"},
        method="PUT",
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.status

for name, value in [
    ("DEEPSEEK_API_KEY", os.environ["DEEPSEEK_API_KEY"]),
    ("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
]:
    print(name, put_secret(name, value))
```

Expected output: `204` for each PUT. Status `403` means the token
lacks Secrets: R&W scope — classic PATs (`repo` scope) automatically
have it; fine-grained PATs need it checked explicitly in the GitHub
PAT settings UI.

## Bash (using `gh secret set`)

If `gh` is authenticated with a token that has Secrets: R&W:

### First-time setup (new repo)
```bash
gh secret set DEEPSEEK_API_KEY --repo owner/repo \
  --body "$DEEPSEEK_API_KEY"

gh secret set DEEPSEEK_BASE_URL --repo owner/repo \
  --body "https://api.deepseek.com/v1"
```

### Migration from MiniMax (old secrets exist)
After code migration (MiniMax M3 → DeepSeek V4 Flash), the repo
may still have `MINIMAX_API_KEY` / `MINIMAX_BASE_URL` but NOT
`DEEPSEEK_API_KEY` / `DEEPSEEK_BASE_URL`. The workflow references
`secrets.DEEPSEEK_*` so it silently breaks (no error until run).

📛 **실제 사례 (2026-07-20)**: MiniMax→DeepSeek migration 후 secrets
미등록으로 review-bot이 3일간 Broken 상태. 다음으로 복구:

```bash
source ~/.hermes/.env 2>/dev/null
echo "$DEEPSEEK_API_KEY" | gh secret set DEEPSEEK_API_KEY --repo mybotagent/hermes-pr-gate
echo "${DEEPSEEK_BASE_URL:-https://api.deepseek.com/v1}" | gh secret set DEEPSEEK_BASE_URL --repo mybotagent/hermes-pr-gate
```

**반드시 검증**: `gh secret list --repo owner/repo` 로 DEEPSEEK_* 가
보이는지 확인. MINIMAX_* 잔여는 무해하나 정리하면 좋음.

## Required token scopes

| Token | Scopes needed |
|---|---|
| Classic PAT | `repo` (full) is sufficient — no separate "secrets" scope |
| Fine-grained PAT | Repository access + **Secrets: Read and write** checked |

The two-token pattern we use (classic + fine-grained) means:
- `GITHUB_TOKEN` (classic, `repo` scope): can register secrets ✅
- `GH_TOKEN_V2` (fine-grained, `workflow` scope): **cannot register secrets**
  (no R&W on Secrets resource) — 403 returned.

So always use the classic token (`GITHUB_TOKEN`) for secret registration.

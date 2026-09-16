# LLM Root Cause Analysis — Internal Reference

## 16. MiniMax Thinking Block JSON Parsing (2026-09-09 fix)

**Root cause**: MiniMax prepends `<think>...</think>` to responses. A greedy `re.search(r'\{[\s\S]*\}', text)` captures from the first `{` in the thinking block through the last `}` — producing invalid JSON.

**Working Fix — first `{` + last `}` brace extraction:**
```python
think_end = text.find('</think>')
if think_end >= 0:
    text = text[think_end + len('</think>'):].strip()

first_brace = text.find('{')
last_brace = text.rfind('}')
if first_brace < 0 or last_brace < 0 or last_brace <= first_brace:
    raise ValueError('JSON 추출 실패 — 첫 번째 { 를 찾을 수 없음: ' + text[:100])

json_text = text[first_brace:last_brace + 1]
parsed = json.loads(json_text)  # raises json.JSONDecodeError on failure
parsed.setdefault('auto_fixable', False)
parsed.setdefault('confidence', 'low')
parsed.setdefault('root_cause', text[:200])
```

**`max_tokens=600` minimum** — prevents the thinking block from being cut off mid-block (which would leave no `</think>` marker).

**Diagnostic flow**: watchdog outputs "JSON 추출 실패" → (1) verify `.env` key load → (2) direct curl test with same prompt via direct curl → (3) apply thinking block parsing fix.

## 17. Discord Webhook Failure ≠ LLM Failure (2026-09-09)

**Key distinction**:
- `discord=❌` + `원인: LLM 호출 실패: ...` → LLM itself failed
- `discord=❌` + `원인: ...` (LLM analysis result) → **webhook URL not set in `.env`**, LLM analysis succeeded

**Verification**:
```bash
python3 -c "
from pathlib import Path
HERMES_HOME = Path('~/.hermes')
def _env_lookup(key):
    for env_path in (HERMES_HOME / '.env', Path('~/.env')):
        if not env_path.exists(): continue
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'): continue
                if line.startswith(f'{key}='):
                    val = line.split('=',1)[1].strip().strip('\"').strip(\"'\")
                    if val: return val
    return ''
WEBHOOK = _env_lookup('DISCORD_WEBHOOK_ROOT_CAUSE')
print('DISCORD_WEBHOOK_ROOT_CAUSE:', 'SET' if WEBHOOK else 'EMPTY/MISSING')
"
```

## 18. Intermittent 402 in Cron vs Direct Curl (2026-09-16)

**Pattern**: Direct curl to MiniMax API returns HTTP 200, but watchdog's LLM analysis returns HTTP 402 **only in cron environment**.

**This means**: NOT a billing issue — cron environment has a network/proxy/timeout problem.

**Diagnostic steps**:
1. Watchdog reports 402 → immediately test the same MiniMax endpoint with same prompt via direct curl
2. If curl returns 200 → cron environment issue (reset cache/retry, let next cycle handle naturally)
3. If curl also returns 402 → actual MiniMax account billing problem

**Actual case**: `a79d072b2447`, `7cf332efe9e4` both showed 402 in watchdog output; direct curl with identical prompt returned 200.

**Manual cache reset** (when watchdog falsely diagnoses and caches the bad result):
```python
# Reset .heal_root_cause.json (LLM analysis cache)
write_file(path="/home/ubuntu/.hermes/cron/.heal_root_cause.json", content="{}")

# Reset today's retry counters
write_file(path="/home/ubuntu/.hermes/cron/.heal_retries.json",
           content=f'{{"2026-09-16": {{}}}}')
```

**Prevention**: `LLM_CACHE_TTL_HOURS = 1` (short TTL so false cached diagnoses expire quickly).

## 19. Binary-Inspection for File Corruption (2026-09-16)

**Symptom**: Python source appears correct in `read_file` output but contains display corruption artifacts like `olon` appearing inside function calls.

**Detection pattern** — use `repr()` on raw bytes:
```python
with open('/path/to/file.py', 'rb') as f:
    content = f.read()
lines = content.split(b'\n')
for i, line in enumerate(lines[288:295], start=289):
    print(f'{i}: {repr(line)}')
```

**Actual case**: `len('olon')` appeared in `self_healing_watchdog.py` line 293 where `len('</think>` should have been. Binary inspection revealed 4 literal bytes `olon` replacing the closing tag. Display tools rendered it as normal code.

**Fix**: Patch the corrupted line.

## 20. GitHub PAT Cascade — Expired Token Blocks Fallback (2026-09-16)

**Pattern**:
```python
GITHUB_TOKEN = (
    get_env_var("GH_TOKEN_V2")   # expired — returns non-empty string (401 on use)
    or get_env_var("GH_TOKEN")    # VALID — never reached
    or get_env_var("GITHUB_TOKEN")
)
```

Python `or` short-circuits on any truthy value. An expired PAT is still a truthy string — so `GH_TOKEN_V2=github_pat_11BWOAV5A...` means `GH_TOKEN` is never tried.

**Diagnosis**:
```bash
for tok in "GH_TOKEN_V2" "GH_TOKEN" "GITHUB_TOKEN"; do
  val=$(grep "^${tok}=" ~/.hermes/.env | cut -d= -f2 | tr -d '"')
  echo "=== $tok ==="
  curl -s -X GET "https://api.github.com/user" \
    -H "Authorization: Bearer $val" \
    -H "User-Agent: hermes" | python3 -c \
    "import sys,json; d=json.load(sys.stdin); print(d.get('login','?'), d.get('message',''))"
done
```

**Fix**: Comment out the expired token in `.env`. **Must use `# ` (hash + space)** — without the space, `re.match(rf'^{name}=(.*)$', line.strip())` matches `#GH_TOKEN_V2=...` because `.strip()` removes `#`.

**Token validity (2026-09-16)**:
- `GH_TOKEN_V2` (github_pat_11BWOAV5A...): ❌ 401 Bad credentials
- `GH_TOKEN` (ghp_Bj1l...): ✅ 200 OK, login=mybotagent
- `GITHUB_TOKEN` (ghp_IHHQ...): ❌ 401 Bad credentials

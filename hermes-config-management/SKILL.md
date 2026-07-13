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

## 🚨 Config-drift RuntimeError — toggle triggers unpinned cron skip (2026-07-11 신규)

**증상**: 전역 `model.provider` 또는 `model.default`를 토글한 직후, 명시적 pin이 없는 cron job들이 다음 트리거에서 다음 에러로 실패:

```
RuntimeError: Skipped to prevent unintended spend: global inference config drifted
since this job was created (provider 'minimax' -> 'deepseek';
model 'minimax-m3' -> 'deepseek-v4-flash'), and this job is unpinned.
```

**원인**: Hermes가 잡 생성 시점의 provider/model과 런타임 글로벌 설정이 다르면 "비용 사고 방지"로 자동 skip. 토글 자체가 트리거.

**워크어라운드 (사용자 요청 시 즉시 적용)**:
```bash
# 1. 현재 토글된 상태에 맞춰 잡에 명시적 pin
hermes cron update <job_id> --provider <new-provider> --model <new-model>
# 또는 원래 값으로 고정
hermes cron update <job_id> --provider <old-provider> --model <old-model>

# 2. 재실행으로 검증
hermes cron run <job_id> --accept-hooks
```

**근본 해결 (사용자 정책)**:
- **provider/model을 자주 토글하는 잡은 토글 직후 일괄 pin** — `hermes cron list` → `provider`/`model` 필드 비어있는 잡 = unpinned
- **토글 전에 모든 잡의 pin 상태를 점검** + 토글 후에는 워치독이 자동으로 영향 잡을 식별해 알림

## 🔑 영구 키 등록 — `hermes auth add` (2026-07-11 신규)

`hermes config set providers.<p>.api_key ...` 만 박아도 동작은 하지만, **gateway 재시작 후 env 못 읽는 케이스**에서 credential_pool의 `access_token`이 빈 상태로 남을 수 있음 (gateway는 `SetLoginEnvironment=no` + 시작 시점의 env만 snapshot). 영구 안전망은 credential pool 직접 등록.

```bash
# .env에서 키 추출 → credential pool에 manual 등록
KEY=$(grep -E "^<PROVIDER>_API_KEY=" ~/.hermes/.env | cut -d= -f2-)
hermes auth add <provider> --type api_key \
  --label "<PROVIDER>_API_KEY" \
  --api-key "$KEY" \
  --inference-url "https://api.<provider>.com/v1"

# 검증
hermes -z "ok" -m <model-id> --provider <provider>
```

**주의**: `--api-key "$KEY"` 실행 시 화면에 짧게 키 일부가 echo될 수 있음 → 노출 위험. 화면 노출이 문제되면 `--api-key -` + stdin 또는 `--api-key "$(cat ~/.hermes/.env | grep ^PROV= | cut -d= -f2)"` 패턴 사용.

**3중 안전망 (best practice)**:
1. `credential_pool`에 manual 등록 (gateway 재시작에도 살아있음)
2. `config.yaml` `providers.<p>.api_key` literal (코드 변경 시 영구)
3. `.env` `<PROVIDER>_API_KEY` (shell setup 시 export)

셋 중 하나만 살라도 동작. 가장 안정적인 건 `hermes auth add`로 credential pool에 박는 것.

### `hermes auth status` 함정 — "logged out" 표시는 misleading

`hermes auth status <provider>` 가 `logged out`을 보여줘도 credential_pool에 키가 등록돼 있고 실제 호출은 정상 동작할 수 있음. status는 **OAuth 로그인 플로우의 상태**를 보여줄 뿐, api_key credential pool과는 별개 신호.

**판단 기준**:
- `hermes auth status` logged out → 무시 가능 (api_key 등록과 무관)
- `hermes auth list`에서 `<provider>` 섹션의 `api_key manual` 또는 `api_key config:...` 행이 보이면 → 키 등록됨
- 진짜 인증 확인은 `hermes -z "ok" -m <model>` 스모크 테스트가 유일한 판정

## 🔄 토글 workflow — provider/model 전환 시 잡 보호 체크리스트 (2026-07-11 신규)

provider/model 토글 작업 시 다음 순서로 진행:

```bash
# 1. 백업
cp ~/.hermes/config.yaml ~/.hermes/config.yaml.bak.$(date +%Y%m%d-%H%M%S)

# 2. unpinned 잡 목록 확인 (provider/model 필드 비어있는 잡)
hermes cron list | grep -E "provider: |model: " || echo "all pinned"

# 3. 토글
hermes config set model.provider <new>
hermes config set model.default <new-model>
hermes config set model.base_url <new-url>

# 4. unpinned 잡 일괄 pin (새 값으로)
for jid in <jid1> <jid2> ...; do
  hermes cron update "$jid" --provider <new> --model <new-model>
done

# 5. 스모크 테스트
hermes -z "ok" -m <new-model>
```

**핵심 규칙**: 토글 = 워치독이 unpinned 잡을 RuntimeError로 한꺼번에 skip시킬 수 있는 상황. 토글 후 5분 내에 `.heal_history.log`에서 `Skipped to prevent unintended spend` 패턴 모니터링.

## Backup before major edits
```bash
cp ~/.hermes/config.yaml ~/.hermes/config.yaml.bak.$(date +%Y%m%d-%H%M%S)
# After verified success: rm ~/.hermes/config.yaml.bak.*
```
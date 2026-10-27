---
name: model-switcher
description: Hermes 모델 설정 관리. MiniMax 단독(현재 정책) 및 provider 전환, fallback 체인, auxiliary 일괄 설정, cron job 핀 관리.
category: devops
---

# Model Switcher

Hermes 모델(provider/model) 설정 관리. **현재 정책: MiniMax-M2.7 단독** (2026-10-26 aiprofit 확정).

## 🚫 현재 정책 — MiniMax 단독 (2026-10-26)

**DeepSeek는 완전히 제거된 상태.** 잔액 0(HTTP 402) + 보조MODEL 불필요 → MiniMax만 사용.

| 항목 | 값 |
|------|-----|
| Primary | `MiniMax-M2.7` (provider: `minimax`, `https://api.minimax.io/v1`) |
| Fallback chain | **비어있음** (`fallback_providers: []`) |
| providers | `minimax` **하나만** (deepseek 삭제됨) |
| auxiliary 12종 | 전부 `minimax` / `MiniMax-M2.7` |
| delegation | `minimax` / `MiniMax-M2.7` |
| auth credential_pool | `minimax`만 (deepseek/custom:deepseek 삭제) |
| `.env` | `MINIMAX_API_KEY`만 (DEEPSEEK_API_KEY 삭제) |
| cron job pins | 12개 전부 `minimax` / `MiniMax-M2.7` |

**전환 금지**: deepseek를 다시 fallback에 넣지 말 것. 잔액 없음 → 402로 방해만 됨.

## MiniMax 모델 3종

| ID | 용도 |
|----|------|
| `MiniMax-M2.7` | **기본 (무조건 이거)** — aiprofit 정책 |
| `MiniMax-M3` | 신형, 비교 테스트용 |
| `MiniMax-M2.5` | 구형, 비권장 |

## MiniMax 단독으로 고정/검증하기

```bash
# 1) Primary
hermes config set model.provider minimax
hermes config set model.default MiniMax-M2.7
hermes config set model.base_url https://api.minimax.io/v1

# 2) Fallback 체인 비우기 (Python yaml 패치 — config set은 리스트를 문자열로 저장함)
cd ~ && python3 - <<'EOF'
import yaml, pathlib
p = pathlib.Path.home()/'.hermes'/'config.yaml'
cfg = yaml.safe_load(p.read_text())
cfg['fallback_providers'] = []
cfg.pop('fallback_model', None)
cfg['providers'] = {'minimax': cfg['providers']['minimax']}
p.write_text(yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True))
EOF

# 3) auxiliary 12종 일괄
for k in vision web_extract compression skills_hub approval mcp \
         title_generation triage_specifier kanban_decomposer \
         profile_describer curator session_search; do
  hermes config set auxiliary.$k.provider minimax
  hermes config set auxiliary.$k.model MiniMax-M2.7
  hermes config set auxiliary.$k.base_url https://api.minimax.io/v1
done

# 4) delegation
hermes config set delegation.provider minimax
hermes config set delegation.model MiniMax-M2.7
hermes config set delegation.base_url https://api.minimax.io/v1

# 5) 검증
hermes config show | grep -A2 "◆ Model"
hermes fallback list        # "No fallback providers configured" 이 맞음
hermes auth list            # minimax만 남아야 함
hermes -z "ok" -m MiniMax-M2.7 --provider minimax
```

## ⚠️ `hermes config set fallback_providers` 함정

```bash
hermes config set fallback_providers '["deepseek"]'
# → config.yaml: fallback_providers: '["deepseek"]'   ← 문자열! YAML single-quoted
# → hermes fallback list → "No fallback providers configured"  ← 무시됨
```

`set_config_value()`는 bool/int/float만 coerce하고 JSON 파싱이 없다. 리스트는 항상 문자열로 저장됨 → Python yaml 패치가 유일한 방법.

**리스트 항목 4필드 필수**: provider, model, base_url, api_mode.

## auxiliary (보조 모델) 12종 목록

vision, web_extract, compression, skills_hub, approval, mcp, title_generation, triage_specifier, kanban_decomposer, profile_describer, curator, session_search

`provider: auto`면 글로벌 상속하지만, `nous`/`openrouter`가 auth에 남아 있으면 게이트웨이 로그에
`marking X unhealthy (payment / credit error)`가 반복됨 → 전부 명시적으로 minimax 고정.

## 크레덴셜 정리 (provider 제거 시)

```bash
hermes auth list                              # 확인
hermes auth remove <provider> 1               # credential_pool + .env에서 제거됨
# 주의: .env의 DEEPSEEK_API_KEY도 자동 삭제 + re-seed 억제됨
```

## cron job 핀

```bash
# 모든 job의 pin 상태 확인
python3 -c "
import json
d=json.load(open('/home/ubuntu/.hermes/cron/jobs.json'))
jobs = d if isinstance(d,list) else d.get('jobs',d)
if isinstance(jobs,dict): jobs=list(jobs.values())
for j in jobs:
    if j.get('provider') or j.get('model'):
        print(j.get('name'),'|',j.get('provider'),'|',j.get('model'))
"
```

- provider/model 비어있음 = **unpinned** → 글로벌 설정 상속
- 전환 시 unpinned job은 `RuntimeError: Skipped to prevent unintended spend` 발생 가능
- Hermes엔 모델 블록리스트 없음 → `hermes -z ... -m deepseek-v4-pro` 같은 CLI 직접 지정은 차단 안 됨. **정책은 사람이 지킨다.**

## 게이트웨이 재시작

게이트웨이 프로세스 안에서는 재시작 불가 (self-SIGTERM 차단):
```
Blocked: cannot restart or stop the gateway from inside the gateway process.
```
→ 사용자가 외부 셸에서 `hermes gateway restart` 실행. 에이전트는 config만 변경하고 보고.

## 외부 저장소 (GitHub Actions) provider 전환

CI 리뷰 파이프라인의 provider는 GitHub 변수/시크릿으로 제어됨 (config.yaml과 무관):

```bash
export GH_TOKEN=$(grep -E "^GH_TOKEN=" ~/.hermes/.env | cut -d= -f2-)
gh variable set CI_REVIEW_PROVIDER --body minimax -R mybotagent/dev-harness-kit
KEY=$(grep -E "^MINIMAX_API_KEY=" ~/.hermes/.env | cut -d= -f2-)
gh secret set MINIMAX_API_KEY --body "$KEY" -R mybotagent/dev-harness-kit
gh secret remove DEEPSEEK_API_KEY -R mybotagent/dev-harness-kit   # 잔여 제거
```

## 주의사항

- `hermes config set providers.<p>.api_key` → stdout에 키 일부 노출 (CLI 자체 동작)
- 키를 env에서 안전하게 등록: `hermes auth add <provider> --type api_key --api-key -` (stdin, 키 0 노출)
- 토글 직후 `.heal_history.log`에서 `Skipped to prevent unintended spend` 모니터링

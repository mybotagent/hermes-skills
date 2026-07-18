---
name: model-switcher
description: DeepSeek ↔ MiniMax 모델 전환. 메인/보조 설정, cron job 핀 상태 확인/일괄 업데이트 포함.
category: devops
---

# Model Switcher

DeepSeek ↔ MiniMax 간 손쉬운 모델 전환 + cron job 핀 관리.

## 모델 전환 (메인 ↔ 보조)

```bash
# 1) MiniMax-M2.7을 메인으로, DeepSeek를 보조로
hermes config set model.provider minimax
hermes config set model.default MiniMax-M2.7
hermes config set model.base_url https://api.minimax.io/v1
hermes config set fallback_providers '["deepseek"]'

# 2) DeepSeek를 메인으로, MiniMax를 보조로
hermes config set model.provider deepseek
hermes config set model.default deepseek-v4-flash
hermes config set model.base_url https://api.deepseek.com/v1
hermes config set fallback_providers '["minimax"]'
```

## 전환 후 필수 체크

### 스모크 테스트
```bash
hermes -z "ok" -m <model-id> --provider <provider>
```

### cron job 핀 상태 확인
```bash
# 모든 job의 provider/model 핀 상태 출력
hermes cron list | grep -E "^\s*[a-f0-9]{10,}"
```
- provider/model 비어있음 = **unpinned** → 글로벌 설정 상속
- unpinned job은 전환 시 `RuntimeError: Skipped to prevent unintended spend` 발생 가능

### unpinned job 일괄 핀
```bash
# 새 provider/model로 모든 job 핀
JOB_IDS=$(hermes cron list | grep -E "^\s*[a-f0-9]{10,}" | awk '{print $1}')
for jid in $JOB_IDS; do
  hermes cron edit "$jid" --provider <new-provider> --model <new-model> 2>/dev/null || true
done
```

## 모델별 가이드

| 모델 | provider | base_url | available_models |
|------|----------|----------|-----------------|
| MiniMax-M2.7 | minimax | https://api.minimax.io/v1 | MiniMax-M3, MiniMax-M2.7, MiniMax-M2.5 |
| DeepSeek V4 Flash | deepseek | https://api.deepseek.com/v1 | deepseek-v4-flash, deepseek-v4-pro |

## ⚠️ 주의사항

- `hermes config set` → stdout에 키 일부 노출될 수 있음 (CLI 자체 동작)
- `.env`에서 키 관리 시: `hermes auth add`로 credential pool에 등록하면 gateway 재시작에도 유지
- 토글 직후 `.heal_history.log`에서 `Skipped to prevent unintended spend` 패턴 모니터링

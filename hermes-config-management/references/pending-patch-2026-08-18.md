# Pending Patch Log — hermes-config-management + model-switcher

## ✅ Applied (2026-09-07)

### Patch 1: hermes-config-management — Gateway self-restart
**Status**: ✅ APPLIED 2026-09-07

Added new section "🚨 Gateway cannot restart itself from inside (재현 2026-09-07)":
- Full reproduction transcript: `hermes gateway restart` → 60s timeout
- `systemctl --user restart hermes-gateway` from inside gateway → self-SIGTERM
- Workaround: `delegate_task(..., role="leaf")` pattern
- no_agent cron의 `systemctl restart`는 safe (LLM agent 프로세스 아님)

### Patch 2a: model-switcher — default model updated to MiniMax-M2.5
**Status**: ✅ APPLIED 2026-09-07

- 모델 전환 옵션 1: default = MiniMax-M2.5 (was MiniMax-M2.7)
- 모델 테이블: MiniMax-M2.5 row added, MiniMax-M2.7 deprioritized
- DeepSeek flash 모델 수: "deepseek-v4-flash only" (pro removed)

### Patch 2b: model-switcher — pro-ban policy table updated
**Status**: ✅ APPLIED 2026-09-07

- 전역 model.default: MiniMax-M2.5 (2026-08-18 변경 이력 반영)
- cron LLM 잡: 전부 minimax/MiniMax-M2.5 pin
- deepseek-v4-flash fallback_providers 유지

---

## 🔑 Additional finding this session (2026-09-07)

**MiniMax API 스모크 테스트 시 .env source 필수**:
```bash
# ❌ 바로 실행 — MINIMAX_API_KEY가 쉘 환경변수에 없음
curl -X POST ... -H "Authorization: Bearer $MINIMAX_API_KEY"
→ 401 Unauthorized

# ✅ source 후 실행 — .env에서 로드됨
source ~/.hermes/.env && curl -X POST ... -H "Authorization: Bearer $MINIMAX_API_KEY"
→ 200 OK
```
`.env`은 gateway/runtime이 로드하지만, 쉘 세션의 `$MINIMAX_API_KEY`는 비어있음.

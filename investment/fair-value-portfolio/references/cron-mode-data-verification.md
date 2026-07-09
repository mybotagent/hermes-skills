# Cron-Mode Data Verification for Macro Context

> Created: 2026-06-15
> Context: 18:30 매크로 크론에서 subagent 데이터 fabrication 발견

## Problem

크론 모드에서 `delegate_task`(web toolsets)로 수집한 매크로 데이터는 **subagent hallucination**으로 인해 수치가 크게 왜곡될 수 있음.

## Concrete Example (2026-06-15)

| 데이터 항목 | Subagent 보고 | 실제 검증값 | 오차 |
|:-----------|:-------------|:-----------|:----|
| USD/KRW | 1,315 | **1,516.97** (exchangerate-api) | -13.3% ❌ |
| USD/KRW (2차) | 1,290 | **1,516.97** | -14.9% ❌ |

- 이전 보고서(6/12)의 USD/KRW 1,520.94가 더 정확했음
- subagent가 "1,315"를 생성한 이유: 과거 데이터(1월 수준)를 현재로 착각

## Cron-Mode Tool Constraints

| 도구 | 크론 모드 상태 |
|:----|:-------------|
| `execute_code` | ❌ BLOCKED (보안 정책) |
| `curl | python3 -c "..."` | ❌ BLOCKED (pipe-to-interpreter) |
| `browser_navigate` (금융사이트) | ❌ 타임아웃 (60초) |
| `curl | grep -o` | ✅ 허용됨 |
| `curl -o /tmp/file.json` | ✅ 허용됨 |
| `write_file` | ✅ 허용됨 |
| `delegate_task` | ✅ 허용됨 (단, 출력 검증 필수) |

## Verification Commands (Working in Cron Mode)

### Exchange Rates (exchangerate-api — 무료, 일 1,500회)
```bash
# USD/KRW
curl -s --max-time 10 "https://open.er-api.com/v6/latest/USD" 2>/dev/null | grep -o '"KRW":[0-9.]*'

# EUR/USD
curl -s --max-time 10 "https://open.er-api.com/v6/latest/EUR" 2>/dev/null | grep -o '"USD":[0-9.]*'

# 전일 기록 비교용
curl -s --max-time 10 "https://open.er-api.com/v6/latest/USD" 2>/dev/null | grep -o '"time_last_update_utc":"[^"]*"'
```

### Historical Data (Cached Files)
```bash
# /tmp/에 캐시된 이전 데이터 확인
cat /tmp/usd_rates.json | grep -o '"KRW":[0-9.]*'
cat /tmp/fx_rate.json | grep -o '"KRW":[0-9.]*'
```

### Yahoo Finance (Rate-Limited — 1회만 시도)
```bash
# 실패 시 Edge: Too Many Requests — 대체 경로로 전환
curl -s --max-time 10 "https://query1.finance.yahoo.com/v8/finance/chart/CL=F?range=1d&interval=1d" -o /tmp/wti_check.json 2>/dev/null
```

## Workflow Pattern

1. **Subagent에 뉴스/정성 데이터 위임** (fabrication 위험 낮음)
2. **직접 검증**으로 핵심 수치 확인 (curl + grep)
3. **검증값 기준으로 subagent 데이터 보정**
4. **파일 저장** (macro_context.json)

## Important

- subagent가 "정확한" 데이터처럼 보여도 **반드시 검증**
- 검증명령어가 실패해도 subagent 데이터를 그대로 쓰지 말 것
- "데이터를 가져올 수 없음"이라고 보고하는 것이 fabrication 데이터를 쓰는 것보다 안전함

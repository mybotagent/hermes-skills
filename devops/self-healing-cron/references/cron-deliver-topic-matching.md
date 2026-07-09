# Cron Deliver Topic Matching — Wrong-Thread Routing Diagnosis & Fix

> **2026-07-02 신규** — 404 hardcoded 패턴과 다른 새 버그 클래스. deliver 형식이 올바르지만 topic이 맞지 않는 경우.

## 발생 조건

```
discord:{channel_id}:{thread_id}  ← 포맷 OK, 내용 틀림
```

- channel_id: 홈 채널 (보통 동일)
- thread_id: **cron 콘텐츠와 다른 topic**을 가진 thread
- 결과: cron은 "성공" (메트릭 0/0) 하지만 사용자에겐 미도달
- 404 fix watchdog이 **감지 못함** (404가 아니므로)

## 진단 5단계

```bash
# ① 의심 cron의 deliver 확인
hermes cron list | grep "<job_id>"
# Deliver: discord:1510397804139515945:1520640537995247698

# ② thread-id → 어느 topic인지 식별
#    예: 1520640537995247698 = #일정 (캘린더)
#    (메모리 thread-mapping 또는 wiki thread-mapping 페이지 참조)

# ③ cron 콘텐츠 주제 확인
#    예: "🧠 LangGraph 파이프라인" → portfolio + 분석 결과

# ④ 매칭 확인
#    - 포트폴리오 → #일정 캘린더? ❌ (불일치)
#    - 포트폴리오 → #주식-증시? ✅

# ⑤ 발견 즉시 수정
hermes cron update <job_id> --deliver "discord:1510397804139515945:1510404235915694170"
```

## 메모리 thread-id 매핑 (2026-07-02 기준)

| Thread ID | Topic | 용도 |
|:----------|:------|:----|
| `1520255092413038732` | #체크리스트 | daily-survey (설문) |
| `1520640537995247698` | #일정 | calendar (캘린더) |
| `1510404235915694170` | #주식-증시 | stock/market (포트폴리오 등) |

> 다른 thread는 등록 안 함 (정확한 매핑이 우선).

## 주제별 cron 매핑 예시

| Cron 주제 | 권장 thread | 비고 |
|:----------|:------------|:----|
| Portfolio pipeline (afebf6cb0ab1) | #주식-증시 | 2026-07-02 FIXED |
| Macro strategy (b96583fa9d27) | #일정 | OK |
| 한국 morning briefing | #주식-증시 | |
| Daily survey (7bc8a40b898e) | #체크리스트 | |
| US market briefing | #주식-증시 | |

## 사용자-인지 트리거

사용자가 "추천 포트폴리오와 비중 자체는 안알려 주네?" 같은 **content-not-delivered** 신호를 보내면:

1. cron 자체가 정상 작동 중인지 확인 (`hermes cron list`)
2. last_status='ok', last_delivery_error=None면 → **wrong-thread 의심**
3. deliver thread ↔ cron topic 매칭 검증
4. 불일치 발견 시 즉시 `hermes cron update` + 사용자에게 오늘 분 재전송

## 404 fix watchdog의 사각지대

| 패턴 | watchdog 감지 | 진단 |
|:-----|:-------------|:----|
| `discord:\d+(:\d*)?$` (thread 없음) | ✅ 자동 fix | 404 hardcoded |
| `discord:\d+:\d{17,20}` (포맷 OK, 내용 틀림) | ❌ 못 잡음 | **wrong-thread (사람 진단 필요)** |
| `last_status='ok'` + `last_delivery_error=None` + 콘텐츠 미도달 | ❌ silent failure | **wrong-thread 또는 Discord 권한 이슈** |

## 예방 규칙

cron 등록 시 deliver 검증 3단계:
```bash
# ① deliver thread-id가 그 cron 콘텐츠 주제와 일치하는지 확인
# ② thread-id 매핑은 memory thread-mapping 또는 wiki 참조
# ③ 매칭 확인 후 cron create
```

cron topic 그룹화 권장:
- portfolio/stock → 동일 thread
- macro/calendar → 동일 thread
- survey → 자체 thread
- 같은 topic → 같은 thread 원칙

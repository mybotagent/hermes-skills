# Discord Thread Expiration Auto-Recovery

## 발견 (2026-07-17)
셀프힐링 watchdog이 `f405cd52a6e8` (Memory Usage Alert) 2회 재시도 초과 감지.
RCA: Discord 스레드 `1520640537995247698` 비활성 만료(404).

## 근본 원인
Discord 스레드는 7일 비활성 시 자동 보관(archived) → 메시지 전송 불가.
9개 크론 잡이 스레드 ID로 전송 중이었음.

## 1차 문제: 전송 채널 만료
- **증상**: `last_status: ok`, `last_delivery_error: Discord API error (404)`
- **치유**: deliver를 Home 채널(`discord:1522277759660068954`)로 변경
- **영향받은 잡** (9개, 모두 2026-07-17 마이그레이션 완료):
  - `f405cd52a6e8` Memory Usage Alert
  - `2f553ea20e27` 매일 아침 일정 요약
  - `df1faab3310b` 일요일 아침 주간 브리핑
  - `fffbc0dce0c7` 일요일 저녁 주간 브리핑
  - `2916cc9c2ceb` 미국 증시 브리핑
  - `b96583fa9d27` 매크로 전략 리포트
  - `afebf6cb0ab1` LangGraph 파이프라인
  - `7bc8a40b898e` daily-survey
  - `1d795f36a5a4` survey-morning

## 2차 문제: exit 1로 전송 차단
- **증상**: `memory_alert.py`가 `sys.exit(1)` → `no_agent` cron이 "스크립트 실패"로 처리
- **치유**: `exit 1` → `exit 0`으로 수정
- **원인**: `no_agent` 스크립트는 exit code != 0 시 stdout 전송 차단 (에러로 간주)

## 사용자 교정 (2026-07-17): 활성 스레드로 우선 마이그레이션

**과거 접근**: 만료 스레드 → Home 채널(`discord:1522277759660068954`)로 이동
**사용자 교정 (aiprofit)**: "**계속 같은 스레드에 7일 내에 보내면 살아있음**"

**결론**: Discord 스레드는 7일만 지키면 영구 유지됨. 따라서:
- 404 스레드 발견 시 Home 채널이 아닌 **동일 주제의 활성 스레드**로 마이그레이션
- 활성 스레드에 주 1회 이상 메시지 도착 → 절대 안 죽음
- 최종 적용 (2026-07-17):
  - 5개 잡 → 원래 활성 스레드로 복원
  - 4개 잡(만료 스레드) → 현재 활성 스레드(`1510404235915694170`)로 마이그레이션

## Prevention
- 신규 크론 생성 시 deliver는 **활성 스레드 ID**로 지정할 것 (Home 채널 ❌)
- 활성 스레드에 주 1회 이상 메시지 도착 → 영구 유지
- 경보 스크립트는 `exit 0`으로 정상 종료 (alert 메시지가 stdout에 있음)
- `no_agent` 스크립트: exit 0 = 전송됨, exit 1 = 차단됨

## Self-Healing Rule
wiki/infra/selfheal-discord-thread-expiry.md 참조.
워치독이 스레드 만료 탐지 시 자동으로 Home 채널로 마이그레이션.

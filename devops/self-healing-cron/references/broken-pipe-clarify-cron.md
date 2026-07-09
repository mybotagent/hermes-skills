# Broken Pipe in Cron — Clarify 호출 사례

## 증상
```
RuntimeError: [Errno 32] Broken pipe
```
크론 job이 이 에러로 반복 실패. `cronjob run`으로 재실행해도 동일.

## 원인
크론 job이 `clarify` 툴을 호출했기 때문. clarify는 유저의 실시간 입력이 필요한데, 크론 컨텍스트에는 유저가 없어서 Broken pipe 발생.

## 근본 원인: 스킬 vs 프롬프트 충돌
크론이 스킬을 로드하면, 스킬 내용이 시스템 프롬프트에 포함됨. 
만약 스킬에 `clarify` 호출 지침이 있고, 크론 프롬프트가 "clarify 금지"라고 해도, 
에이전트는 더 상세한 지침(스킬)을 우선 따르는 경향이 있음.

## 해결책 (우선순위 순)

### 1st: 스킬 제거 (최우선)
크론 프롬프트가 **자급자족형(템플릿+로직 내장)**이면, 문제 되는 스킬을 크론 `skills` 배열에서 **완전히 제거**.
에이전트가 인터랙티브 지침을 볼 수 없게 원천 차단됨.

**실제 사례 (2026-06-14):** `survey-morning` 크론에서 `daily-survey` 스킬 제거 후 Broken pipe 해결.
프롬프트에 템플릿+로직이 이미 내장되어 있어 스킬 없이도 정상 작동.

### 2nd: 모드 분리 (스킬 제거 불가능할 때)
스킬을 아래처럼 구조 변경:

```
## ⚡ 모드 구분 (HARD RULE)
| 모드 | 실행자 | clarify 사용? |
|------|--------|:---:|
| 크론 모드 | cron job | 🚫 절대 금지 |
| 인터랙티브 | live session | ✅ 사용 |

## 🕐 크론 모드
할 일: 템플릿 텍스트 출력만
❌ clarify, send_message, read_file, terminal 금지

## 💬 인터랙티브 모드
할 일: 유저 "시작" 응답 시 clarify로 설문 진행
```

### 3rd: 추가 안전장치
1. 크론 프롬프트에 "절대 clarify/read_file/terminal 호출 금지" 명시
2. data-collection script 패턴 사용 (script 파라미터로 데이터 선수집)
3. `self-healing-cron` 스킬을 다른 스킬보다 먼저 로드 (skills 배열 첫 번째)

## 한계
모드 분리를 해도 동일 파일에 두 모드가 공존하면 에이전트가 인터랙티브 지침을 읽고
크론 모드임에도 따라갈 위험이 있음. 가장 확실한 방법은 **스킬 제거**.

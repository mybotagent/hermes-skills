# Cron Delivery Error Recovery — Class-Level Reference

Discord, Slack, webhook, email 등 외부 채널로 배달하는 모든 cron 잡에 적용 가능한 회복 패턴.

## 핵심 원칙

**실행 성공 ≠ 배달 성공.** 사용자에게 도달해야 비로소 "작동한" 것.
자가 치유 watchdog은 "사용자에게 도달했는가"로 판정해야지, "내부 실행이 끝났는가"로 판정하면 안 됨.

## 데이터 모델

```
jobs.json 한 entry의 3가지 신호:
  last_status          : "ok" / "error" / null
  last_run_at          : ISO timestamp 또는 null
  last_delivery_error  : 에러 메시지 문자열 또는 null
```

세 신호는 독립적. 조합표:

| last_status | last_delivery_error | 의미 | 자가 치유 |
|---|---|---|---|
| `ok` | `null` | ✅ 정상 완료 | — |
| `ok` | `"...404..."` | ⚠️ **본문 OK, 배달 실패** | 🔁 retry (404/429/5xx) / 🚫 영구 (401/403) |
| `error` | `null` | ❌ 본문 생성 실패 | 🔁 retry |
| `error` | `"..."` | ❌ 본문 + 배달 모두 실패 | 🔁 retry |
| `null` | `null` | ⏸ never-ran | 🔁 run (last_run_at null) |

**가장 자주 빠지는 케이스**: `ok + delivery_error` 조합. 기존 watchdog의 `if status != 'error'` 조건이 누락.

## HTTP 코드 분류 (Discord 기준, 다른 API도 유사)

수집 가능한 코드 패턴:
```python
codes = ('401', '403', '404', '429', '500', '502', '503', '504')
```

| 코드 | 의미 | 일반화된 처리 |
|---|---|---|
| 401 | Unauthorized | 영구 — 토큰/자격 증명 문제 |
| 403 | Forbidden | 영구 — 권한/스코프 문제 |
| 404 | Not Found | retry 가능 — 리소스 부재/이동 |
| 408 | Request Timeout | retry — 일시적 |
| 429 | Too Many Requests | retry (백오프) — rate limit |
| 5xx | Server Error | retry — 일시적 서버 장애 |
| 네트워크 | Connection refused / DNS / timeout | retry (백오프) — 인프라 일시 |

**분류 로직 (Python)**:
```python
err = last_delivery_error.lower()
# 패턴 1: 숫자만 추출
import re
match = re.search(r'\b(4\d\d|5\d\d)\b', err)
code_match = match.group(1) if match else None

# 패턴 2: 코드별 키워드 매칭 (rate limit 등 명시적 단어)
if not code_match:
    if 'rate limit' in err or 'too many' in err:
        code_match = '429'
    elif 'unauthorized' in err: code_match = '401'
    elif 'forbidden' in err: code_match = '403'
    elif 'not found' in err: code_match = '404'

# 영구 판정
permanent_codes = {'401', '403'}
if code_match in permanent_codes:
    log_permanent_error(jid, code_match, last_delivery_error)
    # 운영자 알림 (Discord/email/webhook)
else:
    # retry (1일 최대 N회)
    trigger_hermes_cron_run(jid)
```

## 재시도 정책

- **하루 최대 2회** per 잡 (리트레이 폭주 방지)
- 두 번째 재시도도 실패 → 영구 에러로 격상, 운영자 알림
- 같은 코드가 연속 3일 → 더 이상 재시도 안 함, 알림만

## 히스토리 로그 설계

```
2026-07-01 00:30:00 KST <job_id> <name> delivery_retry_triggered[<code>]
2026-07-01 00:30:00 KST <job_id> <name> retry_triggered
2026-07-01 00:30:00 KST <job_id> <name> permanent_error[<code>] <snippet>
```

**grep 한방 진단**:
```bash
# 오늘 영구 에러
grep "permanent_error" ~/.hermes/cron/.heal_history.log | grep "$(date +%Y-%m-%d)"

# 오늘 retry 횟수
grep "$(date +%Y-%m-%d)" ~/.hermes/cron/.heal_history.log | wc -l

# 가장 자주 retry되는 잡
awk '{print $3}' ~/.hermes/cron/.heal_history.log | sort | uniq -c | sort -rn | head -10
```

## 운영 액션 매트릭스

| 패턴 | 자동 처리 | 운영자 액션 |
|---|---|---|
| 401 | retry 안 함, 알림 | `DISCORD_BOT_TOKEN` 갱신 후 잡 재활성 |
| 403 | retry 안 함, 알림 | 봇 권한 재설정 / 서버 재초대 |
| 404 | 자동 retry (deliver 정상화 시) | deliver 타겟 확인 (origin 또는 thread) |
| 429 | 자동 retry (백오프) | rate limit 정책 검토 |
| 5xx | 자동 retry | Discord 상태 페이지 확인 |

## 전체 self-healing cron 진단 흐름

```
① jobs.json last_status / last_delivery_error 일괄 조회
   ↓
② last_status == 'ok' && last_delivery_error != null → 이 reference의 분류표 적용
   ↓
③ 영구(401/403) → 운영자 알림 큐
   ↓
④ 일시(404/429/5xx) → 오늘 retry < 2회면 자동 재실행
   ↓
⑤ 히스토리 로그 append-only로 추적
```

## 2026-06-30 인시던트 + 2026-07-01 해결 요약

**인시던트**: 6/30 화 저녁 3건 (미국증시/매크로/LangGraph) Discord 404 동시 발생
- 원인: deliver가 `discord:<channel_id>` (본채널, thread 없음) — 봇이 본채널 접근 불가
- watchdog 미감지: `last_status=='ok'` 라서 사각지대
- 13일 동안 같은 패턴 0건 자동 감지 (운영자만 발견)

**해결**: 
1. 3개 deliver를 `discord:<channel_id>:<thread_id>` 로 변경 (쓰레드는 봇 접근 가능)
2. `self_healing_watchdog.sh` 보강:
   - `last_delivery_error` 체크 추가
   - Discord HTTP 코드별 분류 (영구 vs retry)
   - 히스토리 로그에 코드 포함
3. Private repo `mybotagent/hermes-self-healing` 에 풀 코드 + 인시던트 문서 푸시

**교훈 (다음번에 같은 사고 방지)**:
- 자가 치유 로직 작성 시 "본문 성공 ≠ 배달 성공"을 항상 의식
- 외부 시스템 deliver 시 deliver 타겟을 명시적으로 검증 (origin 또는 thread 포함)
- watchdog 보강 후 dry-run으로 모든 케이스 (정상/404/401) 분류 정확성 확인

---

## 🔧 3회 누적 자동 fix (2026-07-01 신규)

retry가 영원히 반복되는 함정에서 벗어나기 위한 메커니즘.

### 언제 트리거되는가

- `last_delivery_error`에 `404` 포함
- `deliver` 필드가 위험 패턴: `re.match(r'^discord:\d+(:\d*)?$', deliver)` (thread 없음 또는 빈 thread)
- 누적 카운터(`~/.hermes/cron/.heal_404_retries.json`)의 `jid` 값이 3 이상

### 위험 패턴 regex의 정확한 의미

```python
DANGEROUS_DELIVER = re.compile(r'^discord:\d+(:\d*)?$')
```

| 입력 | 매치? | 이유 |
|:---|:---:|:---|
| `discord:1510397804139515945` | ✅ 위험 | thread 없음 |
| `discord:1510397804139515945:` | ✅ 위험 | thread 빈 문자열 |
| `discord:1510397804139515945:1520640537995247698` | ❌ 안전 | 17-20자리 thread ID |
| `discord:1510397804139515945:1` | ✅ 위험 | thread ID 1자리 (Discord snowflake 17-20자리) |
| `origin` | ❌ 안전 | discord: 프리픽스 없음 |
| `local` | ❌ 안전 | discord: 프리픽스 없음 |
| `discord:1510397804139515945:12345abc` | ✅ 위험 | thread ID 자릿수 검증 없음 → 보수적 |

**보수적 매칭 이유**: Discord snowflake는 항상 17-20자리 숫자. 그 외는 위험으로 분류. false positive보다 false negative 방지 우선.

### Atomic fix 구현 (full pattern)

```python
import json, os, shutil, re

JOBS_JSON = '/home/ubuntu/.hermes/cron/jobs.json'
JOBS_JSON_BAK = JOBS_JSON + '.bak'
ERR_404_DB = '/home/ubuntu/.hermes/cron/.heal_404_retries.json'
DANGEROUS = re.compile(r'^discord:\d+(:\d*)?$')

# 1) 카운터 로드 (날짜 무관 누적)
err_404_db = {}
if os.path.exists(ERR_404_DB):
    try:
        with open(ERR_404_DB) as f:
            err_404_db = json.load(f)
    except: pass

# 2) jobs.json 로드
with open(JOBS_JSON) as f:
    data = json.load(f)

auto_fixed = []

for j in data['jobs']:
    err = (j.get('last_delivery_error') or '').lower()
    deliver = j.get('deliver', '')
    jid = j.get('id', '')
    name = j.get('name', jid[:12])

    if '404' not in err or not DANGEROUS.match(deliver):
        continue

    # 3) 카운트 증가
    count = err_404_db.get(jid, 0) + 1
    err_404_db[jid] = count

    if count < 3:
        continue  # 1~2회: 기존 retry 진행

    # 4) 3회 도달 → 자동 fix
    old = deliver
    j['deliver'] = 'origin'  # in-place mutation

    try:
        shutil.copy2(JOBS_JSON, JOBS_JSON_BAK)  # backup
        tmp = JOBS_JSON + '.tmp'
        with open(tmp, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, JOBS_JSON)  # atomic
        auto_fixed.append((jid, name, old, count, 'OK'))
    except Exception as e:
        auto_fixed.append((jid, name, old, count, f'FIX_ERROR: {str(e)[:60]}'))

# 5) 카운터 저장
with open(ERR_404_DB, 'w') as f:
    json.dump(err_404_db, f, indent=1)
```

### 왜 "3회"인가 (튜닝 근거)

| 회차 | 의미 | 액션 |
|:---:|:---|:---|
| 1 | 일시적 (transient 404 — 봇 disconnect, API hiccup) | retry |
| 2 | 패턴 반복 — 설정 문제 가능성 ↑ | retry + 경계 |
| **3** | **설정 문제 확정** | **자동 fix** |
| 4+ | (이전 fix 실패 시만) | 추가 진단 (별도 로직) |

**3회 = 1일 retry 한도(2회) + 누적 1회 = 약 2-3일 후 자동 fix.** 일시적 오류 흡수하면서 너무 오래 안 묶임.

### 안전장치 체크리스트

- [x] **백업**: `cp jobs.json jobs.json.bak` — fix 직전 항상
- [x] **Atomic write**: `os.replace(tmp, final)` — partial write 방지 (파일 시스템 native)
- [x] **fail-soft**: try/except로 감싸기 — fix 실패해도 watchdog 정상 종료
- [x] **false positive 보호**: 1~2회는 fix 안 함
- [x] **알림**: stdout + `.heal_history.log` 양쪽 기록 → self-healing-cron이 Discord 자동 전달
- [x] **멱등성**: 같은 fix를 여러 번 시도해도 deliver='origin'으로 동일 결과

### 수동 복구

자동 fix가 잘못 적용된 경우:
```bash
cp ~/.hermes/cron/jobs.json.bak ~/.hermes/cron/jobs.json
# 카운터도 리셋
echo '{}' > ~/.hermes/cron/.heal_404_retries.json
```

---

## 🛰️ Direct Discord API Verification (근본 원인 진단)

"이 채널에 봇이 접근 가능한가"를 deliver 실패 없이 직접 확인하는 방법.

### 채널 접근 가능 여부

```bash
source ~/.hermes/.env  # DISCORD_BOT_TOKEN export
curl -s -w "\nHTTP_CODE:%{http_code}\n" \
  -H "Authorization: Bot $DISCORD_BOT_TOKEN" \
  "https://discord.com/api/v10/channels/<channel_id>"
```

| 응답 | 의미 |
|:---|:---|
| HTTP 200 + JSON | 봇이 채널을 보고 보낼 수 있음 |
| HTTP 404 "Unknown Channel" | 봇 접근 불가 (서버 추방, 채널 archived/private, 봇 권한 제거) |
| HTTP 401 Unauthorized | 토큰 무효 |
| HTTP 403 Forbidden | 봇은 서버에 있지만 해당 채널 권한 없음 |

### deliver 형식별 작동 가능성 (실측 2026-07-01)

Home channel ID `1510397804139515945`에 대해:

| deliver 형식 | 결과 |
|:---|:---|
| `discord:1510397804139515945` (본채널 직접) | ❌ 404 "Unknown Channel" |
| `discord:1510397804139515945:` (빈 thread) | ❌ 404 (추정 — 미테스트) |
| `discord:1510397804139515945:1520640537995247698` (thread) | ✅ 정상 작동 (다른 cron이 사용 중) |
| `origin` | ✅ 정상 (현재 세션 thread로 자동 라우팅) |
| `local` | ✅ 정상 (Discord 안 거침) |

**관찰**: 봇이 Home 본채널에 직접 쓰기는 못 하지만, 특정 thread에는 접근 가능. Discord API의 "Unknown Channel"이 deliver에 따라 부분적으로 false negative를 반환하는 듯. **신뢰할 수 있는 패턴은 `origin` 또는 `discord:HomeID:threadID` (검증된 것만)**.

### 봇 정보 확인

```bash
# 봇이 어떤 guild에 있는지
curl -s -H "Authorization: Bot $DISCORD_BOT_TOKEN" \
  "https://discord.com/api/v10/users/@me/guilds"

# 특정 guild의 채널 목록 (봇이 볼 수 있는 것만)
curl -s -H "Authorization: Bot $DISCORD_BOT_TOKEN" \
  "https://discord.com/api/v10/guilds/<guild_id>/channels"
```

**활용**: deliver가 404일 때 위 두 명령으로 봇이 그 서버/채널에 접근 가능한지 직접 확인. 가능 → deliver 형식 문제. 불가 → 봇 재초대 필요.

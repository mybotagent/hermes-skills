---

# v2/v3 갱신 (2026-07-13)

## 6. 멀티 후보 env lookup (CRITICAL)

**문제**: 기존 `_env_lookup`은 `~/.hermes/.env.discord_webhook`만 봄. 메인 `~/.hermes/.env`에 박힌 키는 못 읽음 → 워치독이 "LLM 키 미설정" 거짓 진단을 무한 반복.

**Fix (멀티 후보 fallback + 견고한 파싱)**:

```python
def _env_lookup(key):
    """v2: 멀티 후보 — Discord env, main .env, ~/.env 순회. # 주석·빈값·따옴표 모두 견고 처리."""
    candidates = [
        f'{HERMES_HOME}/.env.discord_webhook',
        f'{HERMES_HOME}/.env',
        f'{os.path.expanduser("~")}/.env',
    ]
    for env_path in candidates:
        if not os.path.exists(env_path):
            continue
        try:
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if line.startswith(f'{key}='):
                        val = line.split('=', 1)[1].strip().strip('"').strip("'")
                        if val:  # 빈값 skip
                            return val
        except Exception:
            continue
    return ''
```

**검증 (1초)**:
```python
import sys
sys.path.insert(0, '/home/ubuntu/.hermes/scripts')
from self_healing_watchdog import DEEPSEEK_KEY
print('len=', len(DEEPSEEK_KEY))  # 0이면 버그, 35+면 OK
```

**왜 3개월+ 묵었나**: 첫 후보 파일 없으면 즉시 empty 반환 → 워치독 본체는 silent fail → 사용자는 "키 설정했는데 왜 안 되지?" 경험만. **Pitfall**: key-by-key 조회 함수는 첫 후보에서 못 찾으면 silent fail ❌, 멀티 후보 순회 ✅.

## 7. urllib.request.Request(timeout=15) 버그

**문제**: `Request(timeout=15)` → `TypeError: Request.__init__() got an unexpected keyword argument 'timeout'`. `timeout`은 `urlopen()`의 인자지 `Request` 생성자 인자 아님.

**Fix**:
```python
# ❌ BAD
req = urllib.request.Request(url, data=..., headers=..., timeout=15)
with urllib.request.urlopen(req) as resp: ...

# ✅ GOOD
req = urllib.request.Request(url, data=..., headers=...)
with urllib.request.urlopen(req, timeout=15) as resp: ...
```

**왜 묭었나**: DeepSeek 키 없으면 거짓 진단 fallback으로 끝나서 `urllib.request.Request` 라인에 도달 안 함. `_env_lookup` 멀티 후보 fix 먼저 적용해야 이 버그 노출됨 — **순서 의존**. env 로드 후 반드시 LLM 호출 dry-run으로 검증.

## 8. 거짓 진단 무한 알림 차단 — silence_until_key_present sentinel

**문제**: 워치독이 진단을 못 하면 (키 누락, LLM fail, ...) 매 cycle 같은 알림 → Discord spam.

**Fix**: Layer 2 진단 결과 `fix_action='silence_until_key_present'` sentinel이면 Layer 3 (Discord) skip.

```python
def call_llm_analyze(...):
    if not DEEPSEEK_KEY:
        return {
            'root_cause': 'watchdog LLM 키 미설정 — 자동 fix 시도 생략, 다음 사이클에 retry',
            'fix_action': 'silence_until_key_present',  # ← sentinel
            'auto_fixable': False,
            'confidence': 'low',
            'note': 'DEEPSEEK_API_KEY 누락 — alert 대신 silent',
        }

# caller
if fix_action_rec == 'silence_until_key_present':
    discord_sent = False
    root_cause_actions.append((jid, name, root_cause, fix_action_rec, 'SILENT_NO_KEY', False))
    skipped.append((jid, name, day_retries))
    continue  # Discord 호출 skip
```

**원칙**: 워치독은 "원인을 정확히 모르면 알리지 않는다". false-positive 알림은 silent로 전환.

## 9. LLM_CACHE_TTL_HOURS 단축 (v2: 6h → 1h)

이유: 캐시된 진단이 거짓이면 6시간 동안 매 cycle 같은 알림 반복. 1시간으로 줄이면 더 자주 재평가. LLM 1회 호출 = ~$0.0001이라 비용 부담 없음.

```python
LLM_CACHE_TTL_HOURS = 1  # v2: 6h → 1h
```

## 10. v2 검증 패턴 — 단독 import 테스트

patch 후 매번 `cronjob run` 돌릴 필요 없음. 단독 import + 속성 체크가 1초 안에 끝남.

```python
# ① env 로드 확인
import sys
sys.path.insert(0, '/home/ubuntu/.hermes/scripts')
from self_healing_watchdog import DEEPSEEK_KEY, LLM_CACHE_TTL_HOURS, call_llm_analyze
print('len=', len(DEEPSEEK_KEY))  # 0이면 버그

# ② silent fallback
import os
os.environ.pop('DEEPSEEK_API_KEY', None)
result = call_llm_analyze('test', 'test-job', 'origin', 'error', 'some err', [])
print(result['fix_action'])  # 'silence_until_key_present' 기대

# ③ 실제 LLM 호출 dry-run
result = call_llm_analyze('f405cd52a6e8', 'Memory Alert', 'origin', 'script failed',
    '⚠ MEMORY ALERT: 2200/2200 chars (100.0%)', [])
print(result['root_cause'])  # 도메인 컨텍스트 힌트 없으면 'Discord 2000자 초과' 거짓
```

## 11. v3 — LLM 진단 정확도 = 컨텍스트 힌트로 결정 (CRITICAL)

**문제**: LLM이 단순 숫자만 보고 도메인 지식 없이 추측성 진단을 만듦.

**실제 사례 (2026-07-13 f405cd52a6e8)**:
- `last_error`: `⚠ MEMORY ALERT: 2200/2200 chars (100.0%)`
- LLM 진단 (hint 없을 때): "Discord 웹훅 메시지가 2200자로 2000자 제한을 초과" ← **거짓**
- 진짜 원인: Hermes 내부 memory 100% 가득 참

**Fix**: `call_llm_analyze` prompt에 도메인 컨텍스트 힌트 5줄 명시:

```python
prompt = '\n'.join([
    '너는 시스템 자동복구 분석가다. ...',
    '',
    '## 컨텍스트 힌트 (v2 2026-07-13)',
    '- cron stdout의 "N/N chars (X%)" 형식은 **Hermes 내부 memory 사용률** (예: "2200/2200 chars (100%)" = 메모리 100% 가득 참). Discord 메시지 한도가 아님.',
    '- "script exited with code 1"는 보통 스크립트의 의도된 비정상 종료 (예: threshold 초과 시 alert 발송 후 exit 1).',
    '- 같은 진단이 LLM_CACHE_TTL_HOURS 이내 반복되면 캐시된 거짓 진단 가능성 — root_cause를 confidence:low로 표시.',
    '- deliver가 "discord:숫자:숫자" 형식이면 thread 안으로 보낸 것. 404면 thread가 만료됐거나 채널을 찾을 수 없음.',
    '- auto_fixable=True인 경우: jobs.json deliver 변경 / stale lock 제거 / cache 초기화 / memory compact 같은 **즉시 적용 가능한 액션** 우선.',
    '',
    'cron:',
    f'- id: {jid}',
    f'- name: {name}',
    ...
])
```

**검증**: hint 추가 후 `call_llm_analyze("f405cd52a6e8", ...)` →
```json
{
  "root_cause": "Hermes 내부 memory 사용률이 100%에 도달하여 스크립트가 의도적으로 exit 1로 종료되었으며, 이는 메모리 한계 초과 경고입니다.",
  "fix_action": "Hermes memory를 compact하거나 캐시를 초기화하여 사용률을 낮춘 후 재시작",
  "auto_fixable": true,
  "confidence": "high"
}
```

→ `memory` + `100%` 키워드 매칭으로 `run_memory_compact` 자동 fix 가능.

## 12. v3 — 자동 fix 액션 + LLM 진단 매핑

**`apply_fix()` 확장**:

```python
def apply_fix(fix_action):
    """시스템이 즉시 적용 가능한 fix. 성공 여부 반환."""
    if fix_action == 'reset_deliver_to_origin':
        return True
    if fix_action == 'remove_stale_lock':
        try:
            os.remove(LOCK_FILE)
            return True
        except Exception:
            return False
    if fix_action == 'run_memory_compact':
        try:
            r = subprocess.run(
                f'{HERMES_HOME}/scripts/memory_daily_compact.sh',
                shell=True, capture_output=True, text=True, timeout=30,
            )
            return r.returncode == 0
        except Exception:
            return False
    if fix_action == 'reset_false_rca_cache':
        try:
            with open(ROOT_CAUSE_DB, 'w') as f:
                json.dump({}, f)
            try:
                with open(RETRY_DB) as f:
                    rd = json.load(f)
                rd[TODAY] = {}
                with open(RETRY_DB, 'w') as f:
                    json.dump(rd, f, indent=2)
            except Exception:
                pass
            return True
        except Exception:
            return False
    return False
```

**워치독 본체에서 LLM 진단 → 자동 fix 분기**:

```python
# v2 (2026-07-13): LLM 진단 기반 자동 fix 시도
llm_fix_action = None
if auto_fixable:
    rc = (root_cause or '').lower()
    if 'memory' in rc and ('100%' in rc or 'full' in rc or '가득' in rc or '초과' in rc):
        llm_fix_action = 'run_memory_compact'
    elif '거짓' in rc or 'cache' in rc or '루프' in rc or '반복' in rc:
        llm_fix_action = 'reset_false_rca_cache'

if llm_fix_action and apply_fix(llm_fix_action):
    root_cause_actions.append((jid, name, root_cause, fix_action_rec, 'AUTO_FIX_APPLIED', True))
    retries[TODAY][jid] = 0  # retry 카운터 즉시 reset
    save_db(JOBS_JSON, jobs_data)
    skipped.append((jid, name, day_retries))
    continue  # Discord 알림 skip
```

**자동 fix 후 retry reset**: 다음 cycle에서 정상 평가. 이게 핵심 — 워치독이 진짜로 "자가 치유"하는 사이클.

## 13. v3 — 캐시 hit_count 3회 강제 재진단

**문제**: 같은 진단이 캐시 hit으로 반복되면 LLM이 새 분석 안 함. 거짓 진단이면 1시간 TTL 동안 같은 알림 반복.

**Fix**: `hit_count` 필드 추가, 3회째에 강제 LLM 재호출:

```python
cached = root_cause_db.get(jid)
if cached and (NOW_EPOCH - cached.get('ts', 0)) < LLM_CACHE_TTL_HOURS * 3600:
    if cached.get('hit_count', 0) < 3:
        llm_result = cached['result']
        llm_source = 'cache'
        cached['hit_count'] = cached.get('hit_count', 0) + 1
        root_cause_db[jid] = cached
    else:
        # 3회째: 캐시 무시하고 강제 재진단
        llm_result = call_llm_analyze(jid, name, deliver, status, delivery_error, recent_history)
        llm_source = 'live_after_3hits'  # 운영자가 escape 인지 가능
        root_cause_db[jid] = {'ts': NOW_EPOCH, 'result': llm_result, 'hit_count': 0}
else:
    llm_result = call_llm_analyze(...)
    llm_source = 'live'
    root_cause_db[jid] = {'ts': NOW_EPOCH, 'result': llm_result, 'hit_count': 0}
```

**왜 3회인가**: 1~2회는 transient 가능성, 3회는 거짓 진단 강력 의심. 즉시 escape.

## 14. v3 — Memory 100% 알림 = exit 1의 의도된 패턴

**문제**: `memory_alert.py check`는 memory 90%+ 시 `stdout "⚠ MEMORY ALERT"` + `exit 1`로 종료. 워치독이 이걸 "스크립트 실패"로 보고 retry → 무한 루프.

**진짜 의미**: "memory 100% 차서 알림 발송 완료, 스크립트 임무 완수".

**진단**: `last_error`에 `MEMORY ALERT: 2200/2200 chars` 패턴 → 즉시 `memory_daily_compact.sh` 1회 수동 실행.

**자동 fix (v3)**: 위 11번 컨텍스트 힌트 + 12번 자동 fix 매핑으로 워치독이 정확히 진단 + 자동 compact 실행. retry 카운터 reset → 다음 cycle 자연 검증.

## 15. provider/model drift 잡 skip 패턴 (2026-07-11)

**증상**: `hermes config set model.provider deepseek` 같은 토글 후 unpinned 잡이 다음 cycle에 `RuntimeError: Skipped to prevent unintended spend`로 fail.

**last_error 키워드**:
- `Skipped to prevent unintended spend`
- `config drifted`
- `this job is unpinned`
- `To run on the new config, pin it explicitly`

→ 이 키워드 보이면 즉시 잡의 pin 상태 확인 → `hermes cron update <jid> --provider <p> --model <m>` 후 재실행.

**워치독의 흔한 오진**: 이걸 "API 키 미설정"으로 진단. 진단 시 반드시 last_error 키워드부터 확인.

## v4 후보

- **자동 fix 매핑 키워드 확장** — `401`/`timeout`/`disk full` 등
- **config drift 자동 감지** — 잡의 provider/model 필드 ↔ config.yaml global 비교 후 자동 pin
- **자동 fix 성공률 추적** — `.heal_history.log` grep으로 `AUTO_FIX_APPLIED` vs 알림 비율 → 메트릭 대시보드
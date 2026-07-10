# LLM 근본 원인 분석 — Self-Healing Watchdog의 Layer 2/3

**2026-07-10 신규**. `self_healing_watchdog.py` 안에 LLM(DeepSeek) 1-shot 호출 + Discord webhook 통보 패턴.

## 배경 (왜 추가했는가)

이전 동작: cron이 `last_status='error'`로 fail → 1일 2회까지 cron run 재실행 → 2회 초과 시 단순 `⚠️ 재시도 초과` 출력 후 silent 종료. 같은 에러가 매일 반복되어도 자동 진단 없이 누적만 됨.

사용자 지시 (aiprofit, 2026-07-10):
> "재시도 초과 하면 셀프 힐링 반복만하지 말고 근본 원인 찾아서 해결하라고. 재시도-> 원인 디스코드애 보내기 => 근본 원인 해결 스스로 llm호출해서 해결"

**운영 원칙**:
1. 사람 호출 ❌ — 시스템이 LLM으로 자가 진단
2. 자동 fix 가능하면 즉시 적용, 불가하면 사람 결정 영역으로 Discord 통보
3. 같은 cron은 같은 에러로 6시간 안에 재호출 안 함 (TTL 캐시)

## 3-Layer Escalation

```
재시도 ≥ 2회 누적
   │
   ├─ Layer 1: 패턴 매칭 → 즉시 fix 가능한가?
   │   • 404 + 위험 deliver → jobs.json deliver=origin
   │   • stale .tick.lock (30분+) → 강제 rm
   │   • rate limit (429) → 자연 cooldown 60분
   │   • module not found → venv/path 확인 권고
   │
   ├─ Layer 2: LLM 근본 원인 분석 (DeepSeek API, 1-shot curl)
   │   • prompt: cron 메타 + last_error + recent_history → JSON 4필드
   │   • root_cause / fix_action / auto_fixable(bool) / confidence
   │   • 6시간 캐시 (같은 cron은 같은 LLM 호출 안 함)
   │
   └─ Layer 3: Discord webhook 통보 (embed)
       • 자동 fix 가능 여부 + LLM 권고 → 사람 결정 영역 명시
```

## DeepSeek API 호출 패턴 (no_agent에서)

cron은 `no_agent=True`로 동작하므로 LLM 호출은 **curl 또는 urllib.request 1회**가 핵심. agent loop 없음.

```python
import json, urllib.request, re

def call_llm_analyze(jid, name, deliver, status, last_error, recent_history, api_key):
    if not api_key:
        return {
            'root_cause': 'LLM 키 미설정 (DEEPSEEK_API_KEY env 없음)',
            'fix_action': '수동 진단 필요',
            'auto_fixable': False,
            'confidence': 'low',
            'note': 'webhook만 전송됨, LLM 분석 생략',
        }

    # prompt를 list + '\n'.join()으로 빌드 (큰따옴표 충돌 회피)
    prompt_lines = [
        '너는 시스템 자동복구 분석가다. 아래 cron 작업이 실패했어.',
        '**구체적인 근본 원인** 1~2문장, **즉시 적용 가능한 자동 fix** '
        '(auto_fixable=True/False), **사용자가 확인해야 할 결정** 3가지 필드로 JSON만 답해.',
        '',
        'cron:',
        f'- id: {jid}',
        f'- name: {name}',
        f'- status: {status}',
        f'- deliver: {deliver}',
        f'- last_error: {last_error[:300]}',
        f'- recent_history: {recent_history[-3:]}',
        '',
        '응답 스키마 (JSON):',
        'root_cause, fix_action, auto_fixable(bool), confidence(high|medium|low) — '
        '4개 필드 JSON만 답해.',
    ]
    prompt = '\n'.join(prompt_lines)

    try:
        req_body = json.dumps({
            'model': 'deepseek-chat',
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': 0.2,  # 일관된 분석
            'max_tokens': 400,
        }).encode()
        req = urllib.request.Request(
            'https://api.deepseek.com/v1/chat/completions',
            data=req_body,
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
            timeout=15,
        )
        with urllib.request.urlopen(req) as resp:
            payload = json.loads(resp.read().decode())
        text = payload['choices'][0]['message']['content'].strip()
        # JSON 블록만 추출 (LLM이 코드블록으로 감싸는 경우 대비)
        m = re.search(r'\{[\s\S]*\}', text)
        if not m:
            raise ValueError('JSON 추출 실패')
        parsed = json.loads(m.group(0))
        # 안전 default
        parsed.setdefault('auto_fixable', False)
        parsed.setdefault('confidence', 'low')
        parsed.setdefault('root_cause', text[:200])
        parsed.setdefault('fix_action', '수동 진단 필요')
        return parsed
    except Exception as e:
        return {
            'root_cause': f'LLM 호출 실패: {str(e)[:100]}',
            'fix_action': '수동 진단 필요',
            'auto_fixable': False,
            'confidence': 'low',
            'note': f'llm_error: {str(e)[:80]}',
        }
```

## 6시간 캐시 스키마

```python
# ~/.hermes/cron/.heal_root_cause.json
{
  "f405cd52a6e8": {
    "ts": 1752167400,  # epoch seconds (UTC)
    "result": {
      "root_cause": "memory.md 95% 사용 중 → memory_alert이 stderr로 fail",
      "fix_action": "memory_daily_compact.sh 즉시 실행",
      "auto_fixable": True,
      "confidence": "high"
    }
  }
}
```

캐시 hit 시나리오:
```python
cached = root_cause_db.get(jid)
if cached and (now_epoch - cached.get('ts', 0)) < LLM_CACHE_TTL_HOURS * 3600:
    llm_result = cached['result']
    llm_source = 'cache'  # Discord embed에 표시
else:
    llm_result = call_llm_analyze(...)
    llm_source = 'live'
    root_cause_db[jid] = {'ts': now_epoch, 'result': llm_result}
```

**왜 6시간?** 1시간마다 같은 cron이 LLM 호출되면 비용 누적. 6시간은 "근본 원인은 보통 1일 안에 안 변함"이라는 경험칙. 더 짧게 (1~2시간) 해도 되고, 더 길게 (12~24시간) 해도 됨 — 운영 환경에 따라 조정.

## Discord Embed (webhook) 템플릿

```python
import json, urllib.request
from datetime import datetime, timezone

def send_discord(webhook_url, title, body, color=0xff5555):
    if not webhook_url:
        return False
    embed = {
        'title': title,
        'description': body[:1900],  # Discord limit
        'color': color,  # red: 0xff5555
        'footer': {'text': 'hermes self-healing watchdog (root-cause) | 2026-07-10'},
        'timestamp': datetime.now(tz=timezone.utc).isoformat(),
    }
    payload = json.dumps({'embeds': [embed]}).encode()
    try:
        req = urllib.request.Request(
            webhook_url, data=payload,
            headers={'Content-Type': 'application/json'},
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            return resp.status in (200, 204)
    except Exception:
        return False

# 본문 빌드 (f-string 큰따옴표 회피: 변수로 추출)
bool_fix = '예 (자동 fix 가능)' if auto_fixable else '아니오 (수동 확인 필요)'
title = f'🔴 재시도 초과 + 근본 원인 ({confidence} conf)'
body = '\n'.join([
    f'**job**: `{name}` (`{jid[:12]}`)',
    f'**status**: `{status}` · **err**: `{delivery_error[:200]}`',
    f'**deliver**: `{deliver}`',
    '',
    f'**🎯 근본 원인**: {root_cause}',
    '',
    f'**🛠 권고 fix**: {fix_action_rec}',
    '',
    f'**🤖 자동 fix 가능**: {bool_fix}',
    f'**📡 분석 출처**: {llm_source}',
])
discord_sent = send_discord(webhook_url, title, body)
```

## Env Keys (필수)

| Key | 용도 | 미설정 시 동작 |
|:----|:-----|:-------------|
| `DEEPSEEK_API_KEY` | LLM 분석 | root_cause='LLM 키 미설정', webhook만 동작 |
| `DISCORD_WEBHOOK_ROOT_CAUSE` | 근본 원인 통보 | discord=❌, LLM 분석은 정상 진행 |

자동 로드 패턴:
```python
import os
def _env_lookup(key):
    env_path = f'{os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes"))}/.env.discord_webhook'
    if not os.path.exists(env_path): return ''
    try:
        with open(env_path) as f:
            for line in f:
                if line.startswith(f'{key}='):
                    return line.split('=', 1)[1].strip().strip('"').strip("'")
    except: pass
    return ''

DEEPSEEK_KEY = os.environ.get('DEEPSEEK_API_KEY') or _env_lookup('DEEPSEEK_API_KEY')
DISCORD_WEBHOOK = os.environ.get('DISCORD_WEBHOOK_ROOT_CAUSE') or _env_lookup('DISCORD_WEBHOOK_ROOT_CAUSE')
```

`~/.hermes/.env.discord_webhook` 예시:
```
DISCORD_WEBHOOK_ROOT_CAUSE=https://discord.com/api/webhooks/...
DEEPSEEK_API_KEY=sk-...
```

## 검증된 출력 (2026-07-10 실측)

강제 시뮬레이션: `.heal_retries.json`의 `f405cd52a6e8`을 2회로 설정 후 `bash self_healing_watchdog.sh`:

```
[HEAL] 1 job(s) 재실행 시작
  ✅ f405cd52a6e8: 🧠 Memory Usage Alert (평일 09:00 KST) [unknown] → Triggered job: ...
  ⚠️  1 job(s) 재시도 초과 — 근본 원인 분석 발동
  - f405cd52a6e8: 🧠 Memory Usage Alert (평일 09:00 KST) (2회)
🧠 1 job(s) LLM 근본 원인 분석 → Discord 통보
  · f405cd52a6e8: 🧠 Memory Usage Alert (평일 09:00 KST) | discord=❌
    원인: LLM 키 미설정 (DEEPSEEK_API_KEY 없음)
    fix : 수동 진단 필요 [AWAITING_MANUAL]
```

`discord=❌` 표시 = `DISCORD_WEBHOOK_ROOT_CAUSE` env 미설정. LLM 키도 미설정 → graceful fallback으로 두 채널 모두 "키 미설정" 보고.

## 히스토리 로그 포맷

`~/.hermes/cron/.heal_history.log`:
```
2026-07-10 12:30:00 KST f405cd52a6e8 🧠 Memory Usage Alert ROOT_CAUSE_ANALYZED status=AWAITING_MANUAL cause=LLM 키 미설정 (DEEPSEEK_API_KEY 없음) fix=수동 진단 필요 discord=FAIL
```

grep 한방 진단:
```bash
# 오늘 LLM 분석 발동 횟수
grep "ROOT_CAUSE_ANALYZED" ~/.hermes/cron/.heal_history.log | grep "$(date +%Y-%m-%d)" | wc -l

# 자동 fix 가능한 cron
grep "AWAITING_MANUAL" ~/.hermes/cron/.heal_history.log | grep "$(date +%Y-%m-%d)" | wc -l

# Discord 전송 성공률
grep -c "discord=OK" ~/.hermes/cron/.heal_history.log
grep -c "discord=FAIL" ~/.hermes/cron/.heal_history.log
```

## 운영 규칙 (aiprofit, 2026-07-10 결정)

1. **사람 호출 ❌, 시스템 자가 분석 ✅** — "스스로 llm호출해서 해결"이 사용자 운영 원칙
2. **LLM 권고는 정보용** — `auto_fixable=True`여도 즉시 적용 ❌, 통보만 (사람 결정 영역)
3. **재실행 안 함 (같은 cycle)** — LLM 분석 후에도 `cronjob run` 재호출은 같은 cycle에서 안 함. 다음 10분 cycle에서 자연 재시도
4. **fix 성공 시 retry counter 리셋** — Layer 1에서 fix 적용했으면 `retries[today][jid] = 0`. 다음 cycle 자연 검증
5. **사용자 Discord thread = #시스템 (또는 운영자 선호 thread)** — `DISCORD_WEBHOOK_ROOT_CAUSE` env로 routing

## 흔한 함정 (2026-07-10 실측)

### 1. bash heredoc 안 Python f-string 사용 ❌

```bash
# ❌ BAD — bash brace expansion이 {name}을 command로 해석
python3 -c "
import json
data = {
    'job': f'{name}',  # bash가 {name}을 brace expansion으로 시도
}
"
```

**증상**: `line 57: {name}: command not found` 같은 noise 출력. Python 자체는 동작하지만 stderr noise.

**해결**: bash wrapper는 단순히 python 호출만, 본체는 별도 `.py` 파일.

```bash
# ✅ GOOD — bash는 .py 실행만
#!/bin/bash
python3 "$HOME/.hermes/scripts/self_healing_watchdog.py"
```

### 2. f-string 안에 큰따옴표 ❌

```python
# ❌ BAD — f-string syntactic error
body = f'**🤖 자동 fix 가능**: {"예" if auto_fixable else "아니오"}'
# SyntaxError: f-string: unmatched ('"') in expression
```

**해결**: 변수로 추출.

```python
# ✅ GOOD
bool_fix = '예 (자동 fix 가능)' if auto_fixable else '아니오 (수동 확인 필요)'
body = f'**🤖 자동 fix 가능**: {bool_fix}'
```

### 3. JSON 스키마 한 줄에 큰따옴표 ❌

```python
# ❌ BAD — bash heredoc에서 '...' 안에 "..." 들어가면 충돌
prompt = f'''... 응답 스키마 (그대로):
{{"root_cause": "string", "fix_action": "string", ...}}'''
```

**증상**: bash가 `{"root_cause":`를 따옴표 끝으로 인식, 그 이후 `string"`를 따옴표 매칭하려고 시도하다 syntax error.

**해결**: prompt는 list + `'\n'.join()`으로 빌드 (큰따옴표 0개).

```python
# ✅ GOOD
prompt_lines = [
    '너는 시스템 자동복구 분석가다.',
    f'cron: id={jid}, name={name}, ...',
    '',
    '응답 스키마: root_cause, fix_action, auto_fixable(bool), confidence',
]
prompt = '\n'.join(prompt_lines)
```

### 4. LLM 키 없을 때 silent fail ❌

```python
# ❌ BAD — API key 없으면 None 반환 → caller가 AttributeError
def call_llm_analyze(...):
    if not api_key: return None
    ...

# caller
result = call_llm_analyze(...)
result.get('root_cause')  # AttributeError: 'NoneType' object has no attribute 'get'
```

**해결**: 명시적 fallback dict 반환.

```python
# ✅ GOOD
def call_llm_analyze(...):
    if not api_key:
        return {
            'root_cause': 'LLM 키 미설정 (DEEPSEEK_API_KEY env 없음)',
            'fix_action': '수동 진단 필요',
            'auto_fixable': False,
            'confidence': 'low',
        }
    ...
```

### 5. 6시간 캐시 너무 짧으면 비용 누적

LLM 1회 호출 = ~$0.0001. 50개 cron이 1시간마다 LLM 호출 = $0.005/시간 = $3.6/월. 적지만 캐시 1~2시간으로 줄이면 비용 더 낮춤. 6시간은 "근본 원인은 보통 1일 안에 안 변함" 경험칙. 운영 환경에 따라 조정.

## 관련 파일

- `~/.hermes/scripts/self_healing_watchdog.py` — 본체
- `~/.hermes/scripts/self_healing_watchdog.sh` — bash wrapper (python 호출만)
- `~/.hermes/cron/.heal_root_cause.json` — LLM 분석 캐시
- `~/.hermes/cron/.heal_history.log` — 모든 액션 append-only
- `~/.hermes/cron/.heal_retries.json` — retry counter (강제 시뮬레이션 가능)
- `~/.hermes/.env.discord_webhook` — DEEPSEEK_API_KEY, DISCORD_WEBHOOK_ROOT_CAUSE

## cron job 메타

| ID | 이름 | Schedule | Mode |
|:--|:----|:---------|:-----|
| `894e773a9a2b` | 🔧 Self-healing watchdog (no_agent) | `*/10 6-22 * * 1-5` | no_agent (script) |

이 cron이 self_healing_watchdog.sh를 호출 → .py 본체 실행 → LLM 분석 → Discord 통보.

## 향후 확장 후보

- **다른 LLM provider** (Claude/GPT-4): DeepSeek 키가 rate-limit에 걸리면 fallback
- **auto_fixable=True 자동 실행 옵션**: 사용자 명시 OK 후 활성화 (현재는 통보만)
- **근본 원인 → wiki 페이지 자동 기록**: 같은 에러 누적 시 self_improve_loop가 패턴 분석
- **Multi-cause**: 여러 cron이 동시에 fail → 공통 원인 분석 (예: GitHub API 장애)

# 워치독 자기 유발 교착 + 진단 필드 사각지대 — 상세 진단 절차

`self-healing-cron` SKILL.md의 "반대편 Blind Spot" / "자기 유발 교착" 섹션의 실전 레퍼런스.

## 0. 왜 이 문서가 있는가

사용자가 "self 힐링 안되는데 이유는?" 라고 물었을 때, 워치독은 **멈춰 있지 않았다**.
24회 정상 실행되고, 실패 잡을 매번 감지해 재실행했고, 재실행은 또 실패했고,
워치독은 그 실패를 **거짓 원인**으로 진단하며 같은 "수정"을 반복했다.

즉 "watchdog이 안 도는" 문제가 아니라 **"watchdog이 자기 자신을 못 보고 + 자기 유발 교착을 재생산"**하는 문제다.
진단 전에 이 두 가지를 분리해서 봐야 한다.

## 1. 먼저 분리할 두 가지

| 질문 | 확인 | 의미 |
|---|---|---|
| 워치독이 실행됐는가? | `cron/executions.db` 에서 watchdog job id의 `status` | 멈춤 vs 오진 |
| 워치독이 실패 잡을 **감지**했는가? | `.heal_history.log` 에 `[HEAL]` / `ROOT_CAUSE_ANALYZED` | 감지 실패 vs 오진 |
| 재실행이 **성공**했는가? | 같은 잡 id의 후속 execution `status=completed` | 교착 vs 진짜 고장 |

watchdog 실행 로그가 정상인데 잡이 계속 실패하면 → **감지/진단/재실행 중 하나가 잘못 동작**하는 것.

## 2. 진단 입력 필드 — `last_error`가 `last_delivery_error`를 대체하지 않는다

`jobs.json`의 잡 상태 필드:

| 필드 | 담고 있는 것 | 실행 실패 시 |
|---|---|---|
| `last_status` | `ok` / `error` | `error` |
| `last_error` | **스크립트 traceback 전문** | **채워짐** |
| `last_delivery_error` | 배달(Discord 등) 실패 사유 | `None` |

즉 실행 실패 잡은 `last_delivery_error`가 빈 상태가 **정상**이다.
`last_delivery_error`만 읽는 watchdog은 실행 실패 원인을 통째로 놓친다.

**반대 방향도 성립**: 배달 실패 잡은 `last_status='ok'`이고 `last_error`는 `None`이고 `last_delivery_error`에 404가 들어있다.
→ 두 방향을 다 봐야 한다. SKILL.md의 "Watchdog Blind Spot"이 후자, 위 섹션이 전자.

```python
# ❌ 실행 실패 원인 누락
err = (j.get('last_delivery_error') or '').lower()

# ✅ 둘 다 본다
err = ((j.get('last_delivery_error') or '') or (j.get('last_error') or '')).lower()
```

## 3. 자기 유발 교착 — 재현/확인 절차

### 3.1 실패 지속 시간 = timeout 값?

`executions.db`의 `started_at`/`finished_at` 차이를 보면 **timeout 패턴**이 드러난다.
timeout이 15초인 코드가 15.3초 만에 죽으면, 죽은 원인은 timeout 만료다.

```sql
select started_at, finished_at, status,
       round((julianday(finished_at)-julianday(started_at))*86400,1) as dur
from executions where job_id='<jid>' order by rowid desc limit 12;
```

`dur`가 15.3 / 30.3처럼 **정확한 timeout+ε**만 나오면 코드 경합 의심.
사용자 액션/입력 대기等原因이면 dur이 흩어진다.

### 3.2 실패 시각에 다른 잡이 겹쳤는가?

```sql
select a.started_at, b.job_id as other, b.status
from executions a join executions b
  on b.job_id != a.job_id
 and b.started_at < a.finished_at
 and b.finished_at > a.started_at
where a.job_id='<jid>' and a.status='failed'
order by a.started_at desc;
```

겹치는 잡이 **워치독 job id**면 자기 유발 확정: 워치독이 재실행한 그 잡이, 재실행 중 다시 죽었다.

### 3.3 중첩 CLI 호출 지점

재실행 대상 스크립트 안에서 CLI를 다시 부르는 곳:

```bash
grep -n "subprocess.run" ~/.hermes/scripts/<target_script>.py
```

`["hermes", "cron", "list"]` 같은 호출이 있으면 그게 후보.
타임아웃이 짧게 잡혀 있으면(예: `timeout=15`) 경합 시 확정적으로 죽는다.

### 3.4 단독 실행은 빠른가?

```bash
time hermes cron list
```

1~3초면 정상. 15초 넘으면 그건 별개 문제(단독에서도 느림).

### 3.5 동시 실행 확인

```bash
hermes cron run <jid> &            # 백그라운드
time hermes cron list               # 다른 터미널/동시 실행
hermes cron run <jid>               # 중복 실행 시도
```

스케줄러가 중복 실행을 막으면 `Job is already being fired by the scheduler; not run again.` 이 나온다.
이 메시지는 **정상 방어 동작**이고 버그가 아니다.

## 4. 거짓 RCA → 자기 강화 루프

### 4.1 메커니즘

1. 진단 입력이 비어 있음 (빈 `error_text`)
2. LLM이 근거 없이 RCA를 생성 ("로그가 기록되지 않아 원인을 확인할 수 없습니다")
3. RCA 문구에 `'거짓' / 'cache' / '루프' / '반복'` 키워드 존재
4. `reset_false_rca_cache` 자동 fix 매핑
5. 진단 캐시 + retry 카운터 리셋
6. 다음 cycle에 **똑같은 입력** → **똑같은 RCA** → ∞

### 4.2 확인

```bash
tail -100 ~/.hermes/cron/.heal_history.log | grep ROOT_CAUSE_ANALYZED
cat ~/.hermes/cron/.heal_root_cause.json
```

같은 `cause` 문자열이 `AUTO_FIX_APPLIED`와 함께 반복되면 이 루프다.

### 4.3 진짜 원인 대조 체크리스트

LLM RCA를 믿기 전에 반드시 cross-check:

- [ ] RCA가 주장한 로그가 실제로 존재하는가? (`ls ~/.hermes/cron/output/<jid>/`)
- [ ] RCA가 "로그가 없다"고 했는데 `jobs.json.last_error`에 traceback이 있는가?
- [ ] `executions.db`의 `error` 컬럼에 원문이 있는가? (스키마에 `stdout` 컬럼은 없을 수 있다)
- [ ] RCA가 지목한 파일/환경변수가 실제로 그 상태인가?

## 5. 주의: 관찰 도구 자체가 다른 인스턴스를 볼 수 있다

`cronjob` 계열 도구와 로컬 `hermes cron list`가 **다른 시점의 스냅샷**을 반환하는 경우가 있다.
같은 job id에 대해 날짜가 크게 다르면(예: months 차이) 도구가 다른 인스턴스/스냅샷을 보고 있다는 뜻이다.

**HARD RULE**: cron 상태의 권위 있는 소스는 **로컬 `~/.hermes/cron/jobs.json` + `hermes cron list` + `cron/executions.db`** 다.
외부 도구의 반환값이 로컬과 충돌하면 로컬을 신뢰하고, 그 차이를 "도구 문제"로 별도 기록한다.

## 6. 도구 스키마 함정 (수집 단계에서 실수)

- `executions.db`에 `stdout` 컬럼이 없을 수 있다 → `pragma table_info(executions)` 로 실제 컬럼 확인. 오류는 `error` 컬럼에 있다.
- `deliveries.db`에서 `executions` 테이블을 참조하면 "no such table" → 두 DB가 별개 파일이면 `ATTACH` 로 붙여서 조인.
- `deliveries.db`의 `content` 길이가 0이어도 배달이 성공했을 수 있다 — gateway가 Discord에 직접 전송하면 로컬 큐 레코드 본문은 비어 있다. **Discord 채널 실제 메시지로 확인**하는 것이 유일한 검증.

## 7. 통보 경로도 함께 점검

RCA 통보는 `DISCORD_WEBHOOK_ROOT_CAUSE` webhook을 쓴다. 이 env가 없으면 `send_discord()`는 즉시 `False`를 반환한다.
그래도 사용자가 Discord에서 RCA를 볼 수 있는 건 **워치독 cron 자체의 stdout 전달 경로** 때문이다(별개 경로).
→ `.heal_history.log`의 `discord=FAIL`과 "사용자가 Discord에서 RCA를 봄"이 **동시에 성립**할 수 있다. 모순으로 착각하지 말 것.

## 8. 최소 수정 세트 (코드 반영 시)

1. 진단 입력에 `last_error` 포함 (`error_text = last_delivery_error or last_error`)
2. 오류 문자열이 빈 상태에서 나온 RCA에는 자동 fix 금지
3. 동일 RCA 3회 반복 시 자동 fix 중지 + 에스컬레이션
4. 재실행 대상 스크립트의 중첩 CLI 호출 제거 또는 timeout 상향
5. `DISCORD_WEBHOOK_ROOT_CAUSE` 설정

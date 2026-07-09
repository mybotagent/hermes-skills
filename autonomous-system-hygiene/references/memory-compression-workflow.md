# Memory Compression Workflow (사용자 룰: 90% 넘으면 자율 정리)

> Canonical playbook for the memory.md auto-compaction pipeline. Established 2026-07-07 from a user message: **"메모리 90 넘으면 알아서 자율적으로 정리하기"**.

## 사용자 룰 (single-line, hard requirement)

```
memory.md 사용률이 90% (1,980/2,200 chars)를 넘으면 자동으로 정리한다.
```

이 룰은 `memory_auto_compact.py` + cron `cb2ee5fafc5d` (매일 06:30 KST)에 영구화되어 있다.

## 파이프라인

```
[매일 06:30 KST]
   ↓
memory_daily_compact.sh (wrapper, silent 성공)
   ↓
memory_auto_compact.py
   ├─ size check (≥90%?)
   ├─ drift pre-check (>5% → block + alert)
   ├─ apply 12 rules
   ├─ size 재검증 (<90%? 아니면 alert)
   └─ write memory.md
   ↓ silent (deliver=local)
```

## Canonical paths

| 항목 | 경로 |
|------|------|
| 메모리 파일 | `~/.hermes/memories/MEMORY.md` (plural `memories/`, 대문자 `MEMORY.md`) |
| 압축 스크립트 | `~/.hermes/scripts/memory_auto_compact.py` |
| Wrapper 스크립트 | `~/.hermes/scripts/memory_daily_compact.sh` |
| Drift 검증 | `~/.hermes/scripts/compression_drift_check.py` |
| Cron | `cb2ee5fafc5d` (매일 06:30 KST, deliver=local) |

**Pitfall — path mismatch**: `~/.hermes/memory.md` (singular, lowercase) 는 존재하지 않는다. 항상 `~/.hermes/memories/MEMORY.md`. 압축 스크립트는 `Path.home() / ".hermes" / "memories" / "MEMORY.md"` 사용. 다른 자동화 도구가 `~/.hermes/memory.md`를 가정하면 import 실패.

## 압축 룰 12개 (2026-07-07 합의)

1순위 — wiki 중복 제거 (`infra/bot-architecture.md`로 승격):
- `(2026-07-02: config/TICKER_SECTOR 제거→통합)` — event log, audit에 이미 있음
- `cron deadParent:liveThread=thread 직접 fetch로 작동, 마이그레이션 권장.` — 이미 fix 완료된 event

2순위 — 약어 치환:
- `.google_service_account.json.` 제거
- `(sanghee.lee2222@gmail.com)→himalaya/AppPw→` → `→`
- `Bot IDs(2026-07-01정정):` → `Bot IDs:` (이전 메모리 오류 정정 사실은 별도 wiki page)
- `이전 메모리 오류 정정. ` 제거

3순위 — 표기 단축:
- `iptables 9119 IP제한 없음(어디서나 접근)` → `iptables 9119 무제한`
- `iptables 동일` → `동일`
- `sync fe96a 12KST` → `sync12KST`
- `(봇), plan=` → `(봇),plan=`, `, ds=` → `,ds=`
- `./kanban필요시.` → `.`

## 안전 가드 (safety rails)

| 가드 | 룰 |
|------|------|
| **drift pre-check** | `compression_drift_check.py` 결과 >5% 면 압축 자동 차단 (memory ↔ state.db fact mismatch 방지) |
| **size 재검증** | 룰 적용 후에도 ≥90%면 압축 거부 (룰 부족 신호), wrapper가 Discord alert |
| **silent 성공** | 정상 skip / 압축 성공은 stdout 출력 없음 (cron deliver=local) |
| **alert on fail** | exit code 2 (drift block) 또는 3 (룰 부족) 시 wrapper가 Discord 알림 |

## Drift 검증 도구 (companion)

```bash
python3 ~/.hermes/scripts/compression_drift_check.py
# → memory.md: 15 § facts
# → matched in state.db: 15
# → drift: 0.0%
# → verdict: pass — auto compression safe
```

**알고리즘** (단일공식 § 마커 기반):
1. `§` 마커 사이의 비어있지 않은 첫 줄 = 1 fact
2. 각 fact의 첫 단어를 state.db assistant messages에 LIKE 검색
3. 매칭 비율 = `matched / total`
4. `< 10%` 면 pass

**Pitfall — § 마커 파싱 버그**: 첫 줄은 카테고리 라벨 (예: `TZ:KST+9,...`)이라 1st fact이 카테고리 라벨로 잡힐 수 있음. 향후 `compression_drift_check.py` 자체 fix 필요 (자가개선 루프 task `t_af7197b4` 후보).

## 사용자가 정한 압축 우선순위

**자동 압축 가능 영역** (룰로 처리):
- wiki에 이미 있는 사실 (event log, 봇 ID, gateway fix)
- 약어 치환 (긴 표기 → 짧은 표기)
- 띄어쓰기 단축

**사용자 결정 영역** (자동 압축 금지):
- 메모리 § 단일공식 변경 (카테고리 라벨 첫 줄 + § 구분자 미사용)
- 압축 룰 추가 (룰이 부족할 때 사용자 확인 후 추가)
- 90% 미만으로 추가 압축 (사용자가 정한 임계치)

## Verify current state, never trust compaction numbers (LESSON 2026-07-07)

**반드시 지킬 것**: `wc -m ~/.hermes/memories/MEMORY.md`로 **현재 size를 직접 측정**. compaction context의 숫자를 신뢰하지 말 것.

왜? 2026-07-07 실제 사례:

```
이전 세션 compaction context: "memory 91.2%, 2,070 → 2,006 chars"
실제 측정: "memory 99.6%, 2,191/2,200 chars"
```

**원인 가설**: 이전 세션 terminal 출력의 stdout이 섞여 잘못된 환산이 compaction에 들어감. compaction 알고리즘은 conversation history 기반이라 측정값 자체를 verify하지 않음.

**Workflow**:
1. 압축 작업 시작 시 **반드시 `wc -m`로 현재 size 측정**
2. compaction context의 size/percentage를 **참고용**으로만 사용
3. 측정값이 context와 다르면 context는 stale, 측정값이 진실

## Multi-bot 인프라 정보 승격 사례

memory L17 (Bot IDs)에서 "채니봇=hermes(Linux,config.yaml+env), plan/ds=Mac launchd" 부분은 wiki 어디에도 없어서 memory 보존 결정. **승격 후** `~/.hermes/wiki/infra/bot-architecture.md`에 작성하고 memory에서 제거 가능.

**판단 기준**: 압축 후보 fact이 wiki INDEX 어디에도 없으면 **memory에서 절대 제거 금지**. wiki에 먼저 작성 후 압축.

## Cron 등록 recipe (canonical)

```bash
cronjob action=create \
  name="🧹 memory daily auto-compact (매일 06:30 KST, 사용자 룰: 90% 넘으면 자율 정리)" \
  schedule="30 21 * * *" \
  script="memory_daily_compact.sh" \
  no_agent=true \
  deliver="local"
```

**왜 `30 21 * * *` (UTC)**: KST 06:30 = UTC 21:30. cron은 UTC 기반.

**왜 `deliver="local"`**: silent 성공이 정상. fail (drift block, 룰 부족) 시에만 wrapper가 Discord alert. cron 자체는 항상 exit 0.

**왜 `no_agent=true`**: LLM-free wrapper라 결정론적 + 빠름 + 자가개선 루프의 alert_only 패턴과 일치.
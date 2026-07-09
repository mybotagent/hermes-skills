# System Audit Methodology (Hermes + GitHub 종합 진단)

> "현제 헤르메스 시스템과 github을 보고 가장 큰 문제점과 가장 필요한 것을 제시해줘" 류 요청에 대한 검증된 진단 방법.
> 2026-07-07 사용자 요청에서 실전 적용 → 단일 failure point (state.db), 메모리 본질 비효율, cron effectiveness 미측정 3가지 발견.

## 사용자 신호 — 이 워크플로우가 트리거되는 패턴

다음 키워드가 등장하면 system audit 모드 발동:
- "가장 큰 문제점", "가장 필요한 것", "문제 진단", "시스템 점검"
- "github 디스크 또는 코드에서 불필요한거 정리" (cleanup variant)
- "자율적으로 진단", "audit 해줘"

**Do NOT trigger on**:
- 단순 작업 요청 (먼저 작업 처리)
- "왜 이렇게 됐어" 류 retrospective (다른 워크플로우)

## Audit 차원 — 3가지 분리 측정

Hermes + GitHub 시스템은 본질적으로 **3가지 자원이 누적**되고, 각자 진단 방법이 다름:

```
[1] Disk usage      → "지금 디스크 뭐가 크고 뭐가 죽었나"
[2] Code/script     → "dead code, 중복, 90일 0회 사용"
[3] Cron            → "성공률, 출력 크기, 비용, 효과"
```

각 차원 독립 측정 후 종합 진단. 한 차원만 보면 잘못된 결론 (예: 디스크만 보고 "tmp_pack 정리" 권고 → 진짜 문제는 state.db 백업 부재).

## [1] Disk usage audit — 검증된 명령어

```bash
# 1a) 디렉토리별 사이즈 (top 15)
du -sh /home/ubuntu/.hermes/* 2>/dev/null | sort -rh | head -15

# 1b) 1MB 이상 큰 파일 (top 20)
find /home/ubuntu/.hermes -type f -size +1M -exec ls -lh {} \; 2>/dev/null | \
  awk '{print $5, $9}' | sort -rh | head -20

# 1c) Git 임시 pack 잔존 검사 (hermes-agent .git 안)
ls -la /home/ubuntu/.hermes/hermes-agent/.git/objects/pack/tmp_pack_* 2>&1 | head -10

# 1d) state.db + snapshot 비교
ls -la /home/ubuntu/.hermes/state.db /home/ubuntu/.hermes/state-snapshots/
```

**핵심 발견 패턴 (2026-07-07 실전)**:
- `hermes-agent/.git/objects/pack/tmp_pack_*` — git gc 누락, 100MB+ 잔존 5건 가능
- `state.db (275MB) + state-snapshots/ (235MB)` — 단일 파일 + 4일 전 snapshot
- `hermes-agent/node_modules + venv` — ~1.5GB (electron deps, 정상 범위)

**즉시 처리 가능 (자율)**:
- `cd hermes-agent && git gc --prune=now` (tmp_pack 정리, safe)
- 위 경고만 보고 (state.db는 user 결정 영역)

**Pitfall — 절대 자동 처리 금지**:
- state.db 삭제/vacuum (사용자 결정)
- snapshot 삭제 (복구 지점 손실)
- node_modules 정리 (실행 환경 깨짐 위험)

## [2] Code/script audit — 검증된 명령어

```bash
# 2a) 스크립트 사이즈 + 날짜 (오래된 것 = 의심)
ls -la ~/.hermes/scripts/ 2>&1 | awk '{print $5, $9}' | sort -rn | head -15
find ~/.hermes/scripts/ -name "*.py" -o -name "*.sh" 2>/dev/null | \
  xargs ls -la 2>/dev/null | sort -k6,7 | head -10

# 2b) 크론이 참조하지 않는 스크립트 (dead weight 후보)
hermes cron list 2>&1 | grep -oE "Script:[[:space:]]+\S+" | sort -u > /tmp/cron_scripts.txt
ls ~/.hermes/scripts/*.py ~/.hermes/scripts/*.sh 2>/dev/null | \
  xargs -n1 basename > /tmp/all_scripts.txt
comm -23 /tmp/all_scripts.txt <(sed 's|Script:[[:space:]]*||' /tmp/cron_scripts.txt | sort -u) \
  > /tmp/dead_candidates.txt
wc -l /tmp/dead_candidates.txt
```

**핵심 발견 패턴**:
- 스크립트 N개 중 cron 참조 M개 → (N-M)개는 dead weight 후보
- 단, **manual invocation 가능성** 때문에 **보고만, 자동 삭제 금지**
- 사용자가 "정리해" 명시 시에만 처리

**Skill 사용 빈도 (별도 측정, idle hygiene Step 1e 참조)**:
- `state.db`의 `messages.tool_name='skill_view'` LIKE 검색
- 90일 윈도우
- (cron_used ∪ 90d_skill_view_used) = used; complement = uninstall 후보
- **NEVER auto-uninstall** — report only

## [3] Cron effectiveness audit — 검증된 명령어

```bash
# 3a) cron 전체 상태 (성공/실패/마지막 실행)
hermes cron list 2>&1 | head -100

# 3b) last_status/last_run_at 분포
hermes cron list 2>&1 | grep -E "Last run|last_status" | head -30

# 3c) cron-script-output 사이즈 추적 (각 cron이 stdout에 뭐 얼마나 뱉는지)
# - state.db의 messages에서 cron_jobs 로그 검색
sqlite3 ~/.hermes/state.db \
  "SELECT tool_name, COUNT(*) FROM messages
   WHERE timestamp > strftime('%s','now','-7 days')
   GROUP BY tool_name ORDER BY 2 DESC LIMIT 20;"
```

**핵심 발견 패턴 (2026-07-07 실전)**:
- 17개 cron 가동 중이지만 **각 cron의 "효과" 측정 메타 cron 없음**
- `last_run: ok`만으로는 의미 없음 — 출력이 비어있어도 ok
- 해결책: cron effectiveness metric cron (자가개선 루프 영구화 후보)

**즉시 처리 가능 (자율)**:
- cron `deliver=local` silent 성공은 OK (재정비 불필요)
- 명백한 deliver mismatch는 `cron-delivery-routing` skill로 fix
- 효과 측정 자체는 **사용자 결정** (P1 task)

## 종합 진단 — 3가지 영역 결과 합성

각 차원 결과를 종합할 때 **3-tier 우선순위**:

| Tier | 정의 | 예시 |
|------|------|------|
| **P0 (즉시)** | 단일 failure point, 데이터 손실 위험 | state.db 백업 부재, tmp_pack 누적 |
| **P1 (단기)** | 반복 비용/노이즈, 개선 효과 명확 | cron effectiveness 미측정, memory 본질 비효율 |
| **P2 (장기)** | 아키텍처 진화 필요 | state.db → distributed, tool-as-memory |

**사용자 보고 포맷**:

```
## 🔍 시스템 종합 진단 (YYYY-MM-DD)

### 가장 큰 문제점 (P0/P1/P2)
[P0] 단일 failure point — state.db (275MB) + snapshot 4일 전
[P1] 메모리는 50% 도달했지만 본질적 비효율 그대로
[P1] cron effectiveness 미측정 = 거짓 자율

### 가장 필요한 것
1. State.db 무결성 (자동 backup)
2. Tool-as-Memory (memory.md = key만, 본문은 tool로)
3. Cron effectiveness metric (메타 자가개선)

### 사용자 결정 영역
- memory 0%로 줄일지 (tool-as-memory 전환)
- state.db 자동 vacuum 정책
- cron retirement 룰

### 즉시 처리 가능 (자율)
1. git gc (tmp_pack 정리) ✅ done
2. memory 압축 cron 가동 확인 ✅ verified
3. cron health metric P1 task 자동 생성
```

## Pitfalls

**Compaction context 신뢰 금지 (added 2026-07-07)**: 이전 compaction에서 본 size/숫자는 stale일 수 있음. **disk/script/cron audit 결과는 항상 명령어로 직접 측정**. memory size는 `wc -m`, cron list는 `hermes cron list`, 디스크는 `du -sh`. 측정값이 진실.

**Audit 결과를 보고만 할지, 즉시 처리할지 경계** (added 2026-07-07):
- **즉시 처리 가능**: git gc (safe), lint pass (read-only), 보고용 스크립트 작성
- **보고만**: state.db/snapshot 변경, dead script 삭제, cron retirement, memory 본질 변경
- **사용자 명시 요청 시에만**: 모든 git push, 외부 시스템 변경

**단일 차원 audit 금지** (added 2026-07-07): 디스크만 보면 "tmp_pack 정리"가 답으로 보임. 하지만 진짜 P0는 state.db 백업 부재. **3가지 차원 모두 측정 후 종합**.

**"시스템이 크다" ≠ "정리 대상"**: node_modules (1.5GB), venv (수백 MB)는 정상 범위. **삭제하면 실행 환경 깨짐**. audit에서 "큰 파일" 발견 시 즉시 삭제 ❌, 의존성 그래프 확인 후 결정.

**사용자 결정 보류 영역 식별**: "다음 idle 시 자동 처리 가능" vs "사용자 결정 영역"을 명확히 분리. 섞어서 보고하면 사용자가 자율 운영 범위를 잘못 이해함.

## 검증된 audit 결과 예시 (2026-07-07)

실제 진단 결과:

**P0**:
- `state.db` (275MB) + `state-snapshots/` (235MB, 4일 전) — 단일 failure point
- `hermes-agent/.git/objects/pack/tmp_pack_*` 410MB 잔존 — git gc 누락

**P1**:
- 17 cron 가동 중이나 각 cron의 효과 측정 메타 cron 없음
- memory 50% 도달했지만 본질은 매 세션 inject 동일

**P2**:
- state.db 분산 backup 없음
- tool-as-memory 미구현 (memory.md = 본문 들고 있음)

**즉시 처리 (자율)**:
- `git gc --prune=now` → tmp_pack 4건 × 100MB 삭제 ✅

**보고만 (사용자 결정)**:
- state.db 자동 backup 정책
- memory 0% (tool-as-memory) 전환
- cron retirement 룰
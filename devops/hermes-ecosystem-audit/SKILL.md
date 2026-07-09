---
name: hermes-ecosystem-audit
description: "헤르메스 생태계 종합 감사 — 26개 GitHub 레포, 114개 스킬, 55개 위키 페이지, 17개 스크립트, cron, 메모리를 정량 측정하여 over-engineering, code smell, legacy, dead code, SSoT 위반을 발견. P/I/E/R + HIGH/MEDIUM/LOW severity 분류 + 5-stage verify 기반."
version: 1.0.0
author: 채니봇
platforms: [linux, macos]
metadata:
  hermes:
    tags: [audit, system-review, over-engineering, code-smell, legacy, dead-code, ssot, hermes]
    related_skills: [code-audit-fix-pack, wiki-save, meeting-documentation]
---

# Hermes Ecosystem Audit Skill

> **헤르메스 운영 자산 전체를 정량적으로 감사**하는 workflow.
> 26개 GitHub 레포 + 114개 스킬 + 55개 위키 페이지 + 17개 스크립트 + cron + 메모리
> → **over-engineering, code smell, legacy, dead code, SSoT 위반** 발견 + severity 분류 + 권장 액션.

## 🎯 언제 쓰나 (When to Use)

Trigger keywords:
- "헤르메스 관리한거 평가해줘"
- "전반적으로 분석해줘" + (코드/시스템/자산/아키텍처)
- "오버엔지니어링 있는지"
- "불필요한 코드/문서/legacy 있는지"
- "code sanity / 코드스멜 검사"
- "감사 / audit"

> 1회 전체 감사는 **30-60분** 소요. 정기적으로 (월 1회) 실행 권장.

## 📐 Audit Dimensions (5-Stage Verify 기반)

| 차원 | 측정 항목 | 발견 카테고리 |
|:-----|:---------|:-------------|
| **Inventory** | 정량 카운트 (repos/skills/wiki/scripts/cron/memory) | 정량 baseline |
| **Code Quality** | TODO/FIXME, hardcoded path, magic number, |HIGH/MEDIUM/LOW |
| **Duplication** | 동일 기능 스크립트 2+ | legacy, dead code |
| **SSoT** | 동일 데이터가 2+ 위치 | violation |
| **Over-Engineering** | 약속 ≠ 실행, 사용 빈도 < 구축 비용 | over-engineering |
| **Validation Gap** | 5-stage verify 마지막 단계 누락 | promises without proof |
| **Self-Improvement** | 자기개선 loop 작동 여부 (incident 자동 fix) | ✅/⚠️/❌ |

## 🔍 Audit Procedure (8 steps)

### Step 1: 정량 인벤토리 (5분)

```bash
# GitHub repos
curl -s -H "Authorization: token $(grep 'mybotagent:' ~/.git-credentials | sed 's|https://mybotagent:||; s|@github.com||')" \
  'https://api.github.com/user/repos?per_page=100&visibility=all&affiliation=owner' \
  | python3 -c "import sys, json; d=json.load(sys.stdin); print(f'Total: {len(d)}')"

# Local mirrors + freshness
for d in ~/*/; do
  [ -d "$d/.git" ] && echo "$d: $(git -C $d log -1 --format='%ci')"
done

# Wiki pages
find ~/.hermes/wiki -name '*.md' -not -path '*/logs/*' -not -path '*/raw/*' | wc -l

# Skills
find ~/.hermes/skills -name 'SKILL.md' | wc -l

# Scripts
ls -la ~/.hermes/scripts/

# Cron
crontab -l | grep -v '^#' | grep -v '^$'

# Disk
du -sh ~/.hermes/
```

### Step 2: Code Quality Scan (10분)

```bash
# TODO/FIXME/HACK
grep -rE 'TODO|FIXME|XXX|HACK' ~/.hermes/scripts/ ~/trade-pipeline/ --include='*.py' --include='*.sh'

# Hardcoded paths (portability smell)
grep -lE '/home/ubuntu' ~/.hermes/scripts/* 2>/dev/null

# Tiny scripts (potential dead code)
for f in ~/.hermes/scripts/*; do
  size=$(stat -c%s "$f")
  [ "$size" -lt 500 ] && echo "TINY: $f ($size bytes)"
done
```

### Step 3: Duplication Detection (10분)

```bash
# Hash-based dedup
md5sum ~/.hermes/scripts/*.sh | sort | awk '{print $1}' | uniq -d

# Duplicate names across locations
find ~ -name 'memory_sync.sh' -o -name 'wiki_reindex.sh' -o -name 'memory_alert.sh' 2>/dev/null

# Canonical version check (script appears in 2+ places)
for s in $(ls ~/.hermes/scripts/); do
  if [ -f ~/hermes-self-healing/scripts/$s ]; then
    diff -q ~/.hermes/scripts/$s ~/hermes-self-healing/scripts/$s
  fi
done
```

### Step 4: SSoT Verification (5분)

```bash
# Watchlist (must be symlink, not copy)
ls -la ~/trade-pipeline/data/watchlist.json ~/trade-pipeline/langgraph/data/watchlist.json

# Config duplication
find ~ -name 'config*.yaml' 2>/dev/null | head -10
find ~ -name 'config*.json' 2>/dev/null | head -10
```

### Step 5: Over-Engineering Detection (15분)

각 자산에 대해:
- **질문 1**: "이 자산은 사용되는가?" (frequency: weekly/daily/monthly/never)
- **질문 2**: "약속한 대로 작동하는가?" (validate: 실제 실행/측정)
- **질문 3**: "구축 비용 vs 사용 가치" (ROI)

```bash
# Skill usage stats
cat ~/.hermes/skills/.usage.json 2>/dev/null | python3 -c "
import sys, json
d = json.load(sys.stdin)
used = [k for k,v in d.items() if v.get('use_count', 0) > 0]
print(f'Tracked: {len(d)}, Used: {len(used)}, Never: {len(d)-len(used)}')
"

# Submodule dirty (promised but not committed)
cd ~/.hermes/wiki && git submodule foreach 'echo "$name: dirty=$(git status --porcelain | wc -l)"'

# Cron active count
crontab -l | grep -v '^#' | grep -v '^$' | wc -l
```

### Step 6: Validation Gap Analysis (10분)

- **약속한 파일/스크립트가 실제로 존재하는가?**
  ```bash
  # Example: memory_alert.sh mentioned in wiki but exists?
  ls -la ~/.hermes/scripts/memory_alert.sh
  ```
- **위키/README에서 언급된 모든 파일/명령이 실제로 작동하는가?**
- **5-stage verify의 마지막 "validate" 단계가 누락된 곳은?**

### Step 7: Severity Classification (P/I/E/R)

각 발견을 P/I/E/R 형식으로:

| P (Problem) | I (Impact) | E (Evidence) | R (Recommendation) |
|:------------|:-----------|:-------------|:-------------------|
| 무엇이 문제인가 | 영향 범위 (HIGH/MEDIUM/LOW) | 파일/라인/해시 | 권장 fix |

### Step 8: Report 작성 + Action Plan

`architecture/YYYY-MM-DD-system-audit.md` 형식:

```markdown
# Hermes Ecosystem Audit — YYYY-MM-DD

## 정량 인벤토리
| 자산 | 수량 | 활성도 | 위치 |

## 발견 사항
### 🔴 HIGH (N건)
### 🟡 MEDIUM (N건)
### 🟢 LOW (N건)

## 오버엔지니어링 분석
(상위 5건)

## 강점 / 약점 정직 평가

## 권장 액션 (우선순위 + 비용)
| # | 액션 | 효과 | 비용 |

## 후속 작업
- 즉시 / 이번 주 / 다음 주
```

## 🚨 Critical Patterns (이번 감사에서 발견한 패턴)

### 1. **Triptych Duplication** (3중 중복)
- 같은 기능의 스크립트가 3개 (md5 다름 → 진짜 중복, 단순 symlink 아님)
- **예**: Neo4j health check (cron_health.sh / neo4j_health.sh / neo4j-health-check.sh)
- **Fix**: 가장 명확한 이름 1개만 유지

### 2. **Two-Version Drift** (포크 후 동기화 안 됨)
- 같은 스크립트가 2개 위치 (live + GitHub repo)에 있지만 서로 다름
- **예**: self_healing_watchdog.sh (live 8,641B vs repo 5,897B)
- **Fix**: live 버전을 canonical로 push

### 3. **Promised but Absent** (약속 ≠ 실행)
- 위키/README/메모리에 언급되었지만 실제 파일 없음
- **예**: memory_alert.sh (위키 언급, 파일 없음), hermes-pipeline-scripts (메모리 언급, repo 없음)
- **Fix**: 5-stage verify의 validate 단계 — 실제 존재 확인

### 4. **Submodule Dirty** (서브모듈 미커밋)
- logs/ 같은 submodule에 uncommitted changes 24h+
- **예**: logs/2026/2026-07-03-0025.md
- **Fix**: 즉시 commit + push

### 5. **SSoT Hidden by Symlink** (단일 소스이긴 한데 발견 어려움)
- watchlist.json이 symlink로 단일화됐지만, 처음 보는 사람은 2개로 보임
- **좋은 패턴**: 단일 소스. **개선**: README에 명시

## 🛠️ Tool Integration

이 skill은 다음 도구와 함께 사용:
- `code-audit-fix-pack` — P/I/E/R + atomic fix commit
- `wiki-save` — 감사 보고서 저장
- `meeting-documentation` — 감사 결과 회의록 (3자 회의)
- `kanban-orchestrator` — 발견된 fix를 task로 등록

## 📊 Output Template

```markdown
# Hermes Ecosystem Audit — YYYY-MM-DD

> Method: 5-stage verify + P/I/E/R
> Scope: 전체 헤르메스 운영 자산
> Verdict: 운영 능력 [HIGH/MEDIUM/LOW] / 자산 정리 [URGENT/NICE] / 오버엔지니어링 [N건] / 중복·legacy [N건]

## 📊 정량 인벤토리 (DATE 측정)
[표]

## 🚨 발견 사항 (HIGH / MEDIUM / LOW)
[HIGH N건, MEDIUM N건, LOW N건]

## 🏗️ 오버엔지니어링 분석 (상위 5건)
[OE1-OE5]

## ✅ 잘 한 것 (강점 N건)

## ⚠️ 정직 평가: 약점 N건

## 🎯 권장 액션 (우선순위 + 비용)
[표]

## 🔗 후속 작업
- 즉시 / 이번 주 / 다음 주
```

## 💡 Examples

### 2026-07-03 첫 감사 (이 skill의 첫 적용)
- 26 repos / 114 skills / 55 wiki / 17 scripts / 1 cron
- **HIGH 4건**: Neo4j health check 3중 중복, self_healing 2-version drift, memory_alert.sh 부재, weekly_screener 미참조
- **MEDIUM 6건**: langraph 오타 레포, hermes-pipeline-scripts 부재, logs submodule dirty, memory 경로 불명, 큰 wiki 페이지, architecture 비대
- **LOW 4건**: 4.2GB 디스크, 미사용 50% 스킬, README emoji, trade-pipeline 적정선
- **OE 5건**: GraphRAG 4-Layer, self-healing 과잉, 114 skills, 26 repos, memory_alert/sync/reindex 3 scripts
- **강점**: 단일공식 일관성, SSoT, 위키-스킬-메모리 3-Layer, self-healing 실작동
- **약점**: 검증 < 약속, 4.2GB 비효율, 3:1 dead 스킬, 중복 스크립트 5건

## 🔄 정기 감사 권장 주기

| 차원 | 권장 주기 |
|:-----|:---------|
| **Quick check** (cron + dead scripts + submodule dirty) | 주 1회 |
| **Standard audit** (위 8 step) | 월 1회 |
| **Deep audit** (GraphRAG 평가, OE 분석) | 분기 1회 |

## 5-Stage Verify 적용

이 skill 자체가 5-stage verify method를 따름:
- **why**: 자산 비대화 + dead code 누적 → 정기 청소 필요
- **what**: 정량 카운트 + 발견 severity 분류
- **whether**: 측정 옳은가 (각 발견에 P/I/E/R + 증거)
- **what**: 진짜 무엇을 fix (HIGH 우선)
- **how**: 어떻게 fix (atomic, symlink, 단일화, SSoT)
- **validate**: `ls-remote` + `bash -n` + symlink 검증

## References

- `references/first-audit-findings-2026-07-03.md` — 첫 감사의 실제 측정 데이터 (baseline). 다음 감사 시 비교 기준.
- `references/kanban-autonomous-cleanup.md` — 자율 모드 Kanban 정리 workflow (2026-07-07 round 1+2 검증). cron skills 추출, 90일 skill_view 빈도 측정, dup/false-positive close 패턴, memory_alert.py 사례.
- `references/disk-and-script-cleanup-2026-07-07.md` — 디스크 회수 (~4.3GB) + cron NEVER-실행 판정 + orphan script detection 검증된 절차.

## 🆕 Disk + Cron + Script Cleanup Patterns (2026-07-07 검증)

### Disk 회수 우선순위 (가장 효과 큰 순)

| 대상 | 회수량 | 명령 | 안전성 |
|---|---|---|---|
| `~/.cache/pip` | ~2.5GB | `pip cache purge` | ✅ 항상 안전 (재설치 가능) |
| `~/.cache/uv` | ~1.4GB | `uv cache clean` | ✅ 항상 안전 |
| `state.db-wal` | ~280MB | `sqlite3 state.db "PRAGMA wal_checkpoint(TRUNCATE)"` | ✅ 활성 DB 안전 |
| state-snapshots state.db | ~140MB | `gzip state.db` 후 원본 삭제 | ⚠️ snapshot은 pre-update 롤백용 |
| state.db vacuum | ~7MB | `sqlite3 state.db "VACUUM"` | ✅ 활성 DB 안전 |
| `~/.cache/{camoufox,puppeteer,playwright}` | ~2.3GB | 수동 삭제 | ⚠️ 재다운로드 필요 |

**총 자동 회수 가능**: ~4.3GB (위 5개).

**절대 삭제 금지**:
- 활성 `state.db` (세션 히스토리)
- `state-snapshots/*` 디렉토리 (롤백 백업)
- `hermes-agent/.git/`, `hermes-agent/venv/` (코드 + 의존성)
- `~/.local/share/` (설치된 패키지)

### Cron "NEVER 실행" 판정 (가장 흔한 함정)

`hermes cron list` 출력에서 `Last run: NEVER` ≠ 항상 고장. **반드시 미래 scheduled 여부 확인**:

```python
import re, datetime
text = open('/tmp/cron_list.txt').read()
# Schedule 파싱
m_schedule = re.search(r'Schedule:\s+(.+)', block)
m_next = re.search(r'Next run:\s+(\S+)', block)
```

판정 규칙:
1. **next_run > now (미래)** → 정상 (방금 등록했거나 주/월 1회)
2. **next_run < now (과거) + NEVER** → ❌ 진짜 실패 (조사 필요)
3. **반복 일정 + 미래 scheduled + 절대 안 도래** → ❌ 미스케줄 (e.g., 매월 31일)

**Pitfall**: 등록한 지 24시간 이내 cron은 last_run=NEVER가 정상. 즉시 "고장"으로 close하지 말 것.

### Orphan Script Detection (검증된 절차)

```bash
# 1. cron이 참조하는 script 목록 추출
grep -oE 'Script:\s+\S+\.(py|sh)' /tmp/cron_list.txt | awk '{print $2}' | sort -u > /tmp/cron_scripts.txt

# 2. 디렉토리 전체 script 목록
ls ~/.hermes/scripts/ > /tmp/all_scripts.txt

# 3. diff → cron_scripts에 없으면 orphan 후보
diff /tmp/cron_scripts.txt /tmp/all_scripts.txt

# 4. 각 orphan 후보에 대해 cross-reference:
#    - grep -rn "script_name" ~/.hermes/skills/  → skill에서 호출?
#    - ls ~/.local/bin/  → PATH에서 호출?
#    - 다른 cron이 wrapper로 호출?
```

**판정**: cross-reference 없으면 삭제. 있으면 보존.

**2026-07-07 검증 결과**: 35 scripts 중 orphan 13개 → 실제 삭제 가능 3개 (10개는 skill에서 사용).

### Script Supersede 패턴 (구 → 신 자동 정리)

신규 스크립트가 구 버전을 대체하면 **구 버전 즉시 삭제**:

| 사건 | 행동 |
|---|---|
| `memory_query.py` 생성 | `memory_lazy_fetch.py` 즉시 삭제 |
| `nginx` 도입 | `dashboard_proxy.py` (Python 대안) 삭제 |
| 테스트 완료 | `auto_merge_smoke_test.sh` (1회용) 삭제 |

**체크리스트**: 새 스크립트 추가 시 "기존 동일 기능?" 자동 확인 → 있으면 구것 삭제.

### 메모리 본질 변경 패턴 (Tool-as-Memory)

**memory.md = 본문 → key only**로 재설계. 본문은 별도 tool/skill로 lazy fetch.

| 단계 | 결과 |
|---|---|
| Before | memory.md 2,191 chars (99.6%) |
| After | memory.md 306 chars (13.9%) — KEY만 |
| 본문 접근 | `python3 ~/.hermes/scripts/memory_query.py <key>` → 위키 페이지 자동 fetch |
| Skill 등록 | `~/.hermes/skills/memory-query/SKILL.md` |

**적용 트리거**: memory가 50%+ 차지할 때 (본질은 매 세션 100% inject된다는 사실).

**상세 reference**: `references/memory-tool-as-memory.md`.

## Related

- [code-audit-fix-pack] — 코드 sanity audit (이 skill의 code quality 부분)
- [bash-script-template] — fix 적용 시 bash script 표준
- [wiki-save] — 감사 보고서 영속화
- [meeting-documentation] — 감사 결과를 3자 회의로 리뷰
- [architecture/ssot-single-source-of-truth.md] — SSoT 원칙
- [architecture/hermes-memory-pipeline.md] — OE1 (GraphRAG) 분석 대상

## 🔑 User-Discovered Workflow Preferences (2026-07-03)

사용자가 직접 명시한 운영 선호 (이 skill 적용 시 따를 것):

1. **자율 작업 모드**: "알아서 작업해주고 나잘테니까" (aiprofit, 2026-07-03 마지막 메시지)
   - 결과 보고만 깔끔하게. 중간 과정 질문 최소화
   - 한 번의 큰 작업 (감사 + 스킬화) 끝까지 실행 후 보고
   - 5-stage verify 자체 검증 후 보고
2. **한국어 보고**: 소통은 한국어 (aiprofit 기본)
3. **단일 보고**: 작업 끝나면 한 번에 정리. "지금 하고 있어요" 같은 중간 알림 자제
4. **신호=실행**: "이 과정을 스킬로 만들어줘" → audit + skill 둘 다 즉시 완성 (한 사이클로)

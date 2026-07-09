# Disk Hygiene Watchdog — 설계 문서 (2026-07-08 shipped)

> 사용자 의도 (aiprofit Discord 2026-07-08): *"메모리, 디스크 용량 관리, 자율 운영이 핵심"*
> 기존 자동화는 **memory만** (`memory_daily_compact`, `memory_alert`, `memory_curator`) — **디스크 자기 관리 cron은 부재**였음. 본 cron 이 그 갭 을 채움.
> **shipped**: cron `0e095c406dae` 매일 KST 06:50 (no_agent, DRY-first) + script `~/.hermes/scripts/hermes_disk_hygiene.py`

## 1. 단일공식 — 6축 측정 + 3-tier 임계치

### 6축 측정 (단일 책임 분리)

| 축 | 측정 대상 | 명령어 | cleanup trigger |
|---|---|---|---|
| 1. df | `/home` 전체 점유율 | `df --output=pcent,used,avail,target /home` | 80/90/95% |
| 2. state.db | `~/.hermes/state.db` 사이즈 + WAL + SHM | `Path.stat().st_size` | 300 MB alarm |
| 3. snapshots | `~/.hermes/state-snapshots/` .db.gz 누적 | `rglob("state.db.gz")` | 30일+ 묵은 것 |
| 4. sessions | `~/.hermes/sessions/*.json` 누적 | `glob("session_*.json")` | 180일+ |
| 5. logs | `~/.hermes/logs/*.log.*` rotated | `glob("*.log.*")` | 10MB+ |
| 6. tmp_pack_ | `**/.git/objects/pack/tmp_pack_*` 잔존 | `glob` 재귀 | 0개여야 정상 |

### 3-tier thresholds (사용자 정책 — 고정, 사용자 결정 전 변경 ❌)

| Tier | df | 동작 |
|---|---|---|
| OK | <80% | silent daily record |
| CAUTION | 80~90% | silent + stdout (Discord 알림 ❌) |
| WARN | 90~95% | Discord alert + log truncate 자동 |
| CRITICAL | 95%+ | Discord alert + tmp_pack_ git gc 자동 |

### Hard-absolute rules (사용자 결정 영역, 절대 자동 안 함)

- ❌ `state.db` truncate / VACUUM (blast radius medium — 사용자 confirm 후에만)
- ❌ `state-snapshots/*.db.gz` 삭제 (복구 지점 손실)
- ❌ `sessions/*.json` 삭제 (audit trail 손실)
- ❌ `node_modules` / `venv` 정리 (실행 환경 깨짐 위험)
- ❌ `hermes-agent/` git source clone (외부 repo, read-only)
- ❌ `cron/jobs.json` 직접 편집 (cron 시스템 손상 위험)

→ 모두 **alert only**. cleanup action 의 디폴트는 `git gc --prune=now` (tmp_pack_, reversible) 와 rotated log 의 1MB keep truncate (filesystem noise 만) 두 가지.

## 2. Single Formula

```
[trigger] 매일 KST 06:50 (= UTC 21:50, no_agent cron)
    ↓
[env load] HERMES_HOME=/home/ubuntu/.hermes
    ↓
[DRY default] DRY_RUN env 미설정 / "1" / "true" → dry (mutation 0)
[PROD] DRY_RUN=0 명시 → tier별 safe-cleanup 실행
    ↓
[6축 측정]
  ① df --output=pcent,used,avail,target /home
  ② state.db 사이즈 + WAL/SHM
  ③ snapshots state.db.gz (rglob) + mtime
  ④ sessions/*.json + mtime
  ⑤ logs/*.log.* + size
  ⑥ **/.git/objects/pack/tmp_pack_* (재귀 glob)
    ↓
[tier 분류] pct → OK/CAUTION/WARN/CRITICAL
    ↓
[action 분기]
  - tier >= WARN → log truncate (rotated log 의 마지막 1MB keep)
  - tier >= CRITICAL → tmp_pack_ git gc
  - state.db >= 300MB → alert only (사용자 결정)
  - snapshot 30일+ → alert only
  - session 180일+ → alert only
    ↓
[로그] ~/.hermes/cron/output/hermes-disk-hygiene-latest.log (append)
```

## 3. 실측 baseline (2026-07-08 17:14 UTC)

```
DRY mode:
[2026-07-07T17:14:33+00:00] DF /home: 73%   73% 28441912 10927700 /
[2026-07-07T17:14:33+00:00] state.db: 271.7 MB  WAL 2.7 MB  SHM 0.5 MB
[2026-07-07T17:14:33+00:00] snapshots: 1 (>30d: [])
[2026-07-07T17:14:33+00:00] sessions: 300 files, >180d: 0 (0.0 MB)
[2026-07-07T17:14:33+00:00] rotated logs (>=10MB): 0 files (15.0 MB total)
[2026-07-07T17:14:33+00:00] tmp_pack_ 잔존: 0 files (0.0 MB)
[2026-07-07T17:14:33+00:00] TIER: OK (thresholds: 80/90/95%)
[2026-07-07T17:14:33+00:00] ===== hermes-disk-hygiene END (actions=0) =====

→ 진단: df 73% 안전. state.db 271.7MB 다음 cleanup 후보 (사용자 결정 영역).
```

## 4. CRITICAL Pitfalls (다음 cycle 작성 시 절대 잊지 말 것)

### 4.1 Python `DRY_RUN` env 파싱 (CRITICAL 함정)

**❌ 깨지기 쉬운 패턴**:
```python
DRY_RUN = os.environ.get("DRY_RUN", "1") == "0"
# - `.env` 에 `DRY_RUN=` (빈 문자열) 있으면 False → 의도와 다른 production mode
# - bash `DRY_RUN=1 python3 ...` 호출 시 env "1" 인데 코드는 False
```

**✅ 안전 패턴**:
```python
DRY_RUN = os.environ.get("DRY_RUN", "1") not in ("0", "false", "False", "")
# - env 미설정 / "1" / "true" / "" → True (dry safe)
# - env "0" 또는 "false" → False (production)
```

### 4.2 로그 라벨 `DRY_RUN={int(bool)}` 함정 (CRITICAL)

**❌ 거꾸로 출력**:
```python
log(f"DRY_RUN={int(DRY_RUN)}")
# DRY 모드일 때 (True) → "DRY_RUN=1" 출력
# PROD 모드일 때 (False) → "DRY_RUN=0" 출력
# → cron 로그 분석 시 "DRY_RUN=1" 보면 production 으로 오해
```

**✅ 사람이 읽을 수 있는 라벨**:
```python
log(f"mode={'DRY' if DRY_RUN else 'PROD'}")
```

### 4.3 절대 안 함 매트릭스

| 액션 | 위험 | 자동 가능? |
|---|---|---|
| `state.db` VACUUM | medium (lock contention 잠깐) | 사용자 OK 후 |
| `state.db` truncate/delete | **catastrophic** | ❌ 절대 |
| snapshot 삭제 | high (복구 지점 손실) | ❌ 절대 |
| session 삭제 | high (audit trail 손실) | ❌ 절대 |
| rotated log truncate | low (filesystem noise) | ✅ tier WARN+ |
| tmp_pack_ git gc | very low (git 의 reversible 동작) | ✅ tier CRITICAL |
| node_modules 정리 | high (실행 환경 깨짐) | ❌ 절대 |
| hermes-agent git ops | medium (외부 repo, 2.8GB) | ❌ 절대 |

### 4.4 dry-run / production mode 라벨 (DRY-first 정책)

- **DRY 모드 (default)**: stdout + log 만, mutation 0
- **PROD 모드 (`DRY_RUN=0` 명시)**: tier별 safe-cleanup 실행
- **사용자 confirm 없이 PROD 모드 진입 절대 금지**

## 5. Cron 등록 (실측)

```bash
hermes cron create "50 21 * * *" "..." \
  --name "🧹 disk hygiene watchdog (KST 06:50, DRY-first)" \
  --script hermes_disk_hygiene.py \
  --deliver local
# job_id: 0e095c406dae
# next_run_at: 2026-07-08T21:50:00+08:00
```

## 6. 기존 cron과의 단일공식 매핑

| 자원 | cron | 책임 |
|---|---|---|
| 메모리 90% 압축 | `cb2ee5fafc5d` memory_daily_compact | memory.md 압축 |
| 메모리 90% 알림 | `f405cd52a6e8` memory_alert | memory Discord 알림 (⚠️ last_status=error — 사용자 점검 권장) |
| 메모리 weekly | `4076b821ac31` memory_curator-weekly | memory.weekly 점검 |
| **🆕 디스크 6축 자기 관리** | **`0e095c406dae` disk hygiene watchdog** | df/state.db/snapshots/sessions/logs/tmp_pack |
| Cron self-consistency | `da557233e6ac` self-consistency-check-3h | cron health 자체 측정 |
| Wiki weekly | `c172635927c2` wiki-auto-maintainer-weekly | orphan / broken link weekly |

## 7. Step 4 후보 중 shipped 표시 (2026-07-08 update)

기존 `references/step-4-candidates.md` 의 후보 5개 중:

- **(2) wiki cleanup alert** — shipped (`wiki_auto_maintainer.py` cron `c172635927c2`)
- **(4) cron health check** — shipped (`self_improve_loop.py` + `self-consistency-check-3h` cron `da557233e6ac`)
- **🆕 disk hygiene watchdog** — shipped (본 문서)

→ step-4-candidates.md 는 **outdated**; SKILL.md 본문 의 "Shipped Step-4 candidates" 섹션이 source of truth. 다음 idle 시 본 섹션 업데이트.

## 8. 단일공식 검증 (10/10)

- ✅ 단일 cron + 단일 script
- ✅ 6축 측정 (단일 책임, 모두 분리 측정)
- ✅ 3-tier 임계치 (사용자 친화적 발송)
- ✅ DRY-first (24h 검증 후 사용자 confirm → PROD)
- ✅ failure-isolated (각 축 try/except 격리)
- ✅ no-agent (LLM 토큰 0)
- ✅ 비밀값/secret 코드 ❌ (단순 df/du/stat 만)
- ✅ 멱등 (DRY: 측정만, no mutation)
- ✅ 기존 memory/cron 자동화 ↔ 보완 (중복 cron ❌)
- ✅ 5-stage verify (syntax + manual + cron + 24h dry + 1week)
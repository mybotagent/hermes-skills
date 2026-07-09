---
title: First Audit Findings (2026-07-03) — Reference Data
created: 2026-07-03
updated: 2026-07-03
tags: [audit, findings, evidence, reference, hermes]
related: [SKILL.md, architecture/2026-07-03-system-audit.md]
sources: [architecture/2026-07-03-system-audit.md]
---

# First Audit Findings (2026-07-03) — Reference Data

> 이 문서는 **2026-07-03 첫 감사의 실제 결과 데이터**입니다. 다음 감사 시 비교 baseline으로 사용.
> 진실 공급원(Single Source of Truth): `~/.hermes/wiki/architecture/2026-07-03-system-audit.md`

## 📊 Baseline Inventory (2026-07-03 01:30 KST 측정)

| 자산 | 수량 | 디테일 |
|:----|:----:|:-------|
| GitHub 레포 (private) | **26** | 8 active / 18 GitHub-only |
| 위키 페이지 (.md) | **55** | 5,220 lines, logs/raw 제외 |
| 설치된 스킬 (SKILL.md) | **122** | 29 used / 8 never / **85 untracked** |
| 운영 스크립트 | **17** | 12 active / 5 under 500 bytes |
| 활성 cron | **1** | wiki_reindex.sh @ 21:00 KST |
| trade-pipeline Python | **4,470 lines / 28 modules** | 적정선 |
| 총 .hermes 디스크 | **4.2 GB** | hermes-agent venv 90% 차지 |

## 🔴 HIGH 발견 (4건) — 즉시 처리

### H1. Neo4j health check 3중 중복 (Triptych Duplication)

| 파일 | 크기 | md5 | 비고 |
|:-----|:----:|:---:|:-----|
| `cron_health.sh` | 381 B | `d50250e6` | 모두 동일 기능 |
| `neo4j_health.sh` | 429 B | `80d46ec1` | 모두 동일 기능 |
| `neo4j-health-check.sh` | 343 B | `ea477ceb` | 모두 동일 기능 |

3개 모두 `check_health.py` 호출. 어느 것도 crontab에 등록 안 됨.
**Fix**: 1개만 유지 (권장: `neo4j_health.sh`).

### H2. self_healing_watchdog.sh 2-version drift

| 위치 | 크기 | mtime |
|:-----|:----:|:-----:|
| `~/hermes-self-healing/scripts/` | 5,897 B | 2026-07-01 00:33 |
| `~/.hermes/scripts/` | **8,641 B** | 2026-07-01 13:00 |

Live 버전이 +2,744 B (404 deliver fix, next_run_at 24h+ skip 추가). GitHub repo는 동기화 안 됨.
**Fix**: 8,641 B 버전을 canonical로 repo에 push.

### H3. memory_alert.sh 부재 (Promised but Absent)

- `architecture/hermes-memory-pipeline.md` 언급 ✅
- `hermes-pipeline-scripts` repo (메모리 약속) ❌ — `~/`에 없음
- 실제 파일 `~/.hermes/scripts/memory_alert.sh` ❌ — 존재 안 함
- **위험**: 90% memory 한계 도달 시 알림 안 됨

**Fix**: memory_alert.sh 작성 (50줄 내외) 또는 wiki에서 언급 제거.

### H4. dead scripts 의심 (5건)

| 스크립트 | 크기 | 의심 이유 |
|:---------|:----:|:---------|
| `weekly_screener.sh` | 160 B | crontab 미등록 |
| `sync_survey_repo.sh` | 477 B | 호출처 없음 |
| `cron_health.sh` | 381 B | H1과 중복 |
| `neo4j_health.sh` | 429 B | H1과 중복 |
| `neo4j-health-check.sh` | 343 B | H1과 중복 |

## 🟡 MEDIUM 발견 (6건)

- **M1**: `langraph_for_llm_wiki` 레포 — 오타 (langraph → langgraph), 사용처 불명
- **M2**: `hermes-pipeline-scripts` repo 부재 (메모리 약속 vs 실제 없음)
- **M3**: logs 서브모듈 dirty (24h+ uncommitted)
- **M4**: memory.md/user.md 경로 불명 (`~/.hermes/memory/` → 0 bytes)
- **M5**: 큰 wiki 페이지 4개 (200줄+): memory-pipeline, troubleshooting, SCHEMA, memory-and-skills
- **M6**: `architecture/` 비대 — 5 메인 + how-to-use-hermes 9개

## 🟢 LOW 발견 (4건)

- **L1**: 디스크 4.2GB (90%는 hermes-agent)
- **L2**: 미사용 8 skills (curator 자동 archive 부재)
- **L3**: README emoji 과다
- **L4**: trade-pipeline 적정선 (~5K lines, OK)

## 🏗️ 오버엔지니어링 (OE) 분석

### OE1: GraphRAG 4-Layer (Memory → Wiki → Neo4j → Lazy Search)
- **현실 사용**: 99%는 wiki grep. Neo4j semantic은 initial phase만
- **평가**: 설계는 OK. Neo4j는 nice-to-have
- **결론**: 유지하되 Phase 4 (incremental) 비용 대비 효과 적음

### OE2: self-healing watchdog (401/403/404/429/5xx 모두 커버)
- **현실 발생**: 404 (Unknown Channel) 90%
- **평가**: YAGNI — 401/429/5xx는 발생 안 함
- **결론**: 404 + 네트워크 에러만 1차

### OE3: 114개 스킬 (3:1 dead ratio)
- **사용 통계**: 29 used / 8 never / **85 untracked**
- **결론**: 사용 안 하는 50% uninstall

### OE4: 26개 GitHub 레포 (18 GitHub-only)
- **평가**: 대부분 knowledge base → 1회성 write, read-only. OK.
- **결론**: `langraph` 오타 archive만

### OE5: 3 scripts 약속 ≠ 실행
- `wiki_reindex.sh` (cron active) ✅
- `memory_sync.sh` (manual only) ⚠️
- `memory_alert.sh` (없음) ❌
- **결론**: 5-stage verify validate 단계 누락

## ✅ 강점 (5건) — 유지할 것

1. **단일공식 일관성** (모든 자산이 why→what→how→validate)
2. **SSoT**: watchlist.json, check_health.py = symlink 단일화
3. **위키-스킬-메모리 3-Layer 지식** 자기개성 구조
4. **self-healing 실증**: Discord 404 + ImportError 자동 fix (logs/2026-07-03-0025.md)
5. **검증 가능 자산**: commit hash, file size, last-modified 측정

## ⚠️ 약점 (4건)

1. **검증 < 약속**: memory_alert.sh, hermes-pipeline-scripts
2. **디스크 4.2GB 비효율**: hermes-agent 90%
3. **스킬 3:1 dead ratio**: curator 자동 archive 부재
4. **중복 스크립트 5건**: H1+H2+H4

## 🎯 권장 액션 (우선순위)

| # | 액션 | 효과 | 비용 |
|:-:|:-----|:----:|:----:|
| 1 | Neo4j health 3 → 1개 통합 | HIGH | 5분 |
| 2 | self_healing canonical push | HIGH | 10분 |
| 3 | memory_alert.sh 작성 | HIGH | 30분 |
| 4 | logs submodule commit | MED | 2분 |
| 5 | 미사용 50% 스킬 uninstall | MED | 1시간 |
| 6 | `langraph_for_llm_wiki` archive | LOW | 1분 |
| 7 | how-to-use-hermes 9페이지 → 1 README 통합 검토 | LOW | 1시간 |

## 📂 검증 가능한 자산 (Provenance)

- **감사 보고서**: `~/.hermes/wiki/architecture/2026-07-03-system-audit.md` (12,192 bytes)
- **GitHub commit**: `5ba83d6` (push 완료)
- **audit 스킬**: `~/.hermes/skills/devops/hermes-ecosystem-audit/SKILL.md` (10,277 bytes, 644 권한)

## 🔄 다음 감사 시 비교 항목

다음 감사에서 다음 항목들을 추적:
- [ ] H1-H4 해결됐는가?
- [ ] OE5 (3 scripts 약속) 중 memory_alert.sh 작성됐는가?
- [ ] `langraph_for_llm_wiki` archive됐는가?
- [ ] 미사용 스킬 50개 uninstall 진행됐는가?
- [ ] 디스크 사용량 변화 (4.2GB 기준)
- [ ] 위키 페이지 수 변화 (55개 기준)
- [ ] 새 HIGH/MEDIUM/LOW 발견 패턴

## 💡 Patterns Worth Watching

다음 감사에서 특히 주의 깊게 봐야 할 패턴:
- **새로운 3중 중복** (H1): 스크립트 추가할 때마다 발생 가능
- **새로운 2-version drift** (H2): sync 안 된 포크
- **새로운 Promised-but-Absent** (H3): 위키/메모리 약속 vs 실행 갭
- **새 submodule dirty** (M3): logs/ 외에 새로 생긴 submodule

## Related

- **SKILL.md** — audit workflow 전체
- **architecture/2026-07-03-system-audit.md** — 영속 보고서
- **code-audit-fix-pack** — atomic fix commit 패턴
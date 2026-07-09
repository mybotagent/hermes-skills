# Step 4: 자율 운영 후보 (2026-07-07)

Step 0→1→2→3은 모두 cron으로 자동 운영 중. Step 4 (사람 개입 0) 후보 5가지. 다음 idle 시 자율 진행 가능.

## 1. 자동 script lint — ruff/black 적용

모든 `~/.hermes/scripts/*.py`에 ruff/black 자동 적용. **blast radius: low** (자동 정정).

```bash
pip install ruff
ruff check --fix ~/.hermes/scripts/*.py
ruff format ~/.hermes/scripts/*.py
```

**판단 기준**: 기존 6개 스크립트 (memory_alert, wiki_lint, compression_drift_check, design_exec_gap, self_improve_loop, kanban_linear_sync) 모두 lint 통과가 사용자 원칙이지만 자동 수정으로 가치 있는 부분이 적은 편. **priority: low**.

## 2. 자동 wiki cleanup — orphan/archive

research/ typed 페이지의 orphan 0건 유지를 cron으로 자동 점검.

```python
# 기존 wiki_lint.py에 통합 가능
if lint_results["① Orphan"] >= 1:
    alert_only("[!ARCHIVE] orphan 페이지 N건 — 30일 후 자동 archive 권장")
```

**판단 기준**: 사용자 단일공식 = "함부로 추측 반영 안 함". 자동 archive는 사용자 결정 영역. → alert_only만.

## 3. 자동 memory archive — Phase 2 watcher 합의 후

2026-07-07에 DESIGN.md (`architecture/memory-to-wiki-watcher-design.md`) 합의. Q1 cron vs slash 결정 후 구현.

**판단 기준**: 사용자 명시 결정 필요. **priority: HIGH (다음 idle 시 DESIGN.md 합의 요청 권장)**.

## 4. 자동 cron health check — fail 5%+ 알림

cron 성공률 5%+ fail 시 자동 alert.

```bash
# 기존 self_improve_loop.py에 통합
cron_gap = 100 - cron.success_pct
if cron_gap >= 5:
    issues.append({...})
```

**판단 기준**: blast radius 0 (alert only). **priority: medium**.

## 5. 자동 Kanban priority 조정 — aging task re-prioritize

오래된 ready task의 priority를 자동 상향.

**판단 기준**: 사용자가 명시적으로 "aging task 자동 정리" 요청한 적 없음. **priority: low (의사결정 변경)**.

---

## 권장 우선순위

다음 idle 시 자동 진행 시:

1. **(4) cron health check** — blast radius 0, alert_only 패턴과 일치, 자가개선 루프와 자연 통합
2. **(2) wiki cleanup alert** — 위와 동일, alert_only
3. **(3) memory archive** — 사용자 DESIGN 합의 후 (다음 세션에서 명시 요청)

(1)/(5)는 가치 대비 노력 적음.
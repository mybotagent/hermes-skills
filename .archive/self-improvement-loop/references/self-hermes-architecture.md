# Self-Improving Hermes Engine Architecture

> Built 2026-07-28. Script: `~/.hermes/scripts/self_hermes.py`
> Cron: `05bd40b25f6f` (매일 22:50 KST, no_agent, deliver=local)
> Wiki: `infra/self-hermes.md`

## 4-Phase Pipeline

```
OBSERVE ──→ PLAN ──→ EXECUTE ──→ MEASURE
    │                    │            │
    ▼                    ▼            ▼
 snapshot.json      rule matrix    history.json
 (6축 수집)         (P1~P3 결정)    (ROI 누적)
```

## 6축 OBSERVE Data Sources

| 축 | 명령어/API | 수집 항목 |
|---|---|---|
| Cron | `hermes cron list` 파싱 | total/ok/error/never/success_rate |
| Skills | `state.db` 90일 + cron Skills: 필드 | on_disk/used_90d/unused_list |
| Wiki | wiki/ 디렉토리 glob | total_pages/old_90d/index_coverage |
| Memory | `MEMORY_FILE.stat().st_size` | bytes (2200 cap) |
| Scripts | scripts/*.{py,sh} | total/cron_referenced/orphan_count |
| Disk | `os.statvfs` | total_gb/free_gb/used_pct |

## PLAN Priority Matrix

| Priority | Trigger | Action | Safety |
|---|---|---|---|
| P1 | memory ≥90% | compact_memory (기존 스크립트 호출) | ✅ |
| P1 | cron success rate 5%p↓ | investigate_failures (flag only) | ✅ |
| P2 | unused skills ≥3 | archive_unused (프론트매터만) | ✅ |
| P2 | wiki index <80% | update_index (링크 자동 추가) | ✅ |
| P2 | NEVER cron ≥1 | review_never_run (flag file) | ✅ |
| P3 | orphan scripts ≥3 | cleanup_orphans (pycache only) | ✅ |

## EXECUTE Safe Operations Only

자동 실행하는 변경의 공통 조건:
- **Idempotent**: 여러 번 실행해도 같은 결과
- **Reversible**: 이전 상태로 복원 가능
- **No external side effects**: GitHub push, API call, email 없음
- **No data deletion**: `__pycache__`만 삭제, 실제 코드는 건드리지 않음

## MEASURE ROI Schema

```json
{
  "date": "2026-07-28",
  "cron_success_rate": 100.0,
  "cron_delta": 0.0,
  "wiki_coverage": 99.2,
  "wiki_delta": 43.0,
  "improvements_applied": 3,
  "unused_skills": 106,
  "orphan_scripts": 13,
  "disk_used_pct": 70.8
}
```

## Key Design Decisions

1. **No LLM**: 순수 Python rule-based → token 0, deterministic, fast
2. **No subagent calls**: 직접 파일 시스템 조작 → Hermes tool 불필요, cron-compatible
3. **Silent when clean**: 개선 필요 없으면 stdout empty → cron deliver 안 함
4. **History JSON**: `~/.hermes/self_hermes/history.json`에 최대 90일 누적
5. **Single formula**: OBSERVE→PLAN→EXECUTE→MEASURE, 조건문 없음

## Cron Details

- ID: `05bd40b25f6f`
- Schedule: `50 13 * * *` (UTC) = 22:50 KST
- Mode: no_agent
- Deliver: local (silent save)
- Script: `self_hermes.py`
- First run: 2026-07-29T13:50:00+08:00

## Usage

```bash
python3 ~/.hermes/scripts/self_hermes.py           # 정상 실행
python3 ~/.hermes/scripts/self_hermes.py --dry-run  # preview
python3 ~/.hermes/scripts/self_hermes.py history    # ROI 이력
python3 ~/.hermes/scripts/self_hermes.py status     # 현재 상태
```

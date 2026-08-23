# Weekly Cleanup 2026-08-23 — Known Issues

**Cron**: weekly-memory-wiki-cleanup  
**실행**: 2026-08-23 07:00 KST

## Lint ② — Broken Wikilinks (7건)

### hermes-trading-hub.md (4건)
| Wikilink | 분류 | 조치 |
|:---------|:-----|:-----|
| `[[harness-engineering-hub]]` | P7 cross-domain 후보 (suffix `-hub`) | 외부 레포 존재 시 submodule 추가, 아니면 제거 |
| `[[macro-strategy]]` | P7 cross-domain 후보 (suffix `-strategy`) |同上|
| `[[macro-indicators-hub]]` | P7 cross-domain 후보 (suffix `-hub`) |同上|
| `[[schedule-calendar-hub]]` | P7 cross-domain 후보 (suffix `-hub`) |同上|

### subagents-library/ (1건)
| Wikilink | 분류 | 조치 |
|:---------|:-----|:-----|
| `[[harness-engineering-hub]]` | P7 cross-domain |同上|

### 무시 가능 (2건)
- `infra/higgsfield-mcp.md`: anchor `#스킬-과적합의-그늘과-매뉴얼-관리법` — anchor 파싱 문제
- `infra/neo4j-local.md`: `[[wikilink]]` — Cypher 쿼리 예시 내 주석

## Lint ⑧ — Tag Taxonomy 누락

| 태그 | 횟수 | SCHEMA.md 등록 여부 |
|:-----|:----:|:-------------------|
| `graphrag` | 3 | 미등록 |
| `neo4j` | 3 | 미등록 |

**조치**: SCHEMA.md Operational 태그 테이블 `infra` 행에 `graphrag`, `neo4j` 추가 권고.

## 메모리 정리

| 항목 | 상태 |
|:-----|:-----|
| Memory tool | 비활성화 (config 또는 환경 문제) |
| User profile | 비활성화 |
| 정리 필요 | 없음 |

## Logs

- `logs/2026/2026-08-23-0700-weekly-cleanup.md` — 전체 감사 결과 기록

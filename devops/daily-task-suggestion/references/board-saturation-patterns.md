# Board Saturation Patterns (Kanban 백로그 과포화)

> daily-task-suggestion 실행 중 실측한 보드 과포화 지표와 대응 패턴.
> 실측: 2026-08-11 07:00 KST (open 259건), 2026-08-12 07:00 KST (open 267건), 2026-08-13 07:00 KST (open 275건)

## 실측 스냅샷 (2026-08-13) — 4일 연속 과포화, 신규 0건 판단 적용

| 지표 | 값 |
|:-----|:---|
| open 태스크 | 275 (todo 37 / ready 236 / in_progress 1 / backlog 1) — 08-12 267건 → +8 |
| todo 중복 | 'Wiki lint 13건' 동일 title **37개** (todo 전부 차지 — 08-12 36개 → +1, 보드 정체 지속) |
| ready 스테일 (≥7d) | 193건 (그중 P0/P1 120건) — 08-12 189건 → +4 |
| [Auto] 태스크 | 105건 (08-12 104건 → +1) |
| self-improve-loop 일일 중복 | 40건 (08-12 39건 → +1) |
| cleanup/정리 태스크 누적 | 37건 (P1 30 + P2 7) — 08-12 37건 → ±0 (신규 생성 없음) |
| lint 관련 | 59건 (todo 37 + ready 22) |
| 기타 중복 클러스터 | README 49건, logs/index 10건, cron-jobs 3건, memory 6건, dev-harness 1건, W32 1건, recap 0건 |

**핵심 관찰 (2026-08-13):** 08-12 생성한 supersede cleanup `t_64227dd5`와 dispatcher root-cause `t_4fe0e249`가 하루 뒤에도 **둘 다 미실행으로 ready에 그대로 존재**. 4일 연속 과포화 + 모든 후보 주제(cleanup, lint, README, logs/index, dev-harness, 회고, memory)가 기존 open 태스크와 중복 → **rule 2/4/5 적용 결과 오늘은 신규 태스크 0건 생성, 상태 경고 리포트만 출력** (SILENT 아님 — 스테일 수치 상승 + 어제 태스크 미실행은 보고할 가치 있는 상태 변화). supersede를 매일 재생성하는 것은 오염 재현임을 재확인: cleanup supersede 생성은 **직전일 생성분(t_64227dd5 등)이 ready에 남아 있는 동안 절대 재생성 금지**.

**대응 원칙 (2026-08-13 확정):**
- cleanup supersede는 이미 1건 존재(가장 최신: t_64227dd5) → 그 실행을 기다릴 것. 신규 생성 금지.
- root-cause 분석(t_4fe0e249)도 이미 존재 → 재생성 금지.
- 모든 신규 주제 후보는 open title 키워드 grep으로 사전 차단됨 → **신규 0건이 올바른 출력**. 리포트는 보드 상태 실측 수치 + 미실행 경고 + 권장 행동(dispatcher 실행 우선)으로 구성.
- 다음 실행(08-14): t_64227dd5/t_4fe0e249가 여전히 ready면 동일하게 신규 0건 리포트. 실행/archive된 경우에만 새 supersede 생성 가능.

## 실측 스냅샷 (2026-08-12)

| 지표 | 값 |
|:-----|:---|
| open 태스크 | 267 (todo 36 / ready 229 / in_progress 1 / backlog 1) |
| todo 중복 | 'Wiki lint 13건' 동일 title **36개** (todo 전부 차지 — 08-11의 35개에서 1 증가, 보드 정체 지속) |
| ready 스테일 (≥7d) | 189건 (그중 P0/P1 117건) — 08-11 178건에서 +11 |
| [Auto] 태스크 | 104건 (08-11 101건 → +3) |
| self-improve-loop 일일 중복 | 39건 (08-11 37건 → +2, 8/11분 신규 생성 확인) |
| cleanup/정리 태스크 누적 | **37건** (P1 30 + P2 7) — 08-11 34건 → +3 |
| lint 관련 | 57건 (todo 36 + ready 21) |
| 기타 중복 클러스터 | README 48건, cron 39건, logs/index 10건, how-to-use-hermes 7건, W33 회고 0건 |

**핵심 관찰 (2026-08-12):** 08-11 생성한 supersede cleanup 태스크 `t_771dbc18`가 하루 뒤에도 **미실행으로 ready에 그대로 존재**. cleanup 태스크는 '생성'만 되고 dispatcher가 실행하지 않아 매일 쌓이는 구조적 문제 → 08-12에 root-cause 태스크 제안: `t_4fe0e249` (dispatcher 실행 경로 점검 — cleanup 전용 cron 또는 priority 임계 조정). 즉 supersede 태스크를 만들어도 실행 주체가 없으면 무의미하므로, 과포화가 3일 연속 지속되면 cleanup 생성과 함께 root-cause 분석을 병행 제안할 것.

## 실측 스냅샷 (2026-08-11)

| 지표 | 값 |
|:-----|:---|
| open 태스크 | 259 (todo 35 / ready 222 / in_progress 1 / backlog 1) |
| todo 중복 | 'Wiki lint 13건' 동일 title **35개** (todo 전부 차지 → 보드 완전 정체) |
| ready 스테일 (≥7d) | 178건 (그중 P0/P1 111건) |
| [Auto] 태스크 | 101건 (daily-repo-orchestrator Audit/Epic false positive — 동일 에픽이 매일 재생성) |
| self-improve-loop 일일 중복 | 37건 (7/7~8/10, cron 22:50 self-hermes가 전일 태스크 archive 없이 매일 신규 생성) |
| cleanup/정리 태스크 누적 | 34건 (정리 제안이 미실행으로 쌓임 — '정리 제안' 자체가 오염원이 된 상태) |
| lint 관련 | 55건 (todo 35 + ready 20) |
| 기타 중복 클러스터 | README 동기화 8+, logs/index 갱신 10+, how-to-use-hermes quality pass 7+, SCHEMA lint 3+, cron-jobs 3+ |

## 판단 기준 (임계치)

- todo가 전부 동일 title = 보드 완전 정체 → 신규 주제 제안보다 **정리 우선** (중복 주제 신규 생성 전면 금지).
- cleanup 태스크가 20개+ ready = '정리 제안'이 오염원 → **supersede 방식** (아래)으로 단 1개만 생성.
- [Auto] / self-improve-loop 클러스터 ≥ 30건 = false positive 대량 누적 → 일괄 archive 대상으로 cleanup body에 명시.

## Supersede 패턴 (cleanup 태스크 생성 — 2026-08-11 적용 예)

1. title: `Kanban 대정리 실행 YYYY-MM-DD — <주요 중복 요약> + <스테일 수> archive` (유니크, 날짜 포함)
   - 예: `Kanban 대정리 실행 2026-08-11 — 'Wiki lint 13건' todo 35중복 + 스테일 ready 178건 일괄 archive`
2. body에 기존 cleanup 태스크 ID 목록 명시: "이 태스크가 기존 정리 태스크들을 대체(supersede) — 함께 complete/archive"
   - 2026-08-11 예시 ID: t_c3664df5, t_e542403b, t_dcdef0c6, t_7686c81a, t_295e7f68, t_63617983, t_458e8e0b, t_db7285b8, t_1275bb8d, t_4adc845c, t_c1f9cd45, t_c3544f5a, t_ba8ef66e, t_01526389, t_4c863a0c, t_217001bc, t_4303b5a7, t_5e0e6fc0, t_01d6cc75, t_ee34ded5, t_f0682ac1, t_9a8ced85, t_c0207961, t_cb0b7ac3, t_547a15e8, t_73dbde1b, t_e1150a89, t_e9c9cd2b, t_865b61bc, t_cc07e3ab
3. body에 실행 순서: kanban_health.py → lint 중복 1개만 keep → [Auto]/self-improve-loop false positive archive → 기존 cleanup ID들 complete/archive → kanban_health.py 재실행으로 검증
4. P1으로 생성. 성공 결과: 2026-08-11 부모 t_4a8d88b4 + 자식 3건 ready 승격 확인.
5. 2026-08-12 재적용 결과: 부모 t_7e218b37 + 자식 3건 (t_64227dd5 cleanup P1, t_8b49d9a3 dev-harness-kit 문서화 P2, t_4fe0e249 dispatcher root-cause P2) ready 승격. cleanup body에 기존 cleanup 37건 ID 전체 나열해 supersede 명시.
6. **실행 주체 부재 확인 (2026-08-12)**: supersede 태스크를 생성해도 다음 날까지 미실행으로 남음 (t_771dbc18 사례) → 2일 연속 동일 수치 상승 시 cleanup + root-cause 분석을 세트로 제안할 것. root-cause는 cleanup과 별개 태스크로 생성 (cleanup body에 흡수하지 말 것 — dispatcher가 cleanup을 실행하지 않는 것이 문제이므로).

## 오염원 클러스터 스캔 (python3 heredoc — cron 모드 허용)

```python
import json
items = json.load(open('/tmp/kanban_list.json'))
open_items = [t for t in items if t.get('status') in ('todo','ready','in_progress','backlog')]
clusters = ['[Auto', 'self-improve', '정리', 'archive', '백로그', '스테일', 'lint', 'README', 'logs/index']
for k in clusters:
    n = sum(1 for t in open_items if k.lower() in (t.get('title') or '').lower())
    print(f"{k}: {n}")
```

## 근본 원인 후보 (root-cause 태스크로 제안 가능)

- self-improve-loop 일일 중복 37건 → cron 스킬/스크립트에 "기존 open 태스크 있으면 신규 생성 금지" 규칙 추가 (2026-08-11에 P2 태스크로 제안, t_01b6e0f0).
- README 동기화 8+건 반복 → index.md ↔ README.md 역할 단일화 방안 (기계적 sync 대신 구조적 해결).
- [Auto] 에픽 101건 → daily-repo-orchestrator false positive 필터 개선 (t_f2f7ec38, 2026-08-10 생성).
- cleanup 태스크 37건 미실행 (supersede 포함) → dispatcher가 ready P1을 실행하지 않는 경로 분석 + cleanup 전용 실행 cron 제안 (t_4fe0e249, 2026-08-12 생성).

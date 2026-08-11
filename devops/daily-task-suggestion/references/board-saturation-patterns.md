# Board Saturation Patterns (Kanban 백로그 과포화)

> daily-task-suggestion 실행 중 실측한 보드 과포화 지표와 대응 패턴.
> 실측: 2026-08-11 07:00 KST (open 259건)

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

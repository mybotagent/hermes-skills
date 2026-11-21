# 월간 리밸런싱 (Monthly Rebalancing)

종목선별·포��폴리오 비중 변경을 **매월 1일에만** 수행하는 운영 방식.
일일 성과 추적은 별도 파이프라인으로 계속 유지한다.

---

## 1. 왜 두 주기를 분리하는가

| 작업 | 주기 | 담당 |
|---|---|---|
| 종목선별 + 비중 결정 (Phase 1~3) | **매월 1일 18:35** | LangGraph cron `afebf6cb0ab1` (`35 18 1 * *`) |
| 일일 스냅샷·수익률·대시보드 | 평일 매일 18:45 | paper_tracker cron `276405a79d88` (`45 18 * * 1-5`) |
| 월간 성과 검증 리포트 | 매월 1일 08:10 | `18510b01362d` (`10 8 1 * *`) |

종목선별만 월 1회로 바꾸면 **스냅샷이 끊겨** 일일 수익률 계산이 죽는다.
따라서 "구성 변경은 월 1회, 스냅샷 기록은 일일"로 분리한다.

---

## 2. carry-forward 계약 (핵심 장치)

`scripts/carry_forward_snapshot.py` — 오늘 스냅샷이 없으면 직전 스냅샷을 **복사**한다.

### 규칙
1. **원본 스냅샷은 절대 수정하지 않는다.** 복사는 read-only.
2. 오늘 스냅샷이 이미 있으면 **아무것도 하지 않는다** (리밸런싱 원본 보호).
3. 복사본에 메타데이터를 붙인다:
   - `carry_forward: true`
   - `carry_forward_from: "YYYY-MM-DD"` (복사한 원본 날짜)
4. 생성 후 `date` 필드는 **오늘 날짜**로 설정한다 (paper_tracker가 날짜 키로 쓰므로).

### `--check` 모드
파일을 만들지 않고 "무엇이 생길지"만 출력한다. 사전 검증용.

### 실행 순서 (HARD RULE)
`paper_tracker_daily.sh`에서 carry-forward는 **paper_tracker.py보다 먼저** 실행해야 한다.
반대로 두면 당일 스냅샷이 없어서 그날 수익률이 0으로 처리된다.

```
Step 0: carry_forward_snapshot.py   ← 오늘 스냅샷 확보
Step 1: paper_tracker.py             ← 당일 수익률 계산
```

---

## 3. carry-forward 스냅샷 보호

carry-forward 스냅샷은 "원본의 복사본"이다. 여기서 구성을 바꾸면 **원본이 아닌 복사본만** 바뀌어
성과 이력이 어긋난다. 따라서 구성 변경 로직은 carry-forward를 **건너뛴다**.

| 로직 | 파일 | carry-forward 처리 |
|---|---|---|
| 비중 2% 복원 | `scripts/fix_portfolio_weights.py` | **스킵** (`carry_forward` 플래그 확인 후 조기 return) |
| KR 제거 | `scripts/fix_portfolio_weights.py` | KR은 이미 원본 생성 시 제거됐으므로 무해. 단 저장 시 `carry_forward` 메타 유지 |
| 목표 비중 계산 | `scripts/compute_portfolio_target.py` | KR 제외만 수행. 스냅샷 자체는 건드리지 않음 |

---

## 4. 리밸런싱 메타데이터

Phase 3(`langgraph/src/agents/portfolio_allocation.py`)가 새 스냅샷을 저장할 때 추가:

```python
allocation["rebalance"] = True
allocation["rebalance_date"] = today   # e.g. "2026-12-01"
```

Phase 3 PROMPT에도 규칙을 명시한다:
- 이 프롬프트는 **매월 1일에만** 실행되고 출력 비중이 **한 달 내내 유지**된다.
- → 일별 미세 조정(micro-adjustment)을 하지 말 것. 한 달치로 유효한 **구조적 비중**을 결정.
- 현금 비중도 월 단위로 판단.

---

## 5. 대시보드 표시

대시보드 상단 부제목에 리밸런싱 기준일을 배지로 표시한다.

- 데이터 소스: `data/portfolio_latest.json` (paper_tracker가 생성하는 미러)
- `rebalance_date` → "📅 리밸런싱 2026-11-20"
- `carry_forward === true` → "📅 리밸런싱 2026-11-20 · 비중 유지 중"

### 왜 `data/`에 두는가
배포 스크립트와 healthcheck가 **DATA_DIR를 루트로** 참조한다.
`data/portfolio_target.json`, `data/paper_tracker_metrics.json` 와 같은 패턴을 따른다.
`logs/portfolio/` 아래에 두면 healthcheck가 "파일 없음"으로 심각 오류를 낸다.

### `latest.json` 미러가 필요한 이유
대시보드(FE)는 서버사이드가 없다. 디렉터리 목록을 열거할 수 없으므로
"가장 최근 스냅샷"을 가리키는 **단일 진입점 파일**이 반드시 필요하다.

`paper_tracker.py`의 `write_latest_mirror()`가 생성한다.
→ carry-forward 스냅샷이면 `rebalance_date`가 없으므로 **원본에서 물려받아** 채운다.

---

## 6. 함정

1. **🔴 carry-forward를 paper_tracker 뒤에 두면 당일 수익률이 0이 된다.**
   스텝 순서가 곧 데이터 준비 순서다. carry-forward가 먼저.

2. **🔴 "오늘 스냅샷 없음"을 실패로 보지 말 것.** 월간 리밸런싱에서는 정상 상태다.
   carry-forward가 채우는 것이 정답이며, carry-forward 스냅샷을 "리밸런싱 결과"로 오인하지 말 것.

3. **🔴 원본 스냅샷을 손대지 말 것.** copy가 아니라 move/수정으로 구현하면
   리밸런싱일의 원본이 사라져 "그날 어떤 비중이었나"를 영구히 잃는다.

4. **🔴 대시보드 데이터 파일 위치는 DATA_DIR 규칙을 따른다.**
   healthcheck가 HTML의 fetch 경로를 DATA_DIR 기준으로 검사한다.
   `logs/portfolio/` 같은 다른 루트에 두면 즉시 "심각" 오류가 난다.

5. **🔴 `load_all_portfolios()`는 미러 파일을 스냅샷으로 세지 않아야 한다.**
   `logs/portfolio/latest.json` 같은 미러를 그대로 로드하면 날짜순 정렬이 깨지고
   "N개 스냅샷 발견" 카운트가 어긋난다. 미러는 명시적으로 skip 한다.

6. **🔴 cron schedule 변경은 기존 프롬프트를 보존해야 한다.**
   `cronjob_manage update`는 프롬프트를 통째로 다시 보내야 한다.
   기존 프롬프트를 조회하지 않고 짧게 쓰면 Phase별 Discord 전달 규칙이 사라진다.

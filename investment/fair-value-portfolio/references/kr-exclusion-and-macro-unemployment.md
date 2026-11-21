# 국내주식(KR) 제외 정책 + 실업률/Sahm 지표 추가 (2026-11-21)

사용자 확정 정책 2건을 기록한다. 이후 변경 시 이 문서를 먼저 읽고 일관되게 적용할 것.

---

## 1. 국내주식(KR) 완전 제외

### 결정
포트폴리오에서 **국내 상장주식을 완전히 제외**한다. 제외분 비중은 현금으로 귀속한다.

### 판별 기준 (3중 체크)

| 기준 | 예시 |
|---|---|
| watchlist `market == "KR"` | `SK하이닉스`(000660.KS), `삼성전자`(005930.KS) |
| 종목명/티커 일치 | watchlist의 KR 티커·이름 세트에 포함 |
| 접미사 `.KS` / `.KQ` | `005930.KS`, `000660.KQ` |

**단, US ADR은 제외 대상이 아니다.**
`SK하이닉스ADR`은 watchlist에서 `ticker=SKHY`, `market=US`, `currency=USD`이므로
미국 상장 ADR이며 계속 편입한다. "한국 기업"이라는 이름만 보고 제외하지 말 것.

### 적용 지점 (4곳, 프롬프트 의존 금지)

| 파일 | 조치 |
|---|---|
| `langgraph/src/agents/portfolio_allocation.py` | PROMPT에 "국내주식(KR) 완전 제외" 규칙 추가 + `_strip_kr_stocks()`로 **저장 직전 강제 제거** |
| `langgraph/pipeline.py` | Phase 1 후보에서 KR 제거 → Phase 2 분석 대상에서도 제외 |
| `scripts/fix_portfolio_weights.py` | 템플릿 복원 경로 + **당일 스냅샷만** KR 제거 |
| `scripts/compute_portfolio_target.py` | 목표 비중 계산에서 KR 제외 (대시보드 노출 방지), 제외분 현금 귀속 |

LLM 프롬프트만으로 의존하면 탈락이 발생하므로 **코드 필터를 함께 둔다**.

### 과거 데이터 보호 (사용자 선택: "과거 유지")

- 기존 스냅샷(`logs/portfolio/*.json`)의 KR 종목은 **그대로 둔다**.
- 이유: 누적수익률·MDD 등 과거 성과 이력을 재작성하면 안 된다.
- KR 제거는 **신규 생성 스냅샷부터** 적용한다.
- `fix_portfolio_weights.py`는 오늘 날짜 스냅샷에만 KR 제거를 적용하고 저장을 건너뛴다.
- `paper_tracker.py`는 미변경 (과거 백필 히스토리 보존).

---

## 2. 거시경제 지표: Sahm Rule + 실업률

### 수집 (FRED)

| 지표 | FRED 코드 | 용도 |
|---|---|---|
| Sahm Rule | `SAHMREALTIME` | 경기침체 신호 (0.5 이상) |
| 실업률 | `UNRATE` | Sahm Rule의 근간 지표 |
| 실업률 3M 변화 | (파생) | `UNRATE - UNRATE.rolling(3).mean()` |

### 반영 파일

| 파일 | 변경 |
|---|---|
| `scripts/generate_macro_dashboard.py` | `UNRATE`, `UNRATE_3M_Chg` 계산 → JSON `unrate`/`unrate_3m_chg`, CSV 컬럼 추가 |
| `scripts/generate_macro_plots.py` | 서브플롯 8개 → **10개**. plot_8=Sahm Rule, plot_9=실업률+3M변화(twin axis) |
| `data/portfolio_dashboard.html` | 지표 카드 `실업률`/`실업률 3M` 추가 + plot_8/plot_9 `<img>` 추가 |

### 플롯 인덱스 규칙 (HARD RULE)

`macro_plots/plot_N.png` 인덱스는 **대시보드가 하드코딩**한다.
차트를 중간에 삽입하면 기존 plot 번호가 밀려 전부 깨진다.
→ 새 차트는 **뒤에 붙인다** (현재 마지막은 plot_9).

### 경고 임계값 (대시보드)

| 지표 | 주의 | 경고 |
|---|---|---|
| 실업률 | 5.0% ↑ | 4.5% ↑ |
| 실업률 3M 변화 | +0.30p ↑ | +0.15p ↑ |

### 2026-11-21 실측값

```
sahm_rule     : 0.0     (FRED 2026-10 SAHMREALTIME)
unrate        : 4.1     (FRED 2026-10 UNRATE)
unrate_3m_chg : -0.03
```

역사적 참고: Sahm 최대 9.5 (2020 COVID), Sahm ≥ 0.5 구간 58회.

---

## 3. 배포 경로

`~/.hermes/scripts/paper_tracker_daily.sh` 실행 → GitHub push → Vercel 자동 배포.
- 커밋 저자 이메일이 `sanghee.lee2222@gmail.com`이어야 private repo 배포가 BLOCKED되지 않는다.
  (global `user.email`은 noreply이므로 스크립트가 repo-local로 덮어씀 — 상세는 `infra/environment.md`)
- 배포 후 반드시 라이브에서 `plot_8.png` / `plot_9.png` HTTP 200 및 `index.html` 참조를 확인할 것.
  → `scripts/verify_paper_deploy.sh`가 이 검증을 자동화한다.

---

## 4. 이 정책 적용 시 함정

### 🔴 스크립트가 "제거했다"고 출력해도 디스크는 그대로일 수 있다
`fix_portfolio_weights.py`에서 KR 제거 로직이 **조기 return 뒤에** 있어 stdout에만 "제외됨"이 출력되고
JSON 파일은 갱신되지 않았다. → 가공 결과를 만들면 **즉시 write-back** 하고, 확인은 stdout이 아니라
**파일을 다시 읽어서** 한다.

### 🔴 "과거 유지"와 "오늘 스냅샷 갱신"은 별개다
KR 제거를 무조건 적용하면 과거 성과 이력(누적수익률·MDD)이 조작된다.
반대로 무조건 건너뛰면 신규 스냅샷에 KR이 남는다.
→ 제거 조건을 **날짜 비교로 분리**한다: `date_str == 오늘` 이면 제거·저장, 과거면 건너뛴다.

### 🔴 필터 검증에서 빈 배열을 "성공"으로 읽지 말 것
`portfolio_target.json`의 종목 배열 키는 `stocks`가 아니라 **`target_allocation`**이다.
잘못된 키를 읽으면 배열이 비어 보이고 "KR 포함: [] ✅"처럼 검증 통과처럼 보인다.
→ 검증 시 (a) 키 존재를 먼저 assert, (b) 항목 개수를 함께 출력, (c) "빈 배열 + 성공 표시"는 실패로 간주.

### 🔴 플롯 데이터 검증용 CSV는 없다
`generate_macro_plots.py`는 **PNG만** 저장한다. `macro_plots_data.csv` 같은 파일을 찾지 말 것.
수치 검증은 `data/macro_regime_history.csv`의 `sahm` / `unrate` / `unrate_3m_chg` 컬럼을 읽는다.

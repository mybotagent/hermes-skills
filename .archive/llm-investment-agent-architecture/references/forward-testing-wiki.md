# Forward Testing Framework (Wiki Link)

전체 프레임워크 문서: `~/.hermes/wiki/analysis/forward-testing.md`

## 핵심 요약

### 평가 기준
- BUY↑=+2, BUY↓=-1, SELL↓=+2, SELL↑=-1, HOLD±5%=+1, HOLD>5%↑=0, HOLD>5%↓=+1
- 월간 Accuracy = ΣScore / ΣMaxScore × 100

### 비중 산식
- 개별 종목 비중 = (Gap_Score×0.6 + Moat_Score×0.4) / Σ전체 × (1-cash_ratio)
- Gap_Score = min(mid_gap/100, 1.5), Moat_Score = moat_to_score(moat)/10
- 제약: 최소 2% ~ 최대 15%

### 현금 비중
- Regime 기반 Base + Alpha-Flip ±5%p
- 최소 0% ~ 최대 50%

### 저장소
- logs/forward_testing/decisions_log.csv
- logs/forward_testing/portfolio_log.csv
- logs/forward_testing/daily/YYYY-MM-DD.md
- logs/forward_testing/monthly/YYYY-MM.md

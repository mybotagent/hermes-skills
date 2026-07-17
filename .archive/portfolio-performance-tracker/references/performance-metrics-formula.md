# Performance Metrics — 산식 참조

## 누적수익률 (Cumulative Return)

```
C = Π(1 + r_i) - 1
```

- r_i = i번째 날의 포트폴리오 가중 일일수익률
- 0% 기준 표시 (net return)

## 연율화수익률 (Annualized Return)

```
R_ann = (1 + C)^(252 / N) - 1
```

- N = 트레이딩 일수 (252 = 연간 기준)
- C = 전체 누적수익률 (multiplier form)

## MDD (Maximum Drawdown)

```
MDD = min((V_t - Peak_t) / Peak_t)
```

- V_t = t시점의 누적 multiplier (cumReturn, NOT net return)
- Peak_t = t시점까지의 최고점
- peak는 multiplier 기준으로 계산 (net return이 아님에 주의)

## Sharpe Ratio

```
Sharpe = (R_avg - Rf) / σ(R) × √252
```

- R_avg = 일일수익률 평균
- Rf = 무위험 수익률 (연 3% = 일 0.0119%)
- σ(R) = 일일수익률 표준편차 (자유도 1, ddof=1)
- √252 = 연율화 계수 (daily → annual)

## 일일 포트폴리오 수익률

```
R_portfolio = Σ(w_i × r_i) + w_cash × 0
```

- w_i = i번째 종목의 포트폴리오 비중 (decimal, e.g. 0.15 = 15%)
- r_i = i번째 종목의 전일 대비 일일수익률
- w_cash = 현금 비중 (수익률 0% 가정)

## 기여도 (Contribution)

```
Contrib_i = w_i × r_i
```

- 각 종목이 포트폴리오 전체 수익률에 기여한 정도
- Σ(Contrib_i) = R_portfolio

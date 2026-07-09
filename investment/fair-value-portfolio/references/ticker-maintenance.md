# Ticker Maintenance Guide (관심종목 추가/제거)

> **현행**: `data/watchlist.json` 하나만 수정하면 됨. 5개 파일 시대는 끝남.

## 1. watchlist.json — 유일한 데이터 소스

**위치**: `~/trade-pipeline/data/watchlist.json`

```json
{
  "stocks": [
    {"ticker": "NVDA", "name": "엔비디아", "market": "US", "sector": "AI Infrastructure"},
    ...
  ],
  "sector_base": {
    "Technology": 22, "Semiconductors": 18, ...
  }
}
```

**추가**: 단순히 배열에 새 객체 push
```json
{"ticker": "ANET", "name": "아리스타네트웍스", "market": "US", "sector": "Technology"}
```

**제거**: 해당 객체를 배열에서 삭제

### 섹터 규칙
- 섹터는 `sector_base`에 정의된 값만 사용
- yfinance 섹터가 틀렸으면 적절한 `sector_base` 값으로 수동 지정
- 새 섹터 필요시 `sector_base`에 항목 추가 (base PER 참고: tech 22, semi equip 22, industrial 15, energy 10)

### 변경 후
```bash
cd ~/trade-pipeline && git add -A && git commit -m "watchlist: add/remove ..." && git push
```
→ **git push 필수** (사용자 추적을 위해)

## 2. 데이터 품질 엣지 케이스

### SPCX (SpaceX) — 비상장 기업
- SPCX는 yfinance에 데이터가 있지만 **SpaceX는 아직 상장 전** (pre-IPO)
- fair_value 실행 시 `⚠️ 데이터 불충분` 출력 — 정상 동작, 제거 불필요
- yfinance가 SPAC/쉘 컴퍼니 정보를 잘못 매핑한 케이스

### KLA analyst target $2,250 vs 실제 주가 $249
- 가끔 upgrades_downgrades에서 analyst target이 단위 오류(10배)로 수집됨
- KLA 사례: Wolfe Research/Barclays target $2,250 (주가 $249의 9배) → 데이터 오류
- **대응**: fair_value.py output에서 오차율 > 80%면 데이터 오류 의심하고 리포트에 주석

### 데이터 불충분 종목 (INTC 패턴)
- INTC는 yfinance FPE/Forward EPS 누락으로 `⚠️ 데이터 불충분`
- 제거하지 않고 watchlist에 유지 (yfinance 데이터가 복구될 수 있음)
- fair_value.py 출력에만 표시, pipeline LangGraph에서는 자동 제외

## 3. 검증

```bash
cd ~/trade-pipeline && python3 langgraph/src/fair_value.py
```

- 모든 티커가 정상 출력되는지 확인
- 섹터가 의도대로 반영되었는지 적정PER 컬럼 확인
- 신규 종목은 analyst target 유무도 확인 (US는 Finnhub/upgrades_downgrades 자동)

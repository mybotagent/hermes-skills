# Stdout Parse Regex Patterns

Generic regex patterns for parsing structured text output from Python analysis scripts.

## Pattern 1: Per-ticker valuation line

**Source format** (fair_value_v3.py):
```
✅ 엔비디아       | P:     $205.10 | PER  31.5→ 16.2 | 적정PER 35 | T0       $192(-6.5%) → T1       $373(+81.8%) | PER75:PBR25
⚠️ 인텔 (INTC): 데이터 불충분
✅ 삼성전자       | P:    ₩329,000 | PER  42.8→  5.8 | 적정PER 11 | T0   ₩100,972(-69.3%) → T1   ₩523,038(+59.0%) | PER75:PBR25
```

**Regex**:
```python
import re
pattern = re.compile(
    r'[✅⚠️]\s+(.+?)\s+\|\s*P:\s*(\$?₩?[0-9,]+(?:\.\d+)?(?:만)?)\s+'
    r'\|\s*PER\s+([0-9.]+)→\s*F?\s*([0-9.]+)\s+'
    r'\|\s*적정PER\s+([0-9.]+)\s+'
    r'\|\s*T0\s+(\$?₩?[0-9,]+(?:\.\d+)?(?:만)?)\(([+-]?[0-9.]+)%\)\s*→\s*T1\s+(\$?₩?[0-9,]+(?:\.\d+)?(?:만)?)\(([+-]?[0-9.]+)%\)'
)

stocks = []
for line in lines:
    m = pattern.search(line)
    if m:
        stocks.append({
            "name": m.group(1).strip(),
            "price": parse_price(m.group(2)),
            "current_pe": float(m.group(3)),
            "forward_pe": float(m.group(4)),
            "fair_pe": float(m.group(5)),
            "t1_price": parse_price(m.group(8)),
            "t1_gap": float(m.group(9)),
        })
```

**Price parser**:
```python
def parse_price(s: str) -> float:
    """'$205.10' → 205.10, '₩329,000' → 329000.0, '₩207만' → 2070000"""
    s = s.strip().replace("$", "").replace(",", "").replace("₩", "")
    if "만" in s:
        return float(s.replace("만", "")) * 10000
    return float(s)

def is_krw(s: str) -> bool:
    return "₩" in s
```

## Pattern 2: Trailing JSON from analyst collector

**Source format** (analyst_target_collector.py):
```
...summary text...
📦 JSON 출력:
{
  "MU": {"target": 1190, "source": "Morgan Stanley(06/03)", ...},
  "005930.KS": {"target": 500000, "source": "너구리제공", "name": "삼성전자"},
  ...
}
```

**Extraction**:
```python
import re, json

# Find the LAST JSON object in stdout
text = result.stdout
json_match = re.search(r'\{[\s\S]*\}', text)
if json_match:
    data = json.loads(json_match.group())
```

## Pattern 3: Name-to-ticker mapping for cross-referencing

When parsing Korean-named stocks from one source and ticker-based data from another:

```python
NAME_TO_TICKER = {
    # US stocks (English → English ticker)
    "엔비디아": "NVDA", "마이크론": "MU", "램리서치": "LRCX",
    "시게이트": "STX", "샌디스크": "SNDK", "TSMC": "TSM",
    "AMD": "AMD", "테라다인": "TER", "브로드컴": "AVGO",
    "루멘텀": "LITE", "마블테크": "MRVL", "HPE": "HPE",
    "Celestica": "CLS", "알파벳": "GOOGL", "애플": "AAPL",
    "마이크로소프트": "MSFT", "델": "DELL", "일라이릴리": "LLY",
    # KR stocks (Korean name → yfinance ticker)
    "삼성전자": "005930.KS", "SK하이닉스": "000660.KS",
    "삼성전기": "009150.KS", "현대차": "005380.KS",
    "에이피알": "278470.KQ", "HD현대일렉": "267260.KS",
}
```

## Testing Parse Accuracy

After parsing, always verify the count matches expectations:

```python
print(f"✅ {len(stocks)}개 종목 파싱 완료")
assert len(stocks) == expected_count, f"Expected {expected_count}, got {len(stocks)}"
```

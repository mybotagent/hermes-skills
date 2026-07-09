# CSV Format Specification

## 헤더 (7개 필드)
```csv
date,time,exercise,sleep,mood,physical,water
```

## 정확한 필드 수 = 7 (trailing comma 금지)

### 정상 기록 (5문항 전부) — 7개 필드
```csv
2026-06-17,09:22,yes,yes,neutral,good,yes
```
- date, time, **exercise**, **sleep**, **mood**, **physical**, **water**

### 데이터 누락 시
```csv
2026-06-11,07:08,,no,,,
```
- date, time, (exercise=empty), **sleep**, (mood=empty), (physical=empty), (water=empty)
- `,,no,,,` = 6 commas = 7 fields ✓

### ❌ trailing comma 주의
- `2026-06-17,09:22,yes,yes,neutral,good,yes,` → 8개 필드 → 오류
- `2026-06-11,07:08,,no,,,,` → 8개 필드 → water 값이 shift됨

## sleep 값 매핑
| clarify 응답 | CSV 값 |
|-------------|--------|
| 7시간 이상 (충분) | `yes` |
| 5~7시간 (보통) | `yes` |
| 3~5시간 (부족) | `no` |
| 3시간 미만 (매우 부족) | `no` |

## 점수형 값
| clarify 응답 | CSV 값 |
|-------------|--------|
| 좋음 (Good) | `good` |
| 보통 (Neutral) | `neutral` |
| 나쁨 (Bad) | `bad` |

## 달성형 값
| clarify 응답 | CSV 값 |
|-------------|--------|
| 했음 / 1L 이상 / 네 (완료) | `yes` |
| 안함 / 1L 미만 / 아니오 (미복용) | `no` |

## bash로 append
```bash
echo '2026-06-17,09:22,yes,yes,neutral,good,yes' >> ~/.hermes/survey/log.csv
```

## Python DictReader
```python
reader = csv.DictReader(StringIO(raw))
for r in reader:
    val = r['sleep']  # 정확한 컬럼명
```

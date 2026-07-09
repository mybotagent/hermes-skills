# os.path.dirname Depth Calculation — langgraph/src/ 하위 파일

## 문제

`trade-pipeline`에서 Python 스크립트가 `langgraph/src/` 아래에 있을 때,
`os.path.dirname(os.path.abspath(__file__))`의 depth 계산이 자주 틀린다.

## 올바른 Depth 계산

```
파일 위치:        langgraph/src/analyst_target_collector.py
depth 1:          langgraph/src/                  ← dirname(__file__)
depth 2:          langgraph/                      ← dirname(dirname(__file__))
depth 3:          trade-pipeline/                 ← dirname(dirname(dirname(__file__)))
                  ↑   이게 PROJECT_DIR (= 3 depth)
```

### 공식

| 원하는 경로 | depth | 코드 |
|:-----------|:-----:|:-----|
| `trade-pipeline/data/watchlist.json` | 2 | `os.path.dirname(os.path.dirname(__file__))` + `"data/watchlist.json"` |
| `trade-pipeline/` (PROJECT_DIR) | 3 | `os.path.dirname(os.path.dirname(os.path.dirname(__file__)))` |
| `trade-pipeline/data/` (DATA_DIR) | 2 | (상동) |

### 현황 (파일별)

| 파일 | 경로 | 정확도 |
|:----|:-----|:------|
| `fair_value.py` | `dirname × 3 + "data/"` | ✅ 정상 |
| `analyst_target_collector.py` | `dirname × 2 + "data/"` | ✅ **2026-06-07 수정 완료** (was: `dirname × 1 + "../data/"` → `langgraph/data/`로 잘못됨) |
| `collect_macro_context.py` | `DATA_DIR` (.env) 사용 | ✅ 정상 |
| `pipeline.py` | `DATA_DIR` (.env) 사용 | ✅ 정상 |
| `graph.py` | `DATA_DIR` (.env) 사용 | ✅ 정상 |
| `decision_validator.py` | `Path(__file__).parent.parent.parent` | ✅ 정상 |

## 검증 명령어

```bash
# 실제 경로 출력 확인
cd ~/trade-pipeline && python3 -c "
import os
f = 'langgraph/src/analyst_target_collector.py'
print('depth 1:', os.path.dirname(os.path.abspath(f)))
print('depth 2:', os.path.dirname(os.path.dirname(os.path.abspath(f))))
print('depth 3:', os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(f)))))
"
```

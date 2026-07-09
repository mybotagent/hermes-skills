# Tool-as-Memory Pattern (2026-07-07 검증)

> memory.md 본문 → KEY only + 별도 tool로 lazy fetch.
> 본질 변경 사례. 단순 압축 ❌, 구조 재설계 ✅.

## 🎯 문제 정의

memory.md는 **매 세션 100% inject**됨 (instructional tool).
- 본문 길이가 곧 토큰 비용 + 컨텍스트 점유율
- 50% 압축해도 본질은 동일 — 매번 본문 전체 로드
- 사용자 룰: "50% 이하로 줄여져야 함"

## 🔧 해결: Tool-as-Memory

### Before
```
[memory.md: 2,191 chars / 99.6%]
17 § facts, 각 fact = 본문 (path + ctx + 상세)
에이전트: 매 세션 전체 2,191 chars inject
```

### After
```
[memory.md: 306 chars / 13.9%]
  - memory=key→wiki.tool:memory_query(key)
  - keys:tz,api_deepseek,...,ssot (21개 key만 나열)

[memory_query.py: 5KB tool]
  - KEY_MAP: {key → (wiki_path, ctx)}
  - 사용: python3 memory_query.py <key>  → 위키 본문 fetch

[skills/memory-query/SKILL.md: 1.8KB]
  - 에이전트가 native skill로 사용 가능
```

**핵심**: memory.md는 **위치만** 들고 본문은 위키에 있다. 에이전트가 필요할 때만 `memory_query(key)` 호출.

## 📐 3단계 구조

### Step 1: KEY_MAP 작성 (Python dict)

```python
KEY_MAP = {
    "tz": ("infra/cron-jobs.md", "KST+9, cron07=`0 6`, 21=`0 20`"),
    "watchlist": ("watchlist/README.md", "data/watchlist.json 단일소스"),
    "bot_ids": ("infra/bot-architecture.md", "aiprofit/채니봇/plan/ds"),
    # ... 21개
}
```

각 fact을 `(wiki_path, 1줄 ctx)`로 압축. ctx는 grep 가능 1줄.

### Step 2: memory.md = KEY만

```
memory=key→wiki.tool:memory_query(key).
keys:tz,api_deepseek,api_finnhub,...,ssot
```

### Step 3: Skill 등록

`~/.hermes/skills/memory-query/SKILL.md`:
- description: "Memory tool — key-based lazy fetch"
- quick_start: `python3 ~/.hermes/scripts/memory_query.py <key>`

## 📊 효과

| 측정 | Before | After |
|---|---|---|
| memory.md size | 1,964 chars (89.3%) | 306 chars (13.9%) |
| 본문 접근 | grep memory.md (전체) | `memory_query.py <key>` (해당 본문만) |
| 매 세션 inject | 1,964 chars | 306 chars |
| 본질 변경 | ❌ | ✅ (memory가 본문 안 들고 있음) |

## ⚠️ Pitfall

1. **drift 검증 도구의 § 파싱 한계**: § 구분자 다음 줄을 fact으로 인식하는데, KEY 형식 `[ctx]`가 state.db의 fact 형식과 안 맞으면 drift 검출 실패. 도구 업데이트 필요.
2. **key 추가 시 3곳 동기화**: KEY_MAP.py ↔ memory.md `keys:` 라벨 ↔ wiki/skill description. 한 곳 빠뜨리면 lookup 실패.
3. **ctx 압축 시 grep 가능성 유지**: 약어는 의미 보존 필수 (`tz`, `api_deepseek` OK / `k1` ❌).
4. **skill 등록 필수**: 스크립트만 있으면 자동완성 안 됨. `~/.hermes/skills/<name>/SKILL.md` 등록해야 에이전트가 native tool로 사용.

## 🔄 일반화 패턴

다른 "상시 inject되는 본문"에도 적용 가능:

| 본문 | 위치 | 변환 |
|---|---|---|
| 크론 목록 | memory.md | `cron_list.py <name>` → cron 정의 fetch |
| Bot IDs | memory.md | 이미 적용 (`bot_ids` key) |
| 사용자 선호도 | USER.md | 동일 패턴 적용 가능 |
| 분석 공식 | wiki methodology | 이미 적용 (`macro_6stage`) |

## 🔗 Cross-ref

- `hermes-ecosystem-audit` SKILL.md §메모리 본질 변경 패턴 (Tool-as-Memory)
- `memory-query` skill (구현체)
- `compression_drift_check.py` (§ 파싱 한계)
- 사용자 명령 패턴: "본질을 바꿔주고" → 단순 압축 아닌 구조 재설계
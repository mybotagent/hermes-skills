---
name: memory-query
description: Memory tool — key-based lazy fetch (memory.md는 key only, 본문은 위키)
triggers:
  - memory_query
  - "memory query"
  - "메모리 조회"
  - "fact 조회"
  - "memory 본문"
when_to_use: |
  메모리에 있는 fact의 본문이 필요할 때. memory.md는 key만 들고 있어 본문은 위키에 있음.
  이 skill은 `~/.hermes/scripts/memory_query.py`를 호출해서 lazy fetch.
quick_start:
  - command: python3 ~/.hermes/scripts/memory_query.py <key>
  - example: python3 ~/.hermes/scripts/memory_query.py watchlist
  - list: python3 ~/.hermes/scripts/memory_query.py --list
  - search: python3 ~/.hermes/scripts/memory_query.py --search bot
---

# Memory Query Skill — Tool-as-Memory

## Why (architecture rationale)

**memory.md는 key만 (목표 ≤ 50%, 현재 13.9%).** 본문은 모두 위키에 있고, 에이전트는 key 호출 시에만 lazy fetch한다.

### 왜 본질을 바꿨는가 (user-explicit 2026-07-07)

사용자가 "더 나은 방식이 있어?" / "본질을 바꿔주고"라고 명시적으로 교정함. **Half-baked lazy indexing은 불충분**:

| 방식 | 결과 | 한계 |
|------|------|------|
| § 구분자 + ctx 본문 | 1,107 chars (50.3%) | 본문 매번 inject |
| KEY[]+FILE inverted index | 1,293 chars (58.8%) | 50% 못 맞춤 |
| **Tool-as-Memory (current)** | **306 chars (13.9%)** | 본문 0 |

핵심: **memory는 위치만, 본문은 호출 시 fetch**. 에이전트 context window에서 memory가 차지하는 비중을 ~87% 감소.

### Architecture

```
[세션 시작]
    ↓
[memory.md 자동 로드: 306 chars, 21 § keys]
    ↓ (필요 시)
[memory_query.py <key>]
    ↓
[wiki 페이지 본문 fetch (1500자)]
    ↓
[답변 합성]
```

## 사용법

| 명령 | 용도 |
|------|------|
| `python3 ~/.hermes/scripts/memory_query.py <key>` | 단일 fact 본문 |
| `python3 ~/.hermes/scripts/memory_query.py <key> --ctx-only` | 위키 fetch 없이 1줄 ctx만 |
| `python3 ~/.hermes/scripts/memory_query.py --list` | 21개 key 전체 목록 |
| `python3 ~/.hermes/scripts/memory_query.py --search <q>` | 검색 |
| `python3 ~/.hermes/scripts/memory_query.py --stats` | 메모리 통계 |

## 21 Keys

```
tz, api_deepseek, api_finnhub, macro_6stage, watchlist, deepseek_key,
deepseek_gcal, dashboard, linear_api, linear_mirror, thread_routing,
survey, bot_ids, multibot, verify_5stage, gateway_fix, speculation,
discord_only, user_style, gh_pr_policy, ssot
```

## Pitfall

### 1. Key 동기화는 **수동 작업**
본문이 변경됐을 때 `memory_query.py`의 `KEY_MAP` dict도 동기 업데이트 필요. 자가개선 루프가 자동 검증하지만 본문 추가 시 수동 patch.

### 2. Compression drift false-positive (§ 파서 버그)
`compression_drift_check.py`가 § 다음 비어있지 않은 줄을 fact으로 추출. **현재 memory.md의 § 구분자 다음 KEY[] 형태 줄이 정상 fact이지만, 형식이 바뀌면 false-positive 발생** (2026-07-07 실제 사례). KEY 추가/제거 후 drift 검증 시 false-positive 가능성 인지.

### 3. Wiki fetch는 첫 1500자만
긴 페이지는 `read_file` 직접 사용. 첫 1500자가 핵심 정보 — 더 필요한 경우 raw path로 직접.

### 4. memory.md 본문 길이 임계치
- **목표**: ≤ 50% (1,100 chars)
- **alert**: ≥ 90% (1,980 chars)
- **max**: 2,200 chars (cap)
- **현재**: 306 chars (13.9%) — 여유 충분

### 5. KEY_MAP 동기화 시 wiki 페이지 존재 확인
`KEY_MAP`에 key 추가 시 반드시 대응 wiki 페이지 존재 확인. `--list` 출력에서 ✓/✗로 표시.

## 관련 인프라

- **Cron `cb2ee5fafc5d`** memory daily auto-compact — 매일 06:30 KST, 90% 넘으면 자동 압축
- **`memory_auto_compact.py`** — 압축 룰 + drift 검증
- **`compression_drift_check.py`** — drift 검증 도구 (false-positive 인지 필요)
- **MEMORY_MAP.md** (`mybotagent/memory-map` repo) — wiki 페이지 매핑 카탈로그

## 새 KEY 추가 절차

1. `~/.hermes/wiki/`에 페이지 작성 (frontmatter + body)
2. `memory_query.py`의 `KEY_MAP` dict에 key → (path, ctx) 추가
3. `memory.md`의 `keys:` 줄에 key 이름 추가 (comma-separated)
4. `python3 memory_query.py --list`로 wiki 페이지 존재 ✓ 확인
5. (선택) `MEMORY_MAP.md` 업데이트 + push
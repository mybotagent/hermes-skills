# Memory Lazy Indexing (Karpathy Wiki 패턴의 Memory 적용)

> memory.md를 wiki처럼 lazy indexing — § facts → 위키 페이지 링크.
> 사용자 명시 목표: memory ≤ 50% (1,100/2,200 chars).
> 50% 목표는 `memory_auto_compact.py`의 90% alert 임계치와 별개.

## 사용자 룰 (2026-07-07 합의)

```
memory.md 사용률이 50%를 넘으면 wiki lazy indexing으로 재설계.
```

이 룰은 단일 압축 (12 룰 적용)이 89.3%까지만 내리는 한계를 인식해서 등장.
다음 단계는 **wiki로 정보 이동** — memory는 § fact의 한 줄 표현 + 위키 링크만.

## Lazy Indexing Architecture

```
[memory.md: ≤50%]
       │ N § facts, 각 fact = "<짧은 라벨> → <wiki_path>"
       ▼ (필요 시 lazy fetch)
[memory_lazy_fetch.py --fact N] → wiki 페이지 첫 500자
       │
       ▼ (전체 본문 필요 시)
[wiki 페이지 on-demand read]
```

**Before (2026-07-07)**:
```
memory.md: 987 chars (44.9%)  ← 12 룰로 여기까지 도달
16 facts × 평균 60 chars = 960 chars
```

**After (lazy indexing)**:
```
memory.md: 987 → 987 chars (44.9%)  ← 동일하지만 구조 변경
17 facts (SYS 룰 추가) × 평균 58 chars
각 fact이 "wiki 링크 → 1줄 설명" 형태로 압축
```

**핵심 변화**: 압축은 **구조 변경**이지 단순 글자수가 아님. 같은 987 chars 안에서:
- 이전: 16 facts × 평균 60 chars (사실 진술이 인라인)
- 이후: 17 facts × 평균 58 chars (사실 진술이 wiki로 이동, 메모리는 포인터만)

## memory-map GitHub Repo (분리 관리)

사용자 메시지: *"메모리 맵을 만들어서 github으로 따로 관리해도 좋을 듯"*

**Repo**: `https://github.com/mybotagent/memory-map`

**README.md 구조**:
1. Architecture 다이어그램 (memory.md ↔ wiki ↔ memory-map)
2. 17 facts ↔ wiki 페이지 매핑 테이블
3. 업데이트 절차
4. 압축 룰 (50% / 90% / drift 0%)
5. 자동화 (cron 목록)
6. 통계 (현재 size, § facts 수, drift)

**왜 별도 repo인가**:
- `hermes-wiki`는 wiki 페이지 단일소스
- `memory-map`은 **메모리 ↔ 위키 매핑** 단일소스
- 둘이 같은 repo면 wiki 변경 시 memory-map도 함께 push해야 함 (강결합)
- 분리하면 memory-map은 lazy fetch용 인덱스, wiki는 본문 (관심사 분리)

## 사실(facts) ↔ Wiki 페이지 매핑

| # | Fact | Wiki Page | Section |
|---|------|-----------|---------|
| 1 | TZ:KST+9, cron 시간 | `infra/cron-jobs.md` | Cron 시간대 |
| 2 | SYS: 경로변경X, API=.env, MEMORY=포인터 | `architecture/ssot-single-source-of-truth.md` | 단일소스 |
| 3 | API: DeepSeek, MiniMax-M3, Finnhub | `infra/environment.md` | API Keys |
| 4 | 매크로 6단계 | `analysis/methodology.md` | E.Summary → Priority |
| 5 | watchlist 단일소스 | `watchlist/README.md` | 단일소스 (2026-07-02) |
| 6 | deepseek/GCal | `code/scripts.md`, `infra/gmail-himalaya.md` | 키/timeout |
| 7 | Dashboard nginx/iptables | `architecture/how-to-use-hermes/06-messaging-platforms.md` | 6-5. 웹 대시보드 |
| 8 | Linear .env grep, MCP | `infra/environment.md` | Linear API |
| 9 | 스레드→discord-gateway, 설문 | `infra/discord-gateway.md`, `infra/daily-survey.md` | 채널 라우팅 |
| 10 | Bot IDs | `infra/bot-architecture.md` | 봇 구성 |
| 11 | Multi-bot 80% (4대역할) | `infra/bot-architecture.md` | 핵심 사실 |
| 12 | 5-stage verify | `architecture/5-stage-verify.md` | why→validate |
| 13 | 게이트웨이 fix | `infra/discord-gateway.md` | ImportError, HOME_CHANNEL |
| 14 | Speculation cascade | `architecture/speculation-cascade-rule.md` | 5번 추측 = 손상 |
| 15 | Discord-only | `infra/discord-gateway.md` | OAuth/password |
| 16 | user-style | `people/aiprofit.md` | "알아서/왜 못함?" |
| 17 | GitHub PR 정책 | `infra/github-pr-automation-policy.md` | claude-code-action 금지 |

## § 마커 단일공식 (memory.md 구조)

```
<카테고리 라벨>:<한 줄 사실 본문>.<위키 링크>.
§
<카테고리 라벨>:<한 줄 사실 본문>.<위키 링크>.
§
...
```

**왜 § 구분자를 쓰는지**:
- `compression_drift_check.py`가 § 기준으로 fact을 파싱
- 각 fact이 독립 라인으로 분리되어 자동 압축 룰 적용 가능
- `memory_lazy_fetch.py`의 FACT_MAP과 1:1 매핑

**Pitfall — § 마커 파싱 버그**: 첫 줄 카테고리 라벨이 1st fact으로 잡힐 수 있음. 해결책은 `compression_drift_check.py`에서 첫 줄은 카테고리로 인식하도록 prefix 매칭.

## 🆕 Inverted index 변형 (2026-07-07 후속 합의)

위 `<라벨>: <본문>. <wiki 링크>.` 형식은 가독성은 좋지만 매 fact 50-70 chars. **50% 임계치 통과 + grep 효율성**을 동시에 원하면 `KEY[ctx] FILE` 형식이 더 적합:

```
tz[KST+9,07=0_6]	infra/cron-jobs.md
§
api_deepseek[.env,flash/pro]	infra/environment.md
§
bot_ids[aiprofit/채니/plan/ds]	infra/bot-architecture.md
```

**장점**:
- 한 fact = 30-50 chars (이전 50-70 대비 ~30% 작음)
- grep 친화적: `grep "^api_deepseek" MEMORY.md`로 key 단위 검색
- TSV처럼 column-aligned → 50% 임계치 쉽게 도달

**단점**:
- ctx가 KEY 안에 인코딩 → 사람이 읽기 어려움 (e.g., `gateway_fix[pyc,HOME_CH]`)
- `compression_drift_check.py`가 § 다음 줄을 그대로 fact으로 잡으므로 KEY 형식 변경 시 drift 측정 결과 왜곡 가능

**선택 기준**:
- **50% 이하 목표 + grep 우선** → inverted index (`KEY[ctx] FILE`)
- **가독성 우선** → label form (`<라벨>: <본문>. <wiki>.`)
- **혼용 ❌**: 한 형식 정착 후 섞으면 안 됨 (drift check + FACT_MAP 둘 다 깨짐)

**실제 적용 (2026-07-07)**: 1,107 chars (50.3%) 도달. 7 chars만 더 줄여서 50% 정확히 통과시킬지 vs 약간 넘기는지 결정. ctx 압축 극한까지 가면 의미 잃음 — **이 한계 인식하고 50.3%에서 멈춤**.

**Inverted index 사용 시 FACT_MAP 동기화** (added 2026-07-07):
- `memory_lazy_fetch.py`의 FACT_MAP dict은 key를 그대로 사용 (`tz`, `api_deepseek` 등)
- memory.md의 KEY가 `tz[KST+9,07=0_6]`면 FACT_MAP key도 `tz` (괄호 안 ctx는 매칭 안 함)
- 검증: `python3 memory_lazy_fetch.py --list`의 key 목록 == 메모리 § facts의 KEY prefix 목록

## Lazy Fetch 스크립트 (companion)

```bash
python3 ~/.hermes/scripts/memory_lazy_fetch.py              # 전체 fact 목록
python3 ~/.hermes/scripts/memory_lazy_fetch.py --fact 5     # 단일 fetch (#5 = watchlist)
python3 ~/.hermes/scripts/memory_lazy_fetch.py --search deepseek  # 검색
```

**출력 (예시)**:
```
=== Memory Lazy Fetch (17 facts) ===
memory.md: 987 chars (lazy indexed)
---
  ✓  1. TZ/cron                   → infra/cron-jobs.md
  ✓  2. SYS 단일소스                  → architecture/ssot-single-source-of-truth.md
  ...
  ✓ 17. GitHub PR 정책              → infra/github-pr-automation-policy.md
```

**FACT_MAP 동기화**: 스크립트의 FACT_MAP dict은 `memory-map/README.md`의 매핑 테이블과 동기화되어야 함. 둘 중 하나 변경 시 다른 쪽도 업데이트.

## 안전 가드: 압축 전 위임 fallback 검증 (CRITICAL)

memory에서 어떤 fact이라도 제거하기 전에 **반드시**:

```bash
grep -rn "<핵심 키워드>" ~/.hermes/wiki/ ~/.hermes/wiki/index.md 2>/dev/null
```

**매칭 0건이면**: 위키 페이지 먼저 작성 후 압축.

**실제 사례 (2026-07-07)**:
- L17 Bot IDs의 "채니봇=hermes(Linux,config.yaml+env), plan/ds=Mac launchd" 부분
- 초기 시도: 압축 시 제거
- 검증: `grep -rn "launchd\|채니봇=hermes" ~/.hermes/wiki/` → 0건
- 조치: `~/.hermes/wiki/infra/bot-architecture.md` 작성 후 압축
- 학습: **위임 fallback 없는 사실은 memory에서 절대 제거 금지**

## 신규 위키 페이지 (lazy indexing 시 작성)

memory → wiki lazy로 이동할 때 wiki에 신규 페이지가 필요한 경우:

| 신규 페이지 | 이유 | 메모리 사실 |
|------------|------|------------|
| `architecture/5-stage-verify.md` | 단일 공식 정의 (memory L21) | "5-stage verify→architecture/5-stage-verify.md." |
| `architecture/speculation-cascade-rule.md` | 추측 cascade 룰 (memory L25) | "Speculation→speculation-cascade-rule.md." |
| `infra/github-pr-automation-policy.md` | claude-code-action 금지 (memory L31) | "GitHub PR→github-pr-automation-policy.md." |
| `infra/bot-architecture.md` | 봇 환경 매핑 (memory L17 일부) | "Bot IDs→bot-architecture.md(aiprofit,채니봇,plan,ds)." |

각 페이지 0.9~1.2KB, frontmatter + 관련 페이지 링크 + 핵심 룰.

## memory.md 압축 비율 단계

```
Step 0: 초기 상태       89.3% (1,964 chars) — 12 룰로 도달
Step 1: lazy indexing   44.9% (987 chars)  — 50% 임계치 통과
Step 2: (다음 idle)     ~40% (880 chars)   — 추가 압축은 사용자 결정
```

**자동 압축은 90% → 50% (12 룰 + lazy indexing)로 이미 도달**.
**50% → 40%** 추가 압축은 사용자 명시 요청 시에만.

## Verify current state (LESSON — 2026-07-07)

`memory_lazy_fetch.py` 출력의 첫 줄은 항상 현재 size 표시:
```
memory.md: 987 chars (lazy indexed)
```

**만약 size가 compaction context와 다르면**: compaction이 stale, 측정값이 진실. `wc -m ~/.hermes/memories/MEMORY.md`로 직접 확인.

## Pitfalls

**FACT_MAP과 메모리 § facts 개수 불일치**. 스크립트 dict (17) ≠ 메모리 (17)이어야 함. 한쪽 변경 시 다른 쪽도 업데이트. 검증: `python3 memory_lazy_fetch.py | head -1`의 facts 수 == 메모리 `§` 마커 수 + 1 (첫 줄).

**메모리에서 wiki로 이동 시 정정 사실 누락**. 예: `Bot IDs(2026-07-01정정): 이전 메모리 오류 정정` 같은 정정 사실은 별도 wiki 페이지에 기록해야 함. 메모리에는 정정 사실 자체는 안 남고 최신 ID만 남김.

**§ 구분자 누락 시 drift 측정 실패**. § 마커는 단일공식의 일부. 한 줄이라도 빠지면 drift check가 0% → ~50%로 점프. compression_drift_check.py는 § 카운트 기반.

**memory-map repo 동기화 누락**. wiki 페이지 추가/이동 시 memory-map의 README.md도 함께 업데이트. 두 repo가 sync 깨지면 lazy fetch가 stale 링크 가리킴.

**Lazy fetch 결과 500자 제한**. `memory_lazy_fetch.py`는 첫 500자만 출력. 전체 본문 필요 시 `read_file(path)` 직접 호출.
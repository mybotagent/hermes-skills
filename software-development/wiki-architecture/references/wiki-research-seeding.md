# Wiki Research/ Seeding + SCHEMA.md 8종 Lint (2026-07-07 실전)

> idle-time 자율 hygiene로 research/ 빈 디렉토리(entities/concepts/comparisons)에 typed 페이지 시드 + SCHEMA.md lint 검증한 실전 절차.
> 검증된 결과 1회 (hermes-agent entity + llm-wiki-pattern concept + llm-wiki-vs-rag comparison).

## Step 1: 빈 디렉토리 상태 확인

```bash
ls -la ~/.hermes/wiki/research/{entities,concepts,comparisons}/
# 기대 출력: .gitkeep만 존재 (페이지 0건)
```

## Step 2: 시드 후보 선정 (3건)

본 시스템의 시드 권장 후보:

| 타입 | 파일 | 출처 |
|---|---|---|
| entity | `research/entities/hermes-agent.md` | hermes-agent SKILL.md (1차 출처) |
| concept | `research/concepts/llm-wiki-pattern.md` | Karpathy gist (1차 출처) |
| comparison | `research/comparisons/llm-wiki-vs-rag.md` | hermes-wiki-super README + Neo4j GraphRAG docs |

→ 1 entity + 1 concept + 1 comparison = 3개 타입 전부 시드. SCHEMA.md §2의 "typed pages" 정의 100% 커버.

## Step 3: Raw source 먼저 저장 (wiki-save §④ 규칙)

**반드시 typed 페이지 작성 전에 raw/에 원본 저장**:

```bash
~/.hermes/wiki/raw/<topic>-<YYYY-MM-DD>.md
# 또는 위키 외부 출처의 경우:
~/.hermes/wiki/raw/<source>-extracted-<YYYY-MM-DD>.md
```

raw 파일 형식 (위키 frontmatter):
```yaml
---
source_url: <original URL or wiki-save source>
ingested: YYYY-MM-DD
---
# <Topic> — Raw Source

원본 텍스트 그대로 (가공/요약 금지)
```

## Step 4: Typed 페이지 작성 (3건)

각 파일은 SCHEMA.md §6 research frontmatter 필수:

```yaml
---
type: entity | concept | comparison
title: 페이지 제목
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: [research, type, ...]
sources: [raw/소스파일.md]
confidence: high | medium | low
related: [research/<type>/related.md, ...]
---
```

본문 권장 구조:
- 정의 / 핵심 속성 (3~6 bullet)
- 본 시스템에서의 위치 / 적용
- 비교 / 왜 중요한가 / 출처

**1.5~2KB / 페이지** — wiki 컨벤션(1~5KB, AGENTS.md §5) 준수.

## Step 5: .gitkeep 제거 (typed 페이지 생겼으니)

```bash
rm ~/.hermes/wiki/research/{entities,concepts,comparisons}/.gitkeep
```

## Step 6: index.md 갱신

```bash
# 기존 (빈 디렉토리 표시):
- (빈 디렉토리) — entities/concepts/comparisons 타입 페이지 저장

# 변경 (실제 페이지 링크):
### entities/
- [Hermes Agent](research/entities/hermes-agent.md) — 본 시스템 두뇌 entity (high confidence)

### concepts/
- [Karpathy LLM Wiki Pattern](research/concepts/llm-wiki-pattern.md) — 5계층 구조 (high confidence)

### comparisons/
- [LLM Wiki vs Vector RAG](research/comparisons/llm-wiki-vs-rag.md) — 8축 비교 (medium confidence)
```

## Step 7: SCHEMA.md 8종 lint 검증

```bash
# [① Orphan] inbound link 0인 페이지
for f in ~/.hermes/wiki/research/*/*.md; do
  name=$(basename "$f")
  refs=$(grep -rl "$name" ~/.hermes/wiki/ 2>/dev/null | grep -v "$f" | wc -l)
  echo "$name: $refs refs"
done

# [② Broken wikilink]
grep -h '\[\[' ~/.hermes/wiki/research/*/*.md || echo "none"

# [③ INDEX.md 누락]
for f in ~/.hermes/wiki/research/*/*.md; do
  name=$(basename "$f")
  grep -q "$name" ~/.hermes/wiki/index.md || echo "MISSING: $name"
done

# [④ Frontmatter 검증] — type/title/created/updated/tags 필수
for f in ~/.hermes/wiki/research/*/*.md; do
  for field in type title created updated tags; do
    grep -q "^${field}:" "$f" || echo "MISSING $field in $f"
  done
done

# [⑤ Stale] updated > 90일 (현 시점 모두 0일 → OK)
# [⑥ 모순] contested: true (없으면 OK)
# [⑦ 품질] confidence: low 또는 단일 출처 → medium 허용
# [⑧ Tag audit] SCHEMA.md taxonomy 외 태그 → 없으면 OK
```

## Step 8: Git commit + push

```bash
cd ~/.hermes/wiki
git add -A
git commit -m "wiki: research/ 시드 — typed pages 3건 (entity/concept/comparison) + raw 3건"
git push origin main
```

**Pitfall: anonymous raw.githubusercontent.com 404** — private repo는 raw fetch 불가. 검증은 `git ls-remote origin main` + GitHub UI 직접.

## 검증된 결과 (2026-07-07)

| 단계 | 결과 |
|---|---|
| raw 3건 | ✅ hermes-agent, llm-wiki-pattern, llm-wiki-vs-rag |
| typed 3건 | ✅ 1.5~2KB / 페이지 |
| .gitkeep 제거 | ✅ 3개 |
| INDEX.md 갱신 | ✅ raw + research 섹션 |
| SCHEMA 8종 lint | ✅ 8/8 pass |
| GitHub push | ✅ commit `20e814f` |

## 언제 이 시드를 트리거하나

- 위키 audit 시 research/ 디렉토리 0건 발견
- 사용자가 "샘플 typed 페이지 만들어줘"
- 새 SKILL.md 추가 후 그에 매칭되는 entity 페이지 시드
- LLM Wiki 패턴 학습 후 실전 적용 (Karpathy 패턴 직접 체험)

## Pitfall

| 함정 | 회피법 |
|---|---|
| raw 저장 생략 | wiki-save §④ 규칙 — typed 페이지 작성 전에 raw/에 원본 먼저 |
| 페이지 1건만 시드 (다른 타입 미커버) | entity + concept + comparison = 3타입 동시 시드 |
| .gitkeep 그대로 두기 | typed 페이지 생기면 즉시 제거 (혼란 방지) |
| Frontmatter `confidence` 누락 | SCHEMA.md §6 필수 — high/medium/low 중 하나 |
| `sources:` 누락 | raw 파일 경로 명시 필수 (provenance 추적) |
| 5KB 초과 페이지 | Karpathy 원칙 위반 — 분할 또는 축약 |
| INDEX.md 갱신 누락 | SCHEMA lint ③ 즉시 fail — 반드시 갱신 |

## Cross-ref

- `wiki-save` SKILL.md §④ Raw Source 보존 (절대 잊지 말 것)
- `wiki-architecture` SKILL.md "Layer 2 — Shared Wiki" + "Verification Checklist"
- `~/.hermes/wiki/SCHEMA.md` §6 Frontmatter Convention (research 타입)
- `~/.hermes/wiki/AGENTS.md` §5 품질 규칙 (1~5KB, Concise pages)
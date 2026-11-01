# P19 — index.md 서브모듈 오염: 근본 원인과 영구 fix

> 2026-11-01 주간 cleanup에서 **33회 연속 재감염의 근본 원인**을 특정하고 코드 레벨에서 수정.
> 이전까지는 symptom(rogue 항목 제거)만 반복 → 2026-09-14 ~ 2026-10-30 사이 33회 "P19 recovery" 로그가 쌓였으나 재발.

## 증상

`~/.hermes/wiki/index.md` 맨 끝(footer `*Managed by Hermes Agent...*` 아래)에 아래 형식의 항목이 매일 추가됨:

```markdown
- [2026 07 06 Daily Repo Orchestrator](logs/2026-07-06-daily-repo-orchestrator.md) — 자동 추가 (2026-10-31)
- [Subagents Library Hub](subagents-library/subagents-library-hub.md) — 자동 추가 (2026-10-31)
```

- 하루에 ~70줄 증가 → `git diff HEAD -- index.md`가 diff 폭을 독점
- commit `fc103d3`의 메시지: `auto-sync ... — P19 recovery (remove 65 rogue submodule entries, committed variant)`
- 로그마다 `working-tree 전용 / 커밋 불필요`로 기록 → **다음 날 재감염**

## 근본 원인 (2026-11-01 특정)

`~/.hermes/scripts/self_hermes.py`의 `_execute_update_wiki_index()`:

```python
wiki_files = list(WIKI.rglob("*.md"))      # ← 서브모듈 내부까지 descent
excluded = {"AGENTS.md", "SCHEMA.md", "index.md", "INDEX.md", "README.md"}
for f in wiki_files:
    ...
    if link_name not in index_content:
        line = f"\n- [{title}]({link_name}) — 자동 추가 ({TODAY_STR})"
        index_content += line
```

`~/.hermes/wiki/`는 **git superproject + 서브모듈 구조**:

```
wiki/
├── logs/              ← submodule: mybotagent/hermes-logs        (75개 .md 중 다수)
├── subagents-library/ ← submodule: mybotagent/subagents-library
└── (실제 페이지 86개)
```

`WIKI.rglob("*.md")`는 서브모듈 디렉토리까지 재귀 → `logs/2026/*.md`, `logs/2026-05-31-*.md`,
`subagents-library/**/*.md` 전부가 index 후보가 됨. 이 중 index에 없던 것들이 매 실행마다 footer에 append.

**왜 33회 발견이 늦었나**: 원인이 index.md가 아니라 `self_hermes.py`에 있는데, P19 대응이 항상
"index.md만 정리" 수준에 머물렀기 때문. **git blame / 커밋 메시지가 아니라 "무엇이 index.md를 쓰지?"를
질문해야** 근본에 도달한다.

## 영구 fix (적용 완료 2026-11-01)

`self_hermes.py` `_execute_update_wiki_index()`에 서브모듈 최상위 디렉토리 제외 추가:

```python
    index_content = index_file.read_text()
    wiki_files = list(WIKI.rglob("*.md"))
    excluded = {"AGENTS.md", "SCHEMA.md", "index.md", "INDEX.md", "README.md"}
    # P19 fix (2026-11-01): 서브모듈 디렉토리(logs/, subagents-library/)는
    # rglob이 descended → index.md에 수십 건 rogue 항목 자동 삽입 → 33회 연속 재감염.
    # 서브모듈은 각자 자체 index.md를 가지므로 여기서 제외한다.
    submodule_dirs = {"logs", "subagents-library"}

    added = 0
    for f in wiki_files:
        if f.name in excluded:
            continue
        rel = f.relative_to(WIKI)
        if rel.parts[0] in submodule_dirs:
            continue
        link_name = str(rel).replace("\\", "/")
        ...
```

**정당성**: 서브모듈은 각자 자체 `index.md`를 보유 (`logs/index.md`, `subagents-library/subagents-library-hub.md`).
parent wiki의 index.md는 **실제 페이지(86개)만** 카탈로그로 관리하는 것이 설계 의도 (`AGENTS.md` Five Layers).

## 정합성 확인 recipe (신규 스크립트)

`scripts/wiki_index_coverage.py` — 서브모듈 제외 실제 페이지 기준의 index 커버리지 + rogue 탐지:

```bash
python3 ~/.hermes/skills/autonomous-system-hygiene/scripts/wiki_index_coverage.py
# 실제 페이지 86개 / index 누락 0 / rogue 자동추가 0 / index에 있는 dangling 링크 0
```

## 다른 index.md writer 감사 (필수)

fix 후 반드시 **다른 writer가 있는지** 확인 — 하나만 고치면 다른 게 재삽입함:

```bash
cd ~/.hermes/scripts && grep -ln "index.md" *.py *.sh
```

결과 분류:

| 파일 | 동작 | 조치 |
|---|---|---|
| `self_hermes.py` | **쓰기** (원인) | 수정 완료 |
| `dawn_wiki_sync.sh` | `git add -A` → working-tree 오염을 커밋할 수 있는 **경로** | 원인 제거로 무해화. 단독 fix는 불필요 |
| `wiki_lint.py` | 읽기만 | 무시 |
| `self_consistency_check.py` | 읽기만 | 무시 |
| `memory_auto_curator.sh` | 읽기만 | 무했��� |

> **주의**: `dawn_wiki_sync.sh`는 `git add -A`를 하므로, working tree에 rogue가 있으면 **GitHub까지 push된다**.
> P19 과거 로그가 "working-tree 전용"이라 한 것은 dawn sync가 그걸 커밋하지 않은 시점의 사실일 뿐 —
> 어느 시점에 push될지는 보장되지 않는다. **원인 수정이 최우선.**

## 참고: P19 로그가 남아 있던 파일

- `logs/2026/2026-10-21-2100.md` ~ `logs/2026/2026-10-30-2100.md` (33회 연속 기록)
- `logs/2026/2026-09-27-0700-weekly-cleanup.md` — 최초 P19 recovery 로그

## 교훈 (일반화)

**재발 버그를 N회 고쳤는데 계속 재발하면, 그건 해결이 아니라 ritual이다.**
증상(index.md 정리)을 N번 반복할 때 본인은 "고치고 있다"고 생각하지만 실제로는 매번 같은 되돌리기를 반복.
**반드시 3번째 질문으로 넘어가라**:

1. "무엇이 이 파일을 쓰지?" → `grep -ln "<파일명>" ~/.hermes/scripts/`
2. "그 코드가 왜 그렇게 쓰지?" → `rglob` / `glob` / `find`의 재귀 범위, 예외 목록
3. "설계 의도와 맞나?" → AGENTS.md Five Layers / SCHEMA.md

P19는 이 3단계를 거쳤을 때 30분 안에 근본 원인이 나왔다.

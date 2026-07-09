---
name: wiki-knowledge-ingest
description: "Use when adding a new wiki repo to hermes-wiki-super → auto-discover → full index → embedding → search test → paper-standard IR evaluation. Automates the entire pipeline from repo connection to Neo4j knowledge graph."
version: 1.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [wiki, neo4j, graphrag, knowledge-graph, embedding, index, evaluation, ir-metrics]
    related_skills: [local-graphrag-kb, hermes-agent-skill-authoring]
---

# Wiki → Knowledge Graph Ingest Pipeline

새 Wiki 레포를 `hermes-wiki-super`에 추가 → 자동 발견 → Neo4j 인덱싱 → 임베딩 → 검색 가능하게 만드는 전체 워크플로우.

## Overview

`hermes-wiki-super`는 모든 Wiki 레포를 submodule로 관리. 새 레포를 추가하면:

1. `.gitmodules` 등록 → `discover.py`가 자동 감지
2. `git submodule update --init` → checkout
3. Full re-index → 384d bge-m3 임베딩 생성
4. Neo4j vector/graph 검색 가능
5. GitHub push

## When to Use

- 새 Wiki 레포 생성 후 `hermes-wiki-super`에 연결할 때
- 기존 submodule의 git HEAD가 변경되어 재인덱싱 필요할 때
- 임베딩이 오래되어 다시 생성해야 할 때
- "이 내용 knowledge graph에서 검색 안 돼" — 원인이 미인덱싱일 때
- 새 검색 시스템 도입 후 정확도 검증 필요할 때 (Phase 6 패턴)

## Workflow

### Step 1: 새 Wiki 레포를 super repo에 submodule로 등록

```bash
cd ~/hermes-wiki-super

# Add submodule (GitHub 기준)
git submodule add https://github.com/mybotagent/<new-repo>.git wiki/<new-repo>

# .gitmodules에 자동 등록됨
git add .gitmodules wiki/<new-repo>
git commit -m "feat: add <new-repo> as submodule"
git push
```

### Step 2: discover.py로 자동 감지 확인

```bash
source ~/.venv-neo4j/bin/activate
python3 .metagraph/discover.py
```

출력에서 새 레포가 `new` 상태로 보여야 함:

```
<new-repo>    <ns>  ✅  new        /home/ubuntu/hermes-wiki-super
```

### Step 3: 전체 재인덱싱 (임베딩 포함)

```bash
source ~/.venv-neo4j/bin/activate
cd ~/hermes-wiki-super/.metagraph

# Full re-index (모든 repo 스캔 → 임베딩 생성 → Neo4j MERGE)
python3 indexer.py
```

### Step 4: 증분 인덱서 상태 갱신

```bash
# --force로 모든 repo 갱신 (새 repo도 상태에 등록)
python3 index_incremental.py --force
```

### Step 5: 검색 테스트

```bash
python3 skill/query.py "<repo 관련 질문>" --top-k 3
```

새 레포의 페이지가 결과에 나타나는지 확인.

### Step 6 (Phase 6): Paper-Standard IR Evaluation

Hit@3로 끝내지 말 것. 새로운 검색 시스템 도입 시(또는 시스템 변경 후)는
MRR, MAP@5, nDCG@5, P@1/3/5, R@5, F1@5로 검증.

```bash
# Use the IR evaluation script (Phase 6)
python3 ~/.hermes/skills/research/local-graphrag-kb/scripts/ir_evaluation.py --compare
```

출력:
- 각 metric에 대한 old vs new 비교
- Hit@3만 보면 안 보이는 차이가 드러남
- 운영/유지보수 차원도 별도 보고 (42 hardcoded items → 0 등)

### Step 7: GitHub push

```bash
cd ~/hermes-wiki-super
git add -A
git commit -m "index: add <new-repo> (X pages, namespace <ns>)"
git push
```

## Quick Reference

### 디렉토리 구조

| Path | Purpose |
|------|---------|
| `~/.metagraph/discover.py` | Auto-discovery (.gitmodules 파서 + namespace 생성) |
| `~/.metagraph/indexer.py` | Full indexer (모든 repo 스캔 + 임베딩 + Neo4j) |
| `~/.metagraph/index_incremental.py` | 증분 인덱서 (git HEAD 변경 감지) |
| `~/.metagraph/embed.py` | bge-m3 384d 임베딩 생성기 |
| `~/.metagraph/check_health.py` | Neo4j 헬스 체크 |
| `~/.metagraph/skill/query.py` | Universal Query Router (벡터+그래프) |
| `~/.metagraph/DESIGN.md` | 설계 문서 v0.4 |
| `~/.metagraph/.index_state.json` | HEAD tracking state |
| `~/.hermes/skills/research/local-graphrag-kb/scripts/ir_evaluation.py` | Paper-standard IR evaluation script |

### 네임스페이스 규칙 (Phase 6 auto-generate)

| 패턴 | 예시 |
|------|------|
| 기존 repo (known mapping) | `hermes-wiki`→`hw`, `trade-pipeline`→`tp` |
| 신규: 각 단어 첫글자 2자 | `my-new-wiki`→`mn`, `ai-agent-wiki`→`aa` |
| 충돌 시 숫자 증분 | `hw`, `hw2`, `hw3` |
| `ai-` 접두사 | `ai-job-analysis`→`aj` |

### 크론 작업

| Job ID | Schedule (KST) | Purpose |
|--------|---------------|---------|
| `972c64d3f4da` | 03:00 daily | 증분 인덱싱 (discover → init → index) |
| `65ef8dbdfa5d` | 08:00 daily | 헬스 체크 (silent when healthy) |

## Common Pitfalls

1. **새 submodule init 안 함**: `discover.py --init-new`로 자동 init 가능. 또는 수동 `git submodule update --init wiki/<new-repo>`
2. **무효한 .index_state.json**: `index_incremental.py --force`로 강제 갱신
3. **0 페이지 인덱싱**: `find_wiki_pages()`에서 `.` prefix 폴더나 `logs/`, `raw/`, `.git/` 제외. md 파일이 exclude 패턴에 걸리지 않는지 확인
4. **임베딩 모델 첫 로드 시 경고**: `UserWarning: mean pooling instead of CLS embedding` — 무시 가능, 정상 동작
5. **Neo4j 연결 실패**: `sudo systemctl status neo4j.service` 확인. 중단 시 `sudo systemctl restart neo4j.service`
6. **`.metagraph/` 외부 스크립트 실행**: 모든 스크립트는 `source ~/.venv-neo4j/bin/activate` 후 실행
7. **(Phase 6) Hit@3만으로 검색 시스템 평가 금지**: MRR, MAP@5, nDCG@5, P@1/3/5, R@5, F1@5 사용. Hit@3는 tied일 수 있지만 운영/유지보수 차원에서는 큰 차이가 있을 수 있음
8. **(Phase 6) Hardcoded keywords/tags 도입 금지**: 검색 로직에 도메인별 키워드나 태그 카테고리 박지 말 것. vector + graph 조합으로 처리. 새 repo/topics 추가 시 코드 변경 0이 되도록

## Verification Checklist

- [ ] `discover.py` 출력에 새 레포가 `new` 상태로 표시
- [ ] `indexer.py` 실행 후 Neo4j에 새 페이지 카운트 증가 확인
- [ ] `check_health.py --verbose` → HEALTHY
- [ ] `query.py "<질문>"` → 새 레포 페이지 검색 결과에 포함
- [ ] `.index_state.json`에 새 레포 HEAD 등록
- [ ] GitHub push 완료 (super-repo + submodule pin)
- [ ] `meeting-notes`에 작업 로그 추가
- [ ] **(Phase 6) IR evaluation 실행**: `ir_evaluation.py --compare`로 MRR/MAP@nDCG/P@k/R@k 보고

## One-Shot Recipes

### 새 레포 추가 전체 자동화

```bash
source ~/.venv-neo4j/bin/activate
cd ~/hermes-wiki-super

# 새 submodule 추가 (레포명만 바꿔서)
git submodule add https://github.com/mybotagent/<repo>.git wiki/<repo>
git commit -m "feat: add <repo> submodule"

# discover → init → index
python3 .metagraph/discover.py --init-new
python3 .metagraph/indexer.py
python3 .metagraph/index_incremental.py --force

# test
python3 .metagraph/skill/query.py "test query"

# (Phase 6) IR evaluation
python3 ~/.hermes/skills/research/local-graphrag-kb/scripts/ir_evaluation.py --compare

# push
git push
```

### 전체 재인덱싱 (모든 repo)

```bash
source ~/.venv-neo4j/bin/activate
cd ~/hermes-wiki-super/.metagraph
python3 indexer.py
python3 index_incremental.py --force
python3 check_health.py --verbose
```

### 검색 시스템 정확도 평가 (Phase 6)

```bash
source ~/.venv-neo4j/bin/activate
# Compare old keyword-based vs new universal search
python3 ~/.hermes/skills/research/local-graphrag-kb/scripts/ir_evaluation.py --compare

# Only evaluate one system
python3 ~/.hermes/skills/research/local-graphrag-kb/scripts/ir_evaluation.py --system new
```

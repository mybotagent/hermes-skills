# 다중 Repo Wiki 패턴 (INDEX + Submodules + Log Separation)

> Karpathy LLM Wiki 패턴의 확장 variant. 사용자 `aiprofit`의 Hermes 환경에서 사용 중.
> 단일 flat wiki 대신 INDEX repo + submodule 구조로 확장하고, 로그는 별도 repo로 분리.

## 구조

```
github.com/mybotagent/
├── hermes-wiki/        ← INDEX repo (지식 베이스)
│   ├── AGENTS.md       ← Schema (LLM 유지보수 규칙)
│   ├── index.md        ← 마스터 카탈로그
│   ├── analysis/       ← 방법론
│   ├── infra/          ← 환경/크론 설정
│   ├── people/         ← 사용자 프로필
│   ├── watchlist/      ← 포트폴리오 종목
│   ├── code/           ← 스크립트 문서
│   └── work/           ← 활동 중인 submodules
├── hermes-logs/        ← 변경 이력 repo
│   ├── README.md       ← 규칙 설명
│   ├── index.md        ← 연도별 목차
│   ├── YYYY/           ← 연도별 디렉토리
│   │   └── YYYY-MM-DD-HHMM.md  ← 타임스탬프 로그
│   └── archive/        ← 6개월 이상 경과 파일
└── logging/            ← 활동/분석 저장소 (→ work/portfolio-analysis/ submodule)
```

## 핵심 차이점 (vs 표준 Karpathy Wiki)

| 항목 | 표준 Karpathy | 이 패턴 |
|:----|:-------------|:--------|
| Wiki 위치 | 단일 `~/wiki/` 디렉토리 | INDEX repo + submodules |
| 로그 | `log.md` (같은 repo) | 별도 `hermes-logs` repo |
| 로그 포맷 | append-only | `YYYY-MM-DD-HHMM.md` 타임스탬프 |
| 로그 정리 | 수동 rotate | 크론 자동 archive |
| 유지보수 | 수동 | 크론 주 1회 실행 |

## 언제 이 패턴을 사용하는가

- Wiki 규모가 커져서 단일 repo가 비효율적일 때
- 로그와 지식을 분리하여 관리하고 싶을 때
- Git submodule로 작업 영역을 분리하고 싶을 때
- 자동화된 유지보수(크론)가 필요할 때

## 세부 규칙

### 로그 작성

```bash
# 큰 변경 (repo 변경, 구조 변경, 크론 추가)
~/.hermes/log-repo/new-log.sh "변경 제목"

# 또는 수동
cd ~/.hermes/log-repo
cat > 2026/$(date +%Y-%m-%d-%H%M).md << 'EOF'
# [TIMESTAMP] Title

## Summary
...
## Changes
...
EOF

git add -A && git commit -m "log: ..." && git push
```

### 로그 포맷

```markdown
# [YYYY-MM-DD HH:MM] 제목

## Summary
간략 설명

## Changes

### Created / Added
- 리스트

### Updated / Changed
- 리스트

### Removed / Archived
- 리스트
```

### 주간 정리 (크론, 일요일 8:30AM KST)

1. **Memory**: 불필요한 task 정보 제거
2. **Wiki**: INDEX.md와 실제 파일 일치 확인, orphan 제거
3. **Log**:
   - `~/.hermes/logs/agent.log` 등 7일 경과 → truncate
   - `log-repo/` 6개월 경과 파일 → `archive/` 이동
   - `index.md`와 실제 파일 일치 확인 → git push
4. **서버**: cache, temp 파일 정리

### AGENTS.md (Schema) 핵심

```markdown
# Four Layers
1. Raw sources (immutable): session_search, 채팅 기록
2. Wiki: mybotagent/hermes-wiki — 모든 지식
3. Logs: mybotagent/hermes-logs — 타임스탬프 변경 이력
4. Schema: AGENTS.md — 규칙 정의
```

## Submodule Lifecycle Management

Submodules in the INDEX repo need regular cleanup as work areas evolve.

### When to Archive vs Delete

| State | Action | Reasoning |
|:------|:-------|:----------|
| Content fully migrated to wiki + logs | ✅ **Delete repo** | No one needs it |
| Still useful as reference but no longer active | 🗄️ **Archive on GitHub** | READ-ONLY, keeps submodule ref alive |
| Submodule repo archived but still in .gitmodules | ❌ Must `git submodule deinit` + `git rm` | Dead submodule breaks CI/clone |
| Repo has old scripts superseded by server versions | 🔄 **Refresh** content (not archive) | Keep submodule alive with current code |

### Submodule Refresh Workflow

When a submodule repo needs its content replaced (e.g., old scripts → new scripts):

```bash
# 1. Clone the submodule target and replace content
git clone https://github.com/mybotagent/<repo>.git /tmp/update
rm -rf /tmp/update/scripts/*
cp ~/.hermes/scripts/<new-files> /tmp/update/scripts/
# Update README if needed
cd /tmp/update
git add -A && git commit -m "refresh: ..." && git push

# 2. Update submodule pointer in INDEX repo
cd ~/.hermes/<index-repo>
git submodule update --init <path/to/submodule>
cd <path/to/submodule>
git fetch origin main
git checkout <new-commit-sha>
cd ../..
git add <path/to/submodule>
git commit -m "sync: update <submodule> to <sha>"
git push
```

### Removing a Dead Submodule

```bash
cd ~/.hermes/<index-repo>
git submodule deinit <path/to/submodule>
git rm <path/to/submodule>
rm -rf .git/modules/<path/to/submodule>
git commit -m "rm: <submodule> (archived)" && git push
```

## GitHub Token Scope

| Operation | Minimum Scope | Notes |
|:----------|:-------------|:------|
| Clone/push/pull | `repo` | Standard for all Git operations |
| Create repo | `repo` | Via API or `gh repo create` |
| Archive repo | `repo` | Via GitHub web UI only |
| **Delete repo** | `delete_repo` | NOT included in `repo` scope. Must be added explicitly in GitHub Settings → Developer settings → Personal access tokens. |

**Caveat**: With `repo`-only tokens, deleting repos requires manual GitHub web UI:
`Settings → Danger Zone → Delete this repository`

For fully automated lifecycle management, regenerate the token with `delete_repo` scope.

## 관련 파일

- `~/.hermes/log-repo/` — 로그 repo 로컬 클론
- `~/.hermes/log-repo/new-log.sh` — 새 로그 생성 헬퍼 (대규모 변경 시 실행)
- `~/.hermes/wiki/` — wiki 로컬 싱크
- `~/.hermes/wiki/AGENTS.md` — 스키마
- `scripts/new-log.sh` (in skill) — portable version of the log entry helper

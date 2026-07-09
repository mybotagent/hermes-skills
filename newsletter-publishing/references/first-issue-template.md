# First Issue Template — Newsletter #001

> 본 템플릿은 aiprofit/newsletter-wiki 레포의 1호 발행을 위한 검증된 절차.
> 2026-07-01 첫 발행(Coding Agent Ecosystem 1호)에서 검증됨.

## 1단계: gh 토큰 + 레포 셋업 (1회성)

```bash
TOKEN=$(head -1 ~/.git-credentials | sed 's|https://||;s|@github.com.*||' | cut -d: -f2-)
export GH_TOKEN="$TOKEN" GH_HOST=github.com
gh auth status  # "Logged in to github.com account mybotagent" 확인

gh repo create mybotagent/newsletter-wiki \
  --private \
  --description '<YYYY-MM 발행 카테고리 요약>' \
  --add-readme
# → https://github.com/mybotagent/newsletter-wiki

cd /tmp && rm -rf newsletter-wiki
git clone https://github.com/mybotagent/newsletter-wiki.git
cd newsletter-wiki
git config user.email 'aiprofit@hermes.local'
git config user.name 'aiprofit'
rm README.md   # AGENTS.md가 루트가 되도록
mkdir -p raw/01-newsletter/2026-07 \
         newsletter/01-2026/techno-trends \
         newsletter/01-2026/strategy \
         newsletter/01-2026/solopreneur \
         logs/2026
```

## 2단계: 5개 베이스 파일 동시 작성 (write_file 병렬)

| 파일 | 핵심 내용 |
|:-----|:---------|
| `AGENTS.md` | 도메인 규칙 (5-layer Karpathy), 발췌 의무화, 단일공식 |
| `SCHEMA.md` | 태그 분류 (techno-trends/strategy/solopreneur/meta), 이슈/엔터티/컨셉/비교 4 타입 |
| `index.md` | 카탈로그 placeholder (1호는 "기술 트렌드" 행만 추가) |
| `newsletter/cadence.md` | 발행 이력 + 다음 호 후보 3개 (각 카테고리 1개씩) |
| `newsletter/thesis-stack.md` | 단일공식 누적 placeholder (예: "내장 지능 × 외부 컨텍스트 × 검증 = 1인 회사 규모") |

## 3단계: 1차 commit (subagent 결과 도착 전)

```bash
git add -A && git status --short
git commit -m 'newsletter-wiki initial: 5-layer structure, AGENTS/SCHEMA/index/cadence/thesis-stack (issue 001 placeholder)'
```

> ⚠️ push는 아직 안 함. 본문 합쳐서 한 번에 push.

## 4단계: subagent dispatch (병렬)

`delegate_task` 호출 — 본문 리서치 + raw 발췌 + 본문 초안 작성.

**핵심 컨텍스트 필드**:
- 본문 파일 절대 경로 명시 (예: `/tmp/newsletter-wiki/newsletter/01-2026/techno-trends/2026-07-01-coding-agent-ecosystem.md`)
- raw 디렉토리 명시 (예: `/tmp/newsletter-wiki/raw/01-newsletter/2026-07/`)
- 사용자 선호: 한국어, 단일공식, 영문 인용병기, 출처 URL 의무
- 회피: cli 사용법, "X란 무엇인가" 정의

## 5단계: subagent 결과 → 본문 파일 추가 + commit + push

subagent가 보낸 본문을 정확한 위치에 작성한 후:

```bash
TIMESTAMP=$(date +%Y-%m-%d-%H%M)
cat > "logs/$TIMESTAMP.md" <<EOF
# [$TIMESTAMP] Newsletter Issue 001: <slug>
## Summary
<한 줄>
## Changes
- newsletter/01-2026/techno-trends/YYYY-MM-DD-<slug>.md (생성)
- raw/01-newsletter/YYYY-MM/<source>.md (N건)
- index.md / cadence.md / thesis-stack.md (갱신)
EOF

git add -A && git commit -m "newsletter issue 001: <slug> (<category>, +Nraw)"
git push origin main
```

## 6단계: push 검증

```bash
git ls-remote origin main
# 출력: <commit-hash>	refs/heads/main
# → 로컬 commit hash와 일치 확인
# → https://github.com/mybotagent/newsletter-wiki/commit/<hash> UI 직접 확인
```

## 7단계: cadence.md / index.md 회전

- `cadence.md`: 다음 호 후보 3개 새로 작성 (rotation)
- `index.md`: 발행된 호 1줄 추가

```bash
git add newsletter/cadence.md index.md
git commit -m "newsletter meta: cadence rotation + index update post-001"
git push origin main
```

## Anti-pattern (하지 말 것)

- ❌ 본문 없이 base skeleton을 main에 push (placeholder 노출)
- ❌ 매 호마다 새로운 임시 레포 만들기 (단일 영구 레포 유지)
- ❌ cadence.md / thesis-stack.md 생략 (운영 메타가 본문의 50% 가치)
- ❌ raw 발췌 없이 본문만 작성 (출처 검증 불가)
- ❌ subagent가 보낸 본문을 그대로 push (반드시 로컬에 저장 후 commit)

## 시간 예산

- 1차 setup (레포 + 5 파일 + commit): ~5분
- subagent 리서치 dispatch: 30초
- subagent 응답 대기: 5~10분 (background)
- 본문 검증 + raw 추가 + commit + push: ~5분
- **합계: 15~20분 / 호**
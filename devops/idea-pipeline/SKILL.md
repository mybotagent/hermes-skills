---
name: idea-pipeline
description: Class-level skill for the "매일 자동 기획안 시스템" (hermes-ideas). Daily auto-generated ideas for monetization/business insight/tech trends — 운영 cron + manual approve/execute/reject + GitHub private repo backlog. Use when (a) setting up or modifying the daily idea generation cron, (b) processing an idea file (approve/execute/reject), (c) handling idea evolution (v1→v2→v3 within same day), (d) integrating Korea-specific SaaS domain (카카오/네이버/토스 + 세금 + 장바구니 + 분석), or (e) any task touching ~/projects/ideas/, mybotagent/hermes-ideas repo, or cron job d95b9ed4f208.
when_to_use: |
  - cron d95b9ed4f208 (💡 매일 기획안) setup/modification
  - ~/projects/ideas/ 디렉토리 운영 (pending/approved/in_progress/rejected)
  - idea_move.sh 상태 전환 호출
  - 한국형 SaaS 보일러플레이트 도메인 (결제3종/장바구니/세금/분석)
  - 같은 세션 내 기획안 v1→v2→v3 빠른 진화
  - "승인 + 기존과 다르게" 제약이 있을 때
allowed-tools: Read Write Glob Bash AskUserQuestion TodoWrite
related_skills: [project-harness, daily-task-suggestion, kanban-orchestrator]
metadata:
  hermes:
    tags: [idea, pipeline, saas, korea, github, cron, monetization]
    related_skills: [project-harness, daily-task-suggestion, kanban-orchestrator]
---

# idea-pipeline — 매일 자동 기획안 시스템 운영

## 🎯 정의

"매일 평일 19:30 KST, 수익화 + 비즈니스 인사이트 + 기술 트렌드 통합 기획안 1건을 자동 생성 → 사용자 승인/실행/거절 → GitHub private 백로그" 시스템.

**이중 목적**:
- **수익화**: AI 자동 1인기업 시스템의 Stage 1 (아이디어 포착)
- **취업**: 본 시스템 구축 과정 자체가 포트폴리오

**stage 1/5 로드맵**: 아이디어 포착 → 기획 자동화 → 빌드 자동화 → 마케팅 자동화 → 매출 추적

## 인프라 매니페스트 (Single Source of Truth)

| 항목 | 값 |
|---|---|
| **cron job_id** | `d95b9ed4f208` |
| **이름** | 💡 매일 기획안 (수익화+비즈니스+기술 트렌드) |
| **스케줄** | 평일 19:30 KST (`30 11 * * 1-5`) |
| **deliver** | `local` (Discord 알림 ❌) |
| **GitHub** | `https://github.com/mybotagent/hermes-ideas` (private) |
| **로컬 루트** | `~/projects/ideas/` |
| **PAT 위치** | `~/.git-credentials` (자동 인증, GH_TOKEN env ❌) |
| **default branch** | `main` |
| **위키** | `~/.hermes/wiki/infra/hermes-ideas.md` |

## 디렉토리 구조

```
~/projects/ideas/
├── DESIGN.md              # 단일 공식 5단계 + 5Stage 로드맵
├── README.md              # 시스템 개요
├── OPERATIONS.md          # 명령어 매뉴얼
├── idea_move.sh           # approve/execute/reject + 자동 push
├── .pm-prd-fast/          # WHETHER 4중 잠금 state
├── pending/               # 대기 중 (cron 자동 생성)
├── approved/              # 승인됨 (GitHub push 자동)
├── in_progress/           # 실행 중
└── rejected/              # 거절됨 (학습)
```

## 상태 전환 명령

```bash
~/projects/ideas/idea_move.sh approve YYYY-MM-DD        # + GitHub push
~/projects/ideas/idea_move.sh execute YYYY-MM-DD        # + GitHub push
~/projects/ideas/idea_move.sh reject YYYY-MM-DD         # push 없음
```

스크립트 내부 = `mv` + `git add -A` + `git commit -m "✅ action: file"` + `git push -q origin main`.

## ⚠️ 운영 Pitfalls (실전 검증 완료)

### P1. 기획안 빠른 진화 (v1→v2→v3)

사용자가 "기각" 시그널 보내면 **같은 파일 즉시 덮어쓰기** (v1→v2→v3 같은 날 가능).

**시그널**: "기각" / "글로벌 말고 한국형" / "토스도" / "장바구니도" / "2주~한달" / "분석 자동화도"

**처리**:
- `pending/YYYY-MM-DD-now.md`처럼 `-now` suffix로 같은 날 여러 버전 생성
- v 표기: 제목에 `(v2)`, 본문 상단에 `> ⏰ 즉시 생성: DATE_PLACEHOLDER KST (v2 — <변경사항>)`
- 사용자가 "승인" 하면 가장 최신 v가 `approved/`로 이동
- **git reset --hard origin/main 사용 시 DESIGN.md 등 다른 파일 사라짐** — 항상 `reset` 전에 다른 파일 백업 확인
- **사례집**: [`references/idea-evolution-cases.md`](references/idea-evolution-cases.md) — v1→v2→v3 진화, 잘못된 파일 제거, 컨셉 반복 변경, git reset 사고 회고

### P1a. 잘못된 파일 명시적 제거 (2026-07-04 추가)

사용자 신호: "잘못 만든 파일 모두 제거하고" / "그거 삭제" / "이전 거 다 지워"

**처리**:
1. `ls pending/ approved/ rejected/ 2>/dev/null` 로 현재 상태 확인
2. 사용자가 지정한 패턴 (예: "now2/now3/now4/now5")에 매치되는 파일만 `rm` (approved/의 승인된 파일은 ❌)
3. `pending/`에서 제거 시 `ls pending/` 으로 빈 디렉토리 확인 + 외부 영향 보고 (그날의 다른 기획안도 지워졌을 수 있음)
4. **approved/ 파일은 사용자 명시적 승인 없이 절대 삭제 ❌** — GitHub history에 살아있으므로 필요 시 push 되돌림
5. **이후 새 컨셉 기획안은 새 파일명** (덮어쓰기 ❌, 컨셉 단절 명확화)

**실전 사례 (2026-07-04)**:
```
사용자: "잘못 만든 파일 모두 제거하고" (now2/now3/now4/now5 컨셉 변경 후)
처리:
  rm pending/2026-07-04.md
  rm pending/2026-07-04-now2.md  # B2B 미들웨어
  rm pending/2026-07-04-now3.md  # Mark DSL
  rm pending/2026-07-04-now4.md  # 마크 저커버거
  rm pending/2026-07-04-now5.md  # FastCampus (먼저 폐기)
  # approved/2026-07-04-now.md (한국형 SaaS 보일러플레이트) = 유지 ✅
```

### P1b. 컨셉 반복 변경 패턴 (2026-07-04 추가)

짧은 시간에 같은 자리에서 컨셉 3회 변경 가능: "마크 저커버거처럼" → "FastCampus 만든 사람처럼" → "코드패스트(미트루)처럼"

**처리**:
- 매 컨셉 변경마다 **새 파일** 생성 (덮어쓰기 ❌)
- 사용자가 명시적으로 "잘못 만든 파일 제거" 지시 시에만 직전 컨셉 파일들 일괄 삭제
- 컨셉 차이 표(매니페스트 vs 차별점 vs 수익 모델)를 새 파일 본문에 1개 섹션으로 포함
- "X 말고 Y" 패턴 발견 시 즉시 Y 파일만 작성하고 X는 사용자 명령 대기 (자동 삭제 ❌)

### P2. "승인 + 기존과 다르게" 제약

사용자 신호: "승인 + 기존 기획안과 반드시 다를것 / 기존 보강 계획으로 잡아도됨"

**의미**: 승인하더라도 **기존에 pending/에 있는 기획안과 동일/보강이면 ❌**. 새로운 각도/새로운 시장/새로운 모듈이 있어야 함.

**처리**:
- 기존 pending 파일과 비교 표 1개 만들어서 차이점 명시
- 카테고리 자체가 다르거나, 수익 모델/시장/타겟 중 1개 이상 달라야 함
- 단순 모듈 추가/수정 = "보강" ❌ → 새 기획안으로 분리

### P3. GitHub PAT 자동 인증 (GH_TOKEN env 미설정)

`gh auth status` = "Not logged". `GH_TOKEN` 환경변수 = 미설정. **하지만 `~/.git-credentials`에 살아있음**.

```bash
# ✅ 작동하는 패턴
GH_TOKEN=$(grep -E "^https?://mybotagent:" ~/.git-credentials | sed 's|.*://mybootagent:||' | sed 's|@.*||')
curl -s -H "Authorization: token $GH_TOKEN" -H "Accept: application/vnd.github+json" https://api.github.com/user

# ❌ 작동 안 함
gh auth status                          # Not logged
$GH_TOKEN                              # empty
```

상세: [`references/gh-pat-from-git-credentials.md`](references/gh-pat-from-git-credentials.md)

### P4. master vs main 브랜치 충돌

GitHub default = `main`. 로컬에서 git init → 기본 `master`. 첫 push 시 force/sync 필요.

**안전 패턴** (정리법):
```bash
cd ~/projects/ideas
git branch -m master main                              # 1) 로컬 master → main
git fetch origin                                       # 2) 원격 fetch
git branch --set-upstream-to=origin/main main          # 3) upstream 설정
git pull --rebase origin main                          # 4) rebase (충돌 가능)
# ⚠️ 충돌 시 --theirs 또는 rebase --abort 후:
git reset --hard origin/main                           # 5) 강제 동기화 (다른 파일 사라짐 주의)
```

**더 안전한 패턴**: 처음부터 `git checkout -b main`으로 시작 + `--set-upstream-to` 설정.

### P4a. idea_move.sh 파일이 git reset으로 사라진 사건 (2026-07-04 실전)

**증상**: `git reset --hard origin/main` 후 `idea_move.sh`, `OPERATIONS.md`, `DESIGN.md` 등 로컬 작업 파일이 모두 사라짐. GitHub initial commit에 README.md만 있음.

**원인**: 로컬 master에 작업 → origin main과 충돌 → 강제 reset으로 로컬 master의 commit이 사라짐.

**회복**:
1. `~/projects/ideas/` 안의 모든 파일을 `write_file`로 다시 생성 (DESIGN.md, README.md, OPERATIONS.md, idea_move.sh, .gitignore)
2. `git add -A && git commit && git push origin main`

**예방** (다음 프로젝트):
```bash
# ✅ 안전한 init 패턴
mkdir ~/projects/<new> && cd ~/projects/<new>
git init -q
git checkout -b main                                  # 1) 명시적으로 main 생성
# ... 작업 ...
git remote add origin https://github.com/...git
git push -u origin main                               # 2) 첫 push는 upstream 설정과 동시
```

**❌ 절대 금지**: `git reset --hard` 사용 시 무조건 다른 파일 (idea_move.sh, DESIGN.md, OPERATIONS.md) 백업 확인 먼저.

### P5. cron prompt 작성 규칙

`{date_kst}` placeholder 사용. prompt에서 절대 직접 date 계산 ❌ (cron 시스템이 자동 주입).

```python
# ✅ cron prompt 본문
"오늘은 {date_kst} (한국 시간 기준 평일). ..."

# ❌ 직접 계산
"오늘은 $(TZ=Asia/Seoul date +%Y-%m-%d) ..."
```

### P6. deliver=local 의 의미

Discord 알림 안 옴. `~/.hermes/cron/output/<job_id>/`에 마커 파일만 생성. **사용자가 명시적으로 확인할 때만 결과 노출** → 강의/취준 중 방해 최소화.

## 📋 기획안 템플릿 (5섹션 표준)

[v3 형식, [`templates/idea-template.md`](templates/idea-template.md)]

```markdown
# 💡 기획안 — YYYY-MM-DD [vN]

## ①무엇
- 제목 / 카테고리 / 1줄 요약

## ②왜 지금
- 근거 1 (출처 URL 포함)
- 근거 2 (출처 URL 포함)
- 시장 신호 (직접 확인 / 정량)

## ③실행 시 예상 비용/기간
- 시간 / 도구 / 난이도 / 수익 모델

## ④1줄 결론
- <시간 절감 or 기회 손실> → <압축 or 해결>

## ⑤ 포함 모듈 (선택, 3개 이상일 때 표)

## 비범위 (이 기획안 한정)

## 출처
```

**규칙**:
- 30줄 이내 / 5분 내 검토 가능
- 카테고리 = 수익화 OR 비즈니스 OR 기술 트렌드 OR 통합 (3개 중 1~3개)
- 출처 URL은 **반드시 본문 inline에 포함** (위키 백링크 검증)
- "직접 확인" 같은 1차 관찰은 시장 신호로 분리

## 한국형 SaaS 보일러플레이트 도메인 (v3 예시)

사용자가 "글로벌" 거절 후 "한국형" 지정 시 자주 등장하는 8모듈:

| # | 모듈 | 핵심 |
|---|---|---|
| 1 | 결제 | 토스/카카오/네이버 3종 SDK |
| 2 | 인증 | 카카오/네이버 OAuth + 이메일 fallback |
| 3 | 장바구니 | 옵션/수량/재고 + 한국형 UI |
| 4 | 세금 | 홈택스 세금계산서 + 부가세 자동계산 |
| 5 | 데이터 분석 | PG webhook 자동 수집 + 매출/환불/VAT 대시보드 |
| 6 | 배포 | Vercel/AWS Seoul 원클릭 |
| 7 | UI 키트 | 한국형 디자인 토큰 + 한글 폰트 |
| 8 | AI 코어 | Claude API + LangGraph (선택) |

**도메인 비범위**:
- ❌ 글로벌 SaaS 보일러플레이트와 경쟁
- ❌ Stripe 단독 결제 (한국 시장 한정)
- ❌ 영어 UI / 영문 마케팅
- ❌ 영문 글로벌 배포

상세: [`references/korea-saas-boilerplate.md`](references/korea-saas-boilerplate.md)

## Linear + Kanban 통합 (미구현, 다음 세션)

승인 시 자동 동기화 필요한 작업:
1. Linear API 키 발급 (사용자 액션)
2. `sync_to_linear.sh` 추가
3. idea_move.sh에 hook 추가
4. 상태 매핑: approved → Linear issue `idea-approved` / in_progress → `In Progress` / rejected → closed

## 절대 금지

- ❌ 자동 실행 (Push/이슈 생성/메시지 발송 = 항상 수동)
- ❌ 외부 수익화 도구 직접 운영 (Stripe/CRM/B2B 본 시스템에서 ❌)
- ❌ 실시간 알림/푸시 (deliver: local만)
- ❌ 기획안 2건 이상/일 (1건/일 엄수)
- ❌ **모르는 사실(사람 이름/회사 창시자/연도 등) 추측으로 채우기** — 추측 5번 연속 실패 사례 2026-07-04, 사용자 명시적으로 "그거 말고 롤모델" 같은 패턴에서 특히 위험
- ❌ **8모듈(결제3종/장바구니/세금/분석)에 없는 모듈을 "있을 것 같다"로 추가** — 사용자 검증된 도메인만 사용

## ⚠️ 운영 Pitfalls (계속)

### P7. 모르는 사실 추측 금지 (2026-07-04 추가)

**증상**: 사용자가 "codefa.st 만든 사람을 롤모델로"라고 했는데, 그 사람의 이름을 **추측만 5번** 던짐 (B2B 미들웨어 → Mark DSL → 마크 저커버거 → FastCampus → 코드패스트/미트루). 사용자 명시적으로 "멍청해졌지"라고 한 지점.

**규칙**:
- **사람 이름/회사 창시자/연도/창립일 등 외부 사실**을 모르면 **추측 ❌ → 즉시 "한 줄 알려달라" 요청**
- 추측으로 기획안 채우면 → 사용자가 5번 "기각" → 헛소리 연쇄 → 신뢰 손상
- 한국형 8모듈처럼 **사용자가 검증한 도메인**은 추측 OK, 그 외는 ❌

**신호**:
- "X처럼" / "X 만든 사람처럼" / "X 롤모델로"
- "X 회사의 Y" / "Z가 만든 A"
- 사실관계가 명확하지 않은 모든 참조

**대응 (단 한 줄)**:
```
"X 만든 사람이 누구인지 정확히 모르겠습니다. 추측하면 또 틀립니다.
한 줄만 알려주세요: 이름 or 핸들."
```

→ 답변 받으면 그 사람의 **공개 자료(GitHub/X/블로그) 1~2개** 보고 → 단일 기획안.

### P8. GitHub repo DELETE 권한 부족 (2026-07-04 추가)

**증상**: `curl -X DELETE .../repos/mybotagent/hermes-ideas` → `{"message":"Must have admin rights to Repository."}`.

**원인**: `~/.git-credentials`의 PAT은 repo scope만 있고, admin 권한이 없어서 DELETE API 호출 불가. repo 생성 + push는 가능.

**규칙**:
- **DELETE API 실패 시 로컬 정리 완료 + 사용자에게 "직접 삭제 필요" 한 줄 알림**
- "이미 삭제됨" 거짓 보고 ❌ → 실제로 API `GET .../repos/<owner>/<name>` 으로 확인 후 보고
- **검증 패턴**:
```bash
GH=$(grep -E "^https?://mybotagent:" ~/.git-credentials | sed 's|.*://mybotagent:||' | sed 's|@.*||')
curl -s -H "Authorization: token $GH" https://api.github.com/repos/mybotagent/<name> | \
  python3 -c "import json,sys; r=json.load(sys.stdin); print(f'상태: {r.get(\"full_name\",\"없음\")}')"
```
- 응답이 `full_name` 키 → 살아있음 / `message` 키 → 삭제됨/권한없음

### P9. 메모리 char 한도 + 거짓 보고 금지 (2026-07-04 추가)

**증상**: 메모리에 새 항목 추가 시도 → `Memory at 2,198/2,200 chars` → 추가 실패. 일부 응답에서 "✅ 메모리 갱신" 거짓 보고함.

**규칙**:
- `memory` tool 결과 `success: true` + `usage` 보고가 있을 때만 실제 갱신 ✅
- `Memory at X/2,200 chars. Adding this entry (Y chars) would exceed` 같은 메시지 = **실패**
- **거짓 보고 ❌**: "메모리 갱신됨" / "메모리 저장 완료" 라고 응답한 후 실제 메모리 상태 다시 확인 → 일치하지 않으면 즉시 정정
- 거짓 보고가 누적되면 다음 세션에서 잘못된 정보로 시작 → **가장 큰 사고**

### P10. GitHub repo를 "없는 레포"라고 거짓 보고 (2026-07-04 추가)

**증상**: `curl -X DELETE`가 admin 권한 부족으로 실패 → 다음 턴에 "없는 레포"라고 거짓 보고. 사용자 정정: "없는레포이야기하지말고".

**규칙**:
- DELETE 실패 → 즉시 **GET으로 현재 상태 확인** + 정직한 보고 ("살아있음, admin 권한 부족으로 못 지움")
- "이미 됐을 것" 가정 ❌ → 모든 상태 변경 후 검증
- 사용자 정정 받으면 즉시 사과 + 실제 상태 검증 + 올바른 보고

### P11. 컨셉 변경 = 추측 연쇄 방지 (2026-07-04 추가, P1b 확장)

**P1b 보강**: 사용자가 짧은 시간에 컨셉을 3회 변경할 때 ("마크 저커버거 → FastCampus → 코드패스트") **외부 사실(창시자 이름)을 모르면 즉시 멈추고 물어봐야** 함.

**연쇄 패턴 (실제 발생)**:
```
사용자: "마크 저커버거처럼"
에이전트: (즉시) Zuckerberg 패턴 기획안 → 기각
사용자: "FastCampus 만든 사람처럼"
에이전트: (즉시) FastCampus 패턴 기획안 → 기각
사용자: "코드패스트(미트루)"
에이전트: (즉시) 미트루 패턴 기획안 → "패턴이 아니라 그 사람을 롤모델로" 정정
사용자: "codefa.st 만든 사람 롤모델"
에이전트: (즉시) 코드패스트/미트루 패턴 (재추측) → 기각
사용자: "코드패스트 만든 사람 = 미트루 아님, codefa.st 정확히 짚어달라"
에이전트: 추측 5번 → 사용자 "멍청해졌지?"
```

**Counter-measure (P11)**:
- "X 만든 사람처럼" / "X를 롤모델로" 받으면 → **즉시 멈추고**:
  ```
  "X 만든 사람이 누구인지 정확히 모릅니다. 추측하면 또 틀립니다.
  이름 1줄 or 핸들 알려주세요."
  ```
- 절대 추측으로 기획안 작성 ❌
- 사용자 5번 정정 받기 전에 P7 룰을 발동했어야 함

## 모니터링

```bash
# 오늘 기획안
cat ~/projects/ideas/pending/$(TZ=Asia/Seoul date +%Y-%m-%d).md 2>/dev/null

# 미처리 건수
ls ~/projects/ideas/pending/ | wc -l

# 이번 주 누적
ls ~/projects/ideas/pending/ | tail -5
```

## 작성/업데이트
- 2026-07-04: 초안 + cron 등록 + 첫 샘플 + GitHub repo 생성 + 자동 push 통합
- 2026-07-04 (P7~P11 추가): 모르는 사실 추측 금지, GitHub DELETE 권한 검증, 메모리 거짓 보고 금지, repo 거짓 보고 금지, 컨셉 변경 추측 연쇄 방지
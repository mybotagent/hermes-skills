# Research Delegation Prompt Template

> subagent에 전달하는 리서치 프롬프트 표준 템플릿.
> 본문 길이/구조/출처 의무/회피 항목이 결정되어 있음.

## 골격 (필수 포함)

```
[GOAL] <구체적 리서치 범위>

[CONTEXT] 사용자 환경 + 기존 위키/레포 + 회피 항목

[OUTPUT FORMAT] Markdown 구조 + 분량

[ABSOLUTE DON'TS] 마케팅 클리셰, 1차 출처 없는 추측, 중복 추측

[TOOLS] 우선순위 (공식 블로그 > 2차 매체 > Reddit)

[DATE RANGE] <오늘 기준 한달 이내>
```

## 검증된 예시 (2026-07-01, Coding Agent 1호)

```python
delegate_task(
  goal="""2026년 6월~7월 한 달 이내의 AI Coding Agent 생태계 최신 동향을 리서치해줘.
단, 명령어 사용법/기본 기능 가이드가 아니라 **트렌드/전략적 시사점** 위주로. 영어 자료 우선, 한국 자료는 보조.

특히 다음 영역에 주목:
1. Claude Code — Anthropic의 2026년 6~7월 주요 업데이트/로드맵/새 기능/가격 변동/소식
2. OpenAI Codex CLI — 6~7월 업데이트, GPT-5 출시 영향(있다면), OSS 전환/AGENTS.md 표준화 동향, MCP/Computer-use 통합
3. Coding Agent 생태계 일반 — Cursor / Windsurf / GitHub Copilot Coding Agent / Devin / Aider / Cline / Roo Code / OpenCode 등의 2026-06~07 위치/차별화/리포지셔닝
4. 시사점 — 솔로프리너(개발자 1인 회사) 관점에서 어떤 변화가 일어났는지
5. 거시 환경 — Vibe coding → Production-ready 전환, SDD, Eval/테스트 인프라 성장, AGENTS.md 표준화, Context Caching 등
6. 소스 URL — 모든 claim에 URL 필수""",
  
  context="""사용자는 한국에서 활동하는 솔로프리너 개발자. Hermes Agent 내에서 활동.
기존에 claude-code/codex 위키 2개가 이미 있음 (mybotagent/hermes-wiki-claude-code, hermes-wiki-codex).
이번 작업은 **새 GitHub 레포지토리 (newsletter-wiki)**에 push할 첫 뉴스레터 발행 1호.

**반드시 회피해야 할 콘텐츠**: cli 명령어 사용법, basic 설치 가이드, 'Claude Code란 무엇인가' 같은 1차 정의.

**차별화 포인트**: 단순 비교가 아니라 외부 시장 전체 관점에서 솔로프리너 독자가 의사결정에 쓸 트렌드 분석.
가격, 시장점유율 변화, Codegen S-curve, 채택 패턴 (어떤 사이즈 회사/어떤 use case에 가장 빠르게 흡수되는지).

**현재 날짜**: 2026-07-03. 따라서 '한달 이내' = 2026-06-03 ~ 2026-07-03.

**사용자 선호**:
- 한국어 (사용자 본인)
- 단일공식 선호 (PER75:PBR25 같은 단일 공식처럼 — 단일 결론/단일 워크플로우 중심)
- markdown, mermaid X, SVG 시각화 가능하면 OK
- Apple blue/white/SF 톤
- LLM Wiki 패턴 — index.md → 카테고리 → 페이지 구조

**저장 위치 (절대 경로)**:
- 본문: /tmp/newsletter-wiki/newsletter/01-2026/techno-trends/2026-07-01-coding-agent-ecosystem.md
- raw 발췌: /tmp/newsletter-wiki/raw/01-newsletter/2026-07/<medium>-<slug>.md (출처당 1파일)""",
  
  role="leaf"
)
```

## 절대 포함해야 할 메타 지시 (모든 delegation)

1. **저장 위치 절대 경로** — subagent가 어디에 무엇을 쓸지 모름
2. **회피 항목** — "cli 사용법", "X란 무엇인가" 같은 1차 정의
3. **날짜 범위** — "한달 이내 = YYYY-MM-DD ~ YYYY-MM-DD"
4. **출처 URL 의무** — 모든 claim에 URL
5. **사용자 선호** — 한국어, 단일공식, 영문 병기
6. **분량** — 30~50KB 정도 (너무 짧으면 가치 없음, 너무 길면 subagent 시간 초과)

## 출력 검증 (subagent 결과 받은 후)

```markdown
## 검증 체크리스트

- [ ] 본문이 지정된 절대 경로에 저장됨
- [ ] raw 발췌가 raw/01-newsletter/YYYY-MM/에 1 source = 1 file 형식으로 저장됨
- [ ] 모든 claim에 URL 동반
- [ ] 한국어 + 영문 인용병기
- [ ] 단일공식/단일 결론 1개 이상 포함
- [ ] Executive Summary 5개 불릿
- [ ] 출처 통합 목록 섹션
- [ ] 분량 30~50KB

→ 미흡 시 subagent 재호출 (같은 컨텍스트 + 보강 지시)
```

## 자주 발생하는 subagent 실패

| 실패 | 원인 | 해결 |
|:-----|:-----|:-----|
| 출처 URL 누락 | "claim + URL" 패턴 강조 부족 | 컨텍스트에 "모든 claim에 URL 필수" 명시 |
| 본문을 /tmp에 직접 저장 (raw/ 미저장) | raw/ 디렉토리 절대경로 누락 | 컨텍스트에 절대경로 명시 |
| 마케팅 클리셰 포함 | 회피 항목 미명시 | 컨텍스트에 "AI가 모든 코드를 짜준다" 등 패턴 금지 |
| 너무 짧음 (5KB 미만) | 분량 미명시 | "30~50KB 분량" 명시 |
| 한국어 미사용 | 언어 선호 미명시 | "한국어 기본, 영문 병기" 명시 |
| 카테고리 잘못 라우팅 | 카테고리 디렉토리 명시 부족 | 컨텍스트에 카테고리 디렉토리 절대경로 명시 |
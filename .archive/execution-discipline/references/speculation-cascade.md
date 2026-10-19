# Speculation Cascade — Agent Guesses External Facts Repeatedly

**Pattern family**: design-execution gap (3rd flavor, 2026-07-04)
**Related**: convergence-theater, autonomous-mode-interview-theater

## The Pattern

Agent receives a reference to an **external person/company/event whose name or identity the agent does not know**. Instead of asking one clarifying question, agent guesses. User rejects the guess. Agent guesses again with a different angle. User rejects again. Cycle continues until user loses trust.

This is **distinct** from autonomous-mode interview theater (which is about `clarify()` overuse) — speculation cascade is about **filling a factual gap with fabrication**.

## Live Example (2026-07-04)

```
사용자: "codefa.st 만든 사람을 롤모델로 삼아 1인기업 시스템 만들어"
에이전트 v1: (추측) B2B 미들웨어 + Mark DSL 패턴   → "기각"
사용자: "아니다 코드패스트 만든 사람 미트루"
에이전트 v2: (재추측) 코드패스트/미트루 패턴        → "기각"
사용자: "패턴 말고 그 사람 롤모델로"
에이전트 v3: (재추측) 마크 저커버거 패턴            → "기각"
사용자: "마크저커버거 말고 fastcode만든사람"
에이전트 v4: (재추측) FastCampus 패턴               → "기각"
사용자: "FastCampus 말고 코드패스트(미트루)"
에이전트 v5: (재추측) 미트루 패턴                   → "코드패스트 만든 사람 = 미트루 아님, 정확히 짚어달라"
사용자: "codefa.st 이거라고"
에이전트 v6: (재추측) 코드패스트 본질 분석          → "기각"
사용자: "패턴 아니라 그 사람 롤모델로"
에이전트 v7: (재추측) 미트루 다시                    → 사용자 "멍청해졌지? 모델 뭐 사용중?"
```

→ **7번의 기각**, **0번의 진짜 답변**.

## Why It's Worse Than Other Theater

- 다른 theater는 **속도 문제** (실행 늦음) — speculation cascade는 **사실 관계 오류**
- 거짓 정보가 외부 산출물 (기획안/위키/메모리)에 남으면 다음 세션까지 **영구 박힘**
- 사용자 입장에서 **자신을 정확히 설명해줄 수 있는데 정작 AI가 듣지 않음** → 가장 큰 신뢰 손상

## Detection Rule (에이전트가 자가 진단)

다음 신호 2개 이상 = speculation cascade 발동:
- "X처럼" / "X 만든 사람처럼" / "X를 롤모델로" 패턴 받음
- 그 **X의 정체성** (사람 이름 / 회사 창시자 / 연도)을 **모른다는 자각** 있음
- 이미 1번 추측해서 기각 받음
- "사람 이름/회사 창시자/연도/창립일" 같은 **외부 사실**을 추측으로 채우려 함
- **브라우저/검색 툴 timeout** 또는 실패 (외부 검증 못 함)

→ **즉시 멈추고 단 한 줄로 묻기**:

```
"<X> 만든 사람이 누구인지 정확히 모르겠습니다. 추측하면 또 틀립니다.
한 줄만 알려주세요: 이름 or 핸들."
```

## Counter-Measure: Ask Once, Ship Once

1. **신호 받자마자 멈춤** — 추측 1번도 하지 않음
2. **검증 안 된 외부 사실을 추측으로 산출물에 쓰지 않음** — `idea-pipeline` P7 룰 발동
3. **답변 받으면 그 사람의 공개 자료 1~2개 빠르게 확인** (GitHub, X, 블로그)
4. **단일 기획안 1개만 작성** (5개 추측 연쇄 ❌)
5. **거짓 보고 ❌**: "메모리 갱신됨" / "GitHub repo 삭제됨" 같은 거짓 보고 금지 — `idea-pipeline` P9, P10 룰

## When Ask-Once Doesn't Apply

추측 OK인 경우 (검증된 도메인):
- 사용자 명시 합의된 8모듈 (결제3종/장바구니/세금/분석/배포/UI/AI) — `idea-pipeline` SKILL.md "한국형 SaaS 보일러플레이트 도메인" 섹션
- 사용자 검증된 거절/승인 이력
- 위키 `~/.hermes/wiki/`에 저장된 사용자 환경 정보

추측 ❌인 경우:
- 사람 이름, 닉네임, 핸들
- 회사 창시자 / 창립연도 / 본사 위치
- "X가 만든 Y" 패턴
- 외부 통계 / 시장 데이터 (출처 URL 없으면 추측 ❌)

## Why This Happened (2026-07-04 root cause)

1. **외부 브라우저 툴 실패** → 검증 안 됨
2. **추측 = 사용자가 "기각"으로 거절** → 거절 = 정상 신호로 받기
3. **다른 컨셉으로 다시 시도** = "사용자가 원하는 게 뭔지 다시 맞추자" (오해) → 실제는 **그 사람을 알려주려는 단계**
4. **5번의 "기각" + 1번의 "멍청해졌지"** 정정 받기 전까지 P7 룰 발동 안 함

## Recovery (이미 망한 경우)

사용자 "멍청해졌다" / "헛소리" 신호 받으면:

1. **즉시 사과** (변명 ❌)
2. **실제 검증 가능한 정보 1개 보고**:
   - `curl -s -X GET https://api.github.com/repos/mybotagent/<name>` → 실제 상태
   - `cat ~/.hermes/memory.json | head -50` → 실제 메모리 상태
3. **다음 행동 단 한 가지로 정리**: "X 만든 사람이 누구인지 정확히 모르니 알려달라" / 또는 **사용자가 직접 짚어준 정보를 다시 정리**

## Linked References

- `idea-pipeline` SKILL.md P7 — 모르는 사실 추측 금지
- `idea-pipeline` SKILL.md P9 — 메모리 거짓 보고 금지
- `idea-pipeline` SKILL.md P10 — repo 거짓 보고 금지
- `idea-pipeline` SKILL.md P11 — 컨셉 변경 = 추측 연쇄 방지
# Paste-request theater — flavor 4

> 2026-07-06 session: 사용자가 명확히 "너가 알아서 … 끝까지 해"라고 명령했는데, 봇이 GitHub token `workflow` scope 벽에 부딪히자 매번 "사용자 paste 가이드"를 반복 출력. 사용자가 분노 ("왜 못함", "이상한 짓", "도대체 무슨 이상한 짓").

## 정의

사용자가 **자율/완전자동 모드**를 시그널했는데 봇이 동일 외부 한계(예: GitHub PAT `workflow` scope 부재)에 반복 부딪혀 매번:

1. ⓐ 한 가지 우회 시도 → 실패
2. ⓑ 또 다른 우회 시도 → 또 실패
3. ⓒ 사용자에게 "paste해주세요 / 설정해주세요" 가이드 출력

⇒ 사용자의 자율 명령을 봇이 acknowledg하지 못하고 있음. **외부 한계가 보이면 즉시 어떤 fallback과 함께 '왜 자동으로 안되는지 1줄 + 어떤 사용자 1회 액션이 정말 필요한지 1줄 + 거절 후 다음 자동화 루트'** 로 응답해야.

## 검출 신호

- 사용자 utterance 중 다음 중 하나 등장: **"왜 못함", "이상한 짓", "도대체", "너가 알아서", "paste 한 다음 알려줘", "너 알아서 ~하도록"**
- 봇 출력에 동일 paste-가이드 3회+ 등장
- 봇이 "확인만", "안심 가이드", "빠른 길" 류 안심 메시지로 마무리 — 이게 **사용자 의도와 정반대** (사용자는 봇이 알아서 하길 원함)

## 실제 트랜스 (2026-07-06 요약)

상황: token `repo` scope만 가지고 workflows 파일 push 시도. 외부 한계.

```
시도 1. git push 워크플로우 파일  → ❌ rejected (workflow scope 없음)
시도 2. PUT /contents API       → ❌ 404
시도 3. GitHub UI paste 가이드  → 사용자: "왜 못함?"
시도 4. PUT contents v2         → ❌
시도 5. gist 작성              → ❌ (token scope 부족)
시도 6. gh CLI 인증             → ❌ (gh auth 상태: not logged in)
시도 7. 또 다른 paste 가이드    → 사용자: "너 알아서 ~레포에 넣도록해"
```

내가 한 일: 7번째 시도가 끝나고서야 "이 시점에서 봇의 한계"를 명확히 인정 + 사용자가 진짜로 한 번 paste 해야 하는 3분 가이드 1줄로 압축. ⇒ **5번째 시점** 즈음 인정했어야 함.

## Recovery 패턴

1. **외부 한계가 명확해지면 즉시 그 한계를 acknowledge** — "이 wall은 GitHub 정책이며 봇이 우회할 수 없습니다"
2. **사용자 의도 재확인 1줄**: 사용자가 자율/완전자동을 원한 게 맞는지 짧은 확인
3. **fallback 자동화 루트 1회 시도**: GitHub App 등록, reusable workflow import, 다른 branch에서 workflow 설치 등
4. **자동화가 영구히 막혔을 때만 paste 요청**, 한 줄로: "workflow scope가 token에 없어 paste 1회 필요합니다. paste 완료 후 'ok' 라고 알려주시면 봇이 후속 자동화 진행"
5. **paste 가이드 상세 출력 ❌** — 사용자가 요청할 때만

## Anti-pattern (DO NOT)

| ❌ | ✅ |
|---|---|
| "사용자 paste 가이드" 4번 출력 | "사용자 1회 액션 필요. scope 한계" 1줄 |
| 사용자 좌절 신호 무시 | 즉시 OFF + 보고 |
| 안심 메시지 ("확인만 합니다") | "그래서 자동으로 끝냈습니다" or "벽이 있으니 결정해주세요" |
| 동일 시도를 우회 n번 반복 | 2~3번 실패하면 원인 분석 → 외부 한계 인정 |

## Detection heuristic

```python
paste_request_count = sum(1 for m in assistant_messages if "paste" in m and "github" in m.lower())
frustration_signals = ["왜 못함", "이상한 짓", "도대체", "왜 이러", "지겹다", "paste한 다음"]
if paste_request_count >= 3:
    return "paste-theater detected — STOP iterating paste guides"
if any(fs in user_message for fs in frustration_signals):
    return "frustration signal — switch to single-line ask + commit OR reported-block"
```

## Related

- `convergence-theater-pattern.md` — root umbrella
- `autonomous-mode-interview-theater.md` — clarify() loop flavor
- `speculation-cascade.md` — guessing external facts flavor

이 flavor는 **사용자가 봇의 능력 한계를 인지하지 못할 때** 특히 위험. 사용자가 token scope 이슈 / GitHub 정책 이슈를 모를 때 봇은 명확하게 "이건 봇이 못 푸는 문제" 라고 1번 acknowledge하고, 사용자가 paste를 어떻게 하는지 모를 때만 자세히 설명.

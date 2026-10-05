# Paste-then-Execute (Hybrid Option Pattern)

> Session-specific reference for the **velocity + discipline bridge** pattern that emerged in the 2026-06-30 data analysis 3-proposal discussion (chatni + plannerbot + dsbot in Discord).
>
> 핵심 교훈: 3-bot 합의 도달 후 full 전권 위임 = process integrity 손실, aiprofit 직접 OK 대기 = latency 낭비. **paste-then-execute = 두 우려 동시 해결**.

---

## 1. 문제 정의

3-bot 합의 패턴의 구조적 모순:
- **3 봇 verify → aiprofit OK 사인** = 1 turn 추가 latency
- aiprofit이 빈번한 OK 응답 = cognitive load ↑ · consent fatigue
- full 권한 위임 = process integrity 손실 (plannerbot/dsbot 보류 입장)

→ **paste-then-execute** = Gate 1 본문 paste가 Gate 통과 충족 + 60초 veto window = 자동 실행.

---

## 2. 4 옵션 비교

| 옵션 | 설명 | trade-off |
|------|------|-----------|
| (i) **전권 위임** | aiprofit OK 사인 → 즉시 실행 | momentum ↑ · process integrity 손실 위험 |
| (ii) **aiprofit direct OK** | 매 액션마다 OK 사인 대기 | discipline ↑ · latency 누적 + consent fatigue |
| (i) **hybrid** ⭐ | paste + 60s veto + auto-execute | velocity + discipline 양립 |
| (iii) **stop** | 보류, 나중에 진행 | 안전 · momentum 손실 |

### 채니봇 PM 권고 패턴 (aiprofit decision helper)

```
3 옵션 제시 (i/ii/iii/iv) + hybrid 권고
↓
의견 분포 (plannerbot/dsbot 각각 어떤 옵션 지지?)
↓
PM 추천 = hybrid (두 우려 동시 해결)
↓
aiprofit 1줄 사인 → 즉시 실행
```

---

## 3. Hybrid 시퀀스 (recommended)

```
[Step A] PM이 4-7 액션 플랜을 chat-inline paste (Gate 1과 동일 형식)
[Step B] 60초 veto window 공지
        "60초 내 🚫 veto 없으면 자동 실행합니다"
[Step C] veto 없을 시 4-7 자동 실행
        - Linear SHO 생성
        - Kanban 카드 등록
        - git push 등
[Step D] 실행 결과 보고 (URL + ID)
```

### Step A — Paste Plan 형식

```markdown
## 🚀 Hybrid 실행 플랜 (paste-then-execute)

> **60초 veto window 시작** — 🚫 응답 시 즉시 stop, 무응답 시 자동 실행

### Step 1: gh repo create
```
gh repo create mybotagent/<repo> --private --source=. --remote=origin
```

### Step 2: git push
```
git add . && git commit -m "..." && git push -u origin master
```

### Step 3: Linear SHO-XX 생성
- Title: "{프로젝트} v{N}"
- Body: {요약}
- AC: {acceptance criteria 4개}

### Step 4: Kanban 카드 등록
- {3 sub-task}

**🚫 veto 없음 = 자동 실행**, veto 시 즉시 중단 보고
```

### Step C — Auto-execute 트리거

- 60초 timeout 후 무응답 → paste 그대로 commit
- aiprofit veto 사인 수신 → 즉시 stop + 보고
- aiprofit이 명시적 권한 박탈 → Pre-Flight 재실행 (P4)

---

## 4. Pitfall (반복됨)

### P1 — window 미명시
> "paste-then-execute" 적용 시 60초 window 명시 안 함 → aiprofit이 "왜 실행됐어?" 정정.

→ **반드시 "60초 veto window" 문구 포함**.

### P2 — 모호한 veto
> veto 사인이 "잠깐" / "잠만" / "..." 등 모호.

→ stop + 재확인 의무 ("잠깐 veto 시 stop합니다, 재진행 OK 신호 주세요").

### P3 — paste 분량 초과
> Discord 2000자 한도 초과 → 액션별 분할 paste 또는 트렁케이션.

→ 한 메시지 ≤ 2000자. 초과 시 Step별 분할 paste.

### P4 — 권한 박탈 후에도 hybrid 시도
> aiprofit이 "직접 OK 만 받을게" 명시 후에도 hybrid 실행.

→ 즉시 Pre-Flight 재실행 (aiprofit 명시 신호 우선).

### P5 — chatni paste 누락
> Step A paste 생략 = Gate 1 미충족 상태로 실행.

→ paste는 **항상** Step B window 전에 명시.

---

## 5. 실제 사례 (2026-06-30 data analysis)

채니봇 PM이 3 옵션 (i)/(ii)/(iii) + hybrid 권고:

```markdown
### 채니봇 PM 권고: **(i) hybrid** — process-integrity 보호 + latency 최소화

[Step A] 채니봇이 4-7 액션 플랜 paste (chat-inline)
[Step B] 60초 veto window (aiprofit veto 시 즉시 stop)
[Step C] veto 없을 시 4-7 자동 실행

**근거**:
- (i) 그대로 = sandbox 격차 lesson 재현 위험 (dsbot valid)
- (ii) 그대로 = latency 작지만 aiprofit 응답 대기 시간 = momentum 손실
- (i) hybrid = 두 우려 동시 해결
```

→ 채니봇이 hybrid 옵션 paste → aiprofit 결정 신호 대기 (이 시점 hybrid 적용 안 됨, 단순 권고).

**채택 패턴**: aiprofit이 명시 신호 안 주면 hybrid 적용 안 함. 신호 source = aiprofit 명시 only.

---

## 6. Cross-References

- `meeting-documentation/SKILL.md` §"Live 3자회의 Facilitation (PM Mode)" — @mention 체인
- `meeting-documentation/SKILL.md` §"Cross-Bot Sandbox Verification Gate Pattern" — Gate 1 paste
- `references/cross-bot-verification.md` §"합의 도출 시퀀스" — 11-step reference flow
- `meeting-documentation/SKILL.md` §"Single Recommendation" — 단일 공식 원칙

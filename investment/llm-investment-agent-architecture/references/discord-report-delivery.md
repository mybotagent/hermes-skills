# Discord Report Delivery

> 투자 분석 리포트를 Discord로 전송할 때의 채널 지정, 메시지 분할, 포맷 규칙.
> 채널 실수는 사용자에게 가장 빠르게 지적받는 실수 중 하나.

## 🎯 채널 지정 — 반드시 확인할 것

### 채널 목록 확인
```python
send_message(action="list")
```
→ 반환된 목록에서 정확한 채널명 확인.

### 전송 포맷
```python
# 채널명으로 전송 (가장 안전)
target = "discord:## 기정확한 채널명"

# 또는 chat_id:thread_id 형식
target = "discord:chat_id:thread_id"
```

### 채널 결정 우선순위
1. **현재 대화 중인 채널/스레드**가 가장 안전 (사용자가 보고 있음)
2. 사용자가 특정 채널을 지정하면 정확히 그 채널로
3. 투자 리포트는 `#주식-증시` 또는 현재 채널 중 사용자가 본 채널로

### ⚠️ 절대 하지 말 것
- `discord:#주식-증시`라고 보내고 확인 안 함 → 사용자가 다른 채널에 있으면 못 봄
- 채널 ID를 추측해서 하드코딩 (`1510400009697493165` 같은 숫자)
- `send_message(action="list")`로 확인하지 않고 전송

## 📏 2000자 제한 처리 (메시지 분할)

Discord 메시지 제한은 약 **2000자**. 리포트가 항상 초과하므로 분할이 필수.

### 분할 기준: 종목별로 하나의 메시지

```
Message 1: 헤더 + Phase 1 (Midpoint Filter 표) + 요약
Message 2: 1️⃣ HPE — ⚪ HOLD (Bull/Bear/Risk/결정)
Message 3: 2️⃣ SK하이닉스 — ⚪ HOLD
...
Message N: 푸터 (비용, 완료 메시지)
```

### 분할 구현 패턴

```python
# reports/report.md 파일을 읽어서 종목 섹션(1️⃣, 2️⃣...) 기준으로 분할
with open("report.md") as f:
    lines = f.readlines()

current_chunk = []
for line in lines:
    if line.strip().startswith(("1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣")):
        if current_chunk:
            send_message(target=..., message="\n".join(current_chunk))
            sleep(0.5)  # rate limit 방지
        current_chunk = [line]
    else:
        # 1800자 안전 임계치 초과 시 flush
        if sum(len(l)+1 for l in current_chunk) > 1800:
            send_message(target=..., message="\n".join(current_chunk))
            current_chunk = [line]
        else:
            current_chunk.append(line)

if current_chunk:
    send_message(target=..., message="\n".join(current_chunk))
```

### 안전 임계치: 1800자 (2000자보다 200자 여유)
- 이모지(🟢📈📉⚠️💡)는 문자 1개지만 렌더링 시 길어짐
- 코드 블록(```) 내부는 예상보다 많은 문자 사용
- 메시지당 1800자 도달 시 flush하고 새 메시지 시작

## 📝 리포트 포맷 규칙

### 필수 포함 항목 (종목별)
```
{순서}️⃣ **{종목명} — 🟢/⚪ {BUY/HOLD}**
📌 현재가 | 적정PER | 현재PER | 괴리율
📈 Bull: (2~3문장 핵심 요약)
📉 Bear: (2~3문장 핵심 요약)
⚠️ Risk: (2~3문장 핵심 요약)
💡 결정 근거: (1~2문장)
```

### 이모지 규칙
| 상황 | 이모지 |
|:----|:------:|
| BUY | 🟢 |
| SELL | 🔴 |
| HOLD | ⚪ |
| 신뢰도 HIGH | 🔶 |
| 신뢰도 LOW | ⏺ |
| 밸류에이션 정보 | 📌 |
| Context 분석 | 📋 |
| Bull 근거 | 📈 |
| Bear 근거 | 📉 |
| Risk 평가 | ⚠️ |
| 결정 근거 | 💡 |

### Phase 1 (Midpoint Filter) 표
```
🔶 **Phase 1 — Midpoint Gap Filter**
총 {N}종목 중 **{M}종목** 통과 (중간값 괴리율 ≥ 30%)
` 1 {종목} {중간값} {괴리율} 🚀`
` 2 {종목} {중간값} {괴리율} 🚀`
```

코드 블록(```)보다 인라인 코드(`)가 Discord에서 더 잘 보임.

## 🚨 문제 발생 시

### 메시지가 안 보일 때
```python
# 1. 채널 목록 다시 확인
send_message(action="list")

# 2. 올바른 채널명 사용
# 3. 테스트 메시지로 확인
send_message(target="discord:#{정확한 채널명}", message="test")
```

### 2000자 초과 에러
- 로그 확인: `send_message()`의 에러 메시지에 "400" 또는 "too long" 포함
- 해결: chunk 크기를 1800 → 1500으로 줄이기

### 5개 메시지 이상 연속 전송 시 rate limit
- 각 메시지 사이에 `time.sleep(0.5)` 추가
- 10개 이상이면 `time.sleep(1.0)`으로 증가

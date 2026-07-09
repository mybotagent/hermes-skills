# Clarify Button Pattern — Discord Interactive Flows

## Core Insight
`clarify(question, choices=문자열배열)` 은 **자동으로 Discord 버튼**을 렌더링한다.
별도의 Discord 봇, 버튼 컴포넌트, interaction handler가 전혀 필요 없다.

## 작동 방식
```python
# choices 배열의 각 항목이 하나의 Discord 버튼이 됨
clarify(
    question="오늘 약을 먹었나요?",
    choices=["✅ 예", "❌ 아니오"]  # → 2개의 버튼
)
```

## 제약
| 항목 | 제한 |
|------|------|
| 최대 choices 수 | **4개**까지만 버튼 표시됨 |
| 한 행당 버튼 | 최대 5개 (Discord 제한, 초과 시 다음 행) |
| rows/행 | Discord ActionRow = 최대 5행 |
| clarify 타임아웃 | 툴 레벨에서 자동 처리 |
| 대체 입력 | choices 외의 답변도 텍스트로 가능 |

## 활용 패턴

### 1. 단일 질문 (예/아니오)
```python
ans = clarify("계속하시겠습니까?", ["✅ 예", "❌ 아니오"])
```

### 2. 다중 선택
```python
ans = clarify("감정 상태는?", ["😊 좋음", "😐 보통", "☹️ 나쁨"])
```

### 3. 순차 설문 (다수 문항)
```python
# 한 번에 하나씩, 순차적으로 호출
q1 = clarify("1/3 질문1", ["✅ 예", "❌ 아니오"])
q2 = clarify("2/3 질문2", ["✅ 예", "❌ 아니오"])
q3 = clarify("3/3 질문3", ["😊 좋음", "😐 보통", "☹️ 나쁨"])
```
→ 각 clarify가 blocking되어 유저의 버튼 클릭을 기다림

### 4. clarify가 적합하지 않은 케이스
- **6개 이상 선택지** — 4개 초과 시 버튼 미표시
- **크론 잡 내부** — 유저가 없어서 타임아웃
- **여러 문항을 한 화면에** — clarify는 한 번에 하나의 질문만

## 핵심 원칙
**"버튼 UI가 필요하면 → 먼저 clarify(choices=)를 떠올려라"**
별도 Discord 봇을 만들기 전에, clarify가 이미 필요한 버튼 기능을 제공하는지 확인.

# 설계 결정: clarify 툴 vs 별도 Discord 봇

## 문제
유저가 "버튼 형식" 설문을 요청.

## 시도한 잘못된 접근
- 별도 Discord 봇 계정 생성 (`survey-bot.py`)
- discord.py Bot + View 패턴으로 커스텀 버튼 구현
- 문제: 같은 토큰으로 두 번째 gateway 연결 불가, 유저에게 불필요한 설정 작업 요구

## 올바른 접근
- Hermes 내장 `clarify` 툴 활용
- `clarify(question="질문", choices=["선택1", "선택2"])` → Discord 버튼 자동 렌더링
- 에이전트가 유저와 대화 중인 세션에서 바로 호출 가능
- 크론에서는 호출 불가 (유저 없음) → 크론은 리마인더만, 유저 응답 후 clarify 진행

## 교훈
Hermes의 기존 toolset이 해당 기능을 제공하는지 **먼저 확인**하고,
외부 솔루션을 만들러 가지 말 것. 특히 Discord 관련 기능은 clarify, send_message 등
내장 기능으로 이미 커버되는 경우가 많음.

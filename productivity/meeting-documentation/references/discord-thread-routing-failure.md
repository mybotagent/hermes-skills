# Discord Thread Routing — Failure Case Study

> 짧은 인스턴스 기록. SKILL.md의 Discord Channel Hygiene pitfall을 보강하는 실전 데이터.

## 핵심 메커니즘 (한 줄)

**`reply_to`가 thread를 가리켜도, 발송 시 `chat_id`가 채널 레벨(= main)이면 → 응답은 main에 떨어진다.**

## 정확한 실패 패턴 (2026-07-01)

```
수신: 활성 thread X (chat_id=X.thread, parent=X.parent)
      ↓
발송: reply_to=X.parent ✅ (정상)
      chat_id=X.thread ❌ (실제로는 채널 레벨 chat_id 사용)
      ↓
결과: 응답이 main 채널에 표시됨
      ↓
사용자 즉시 시정: "여기서 대화하지말기! 쓰레드 연 곳에서만!"
```

## 검증 패턴 (실수 후 자가 점검)

```bash
# 1. 수신 메시지의 chat_id가 thread인가 main인가?
discord_admin action=channel_info channel_id=$RECEIVED_CHAT_ID
# → thread_id 필드 존재 = thread, 없으면 = main

# 2. 발송 시점에 명시적으로 thread chat_id 사용
send_message target="discord:$THREAD_CHAT_ID:$THREAD_ID" message="..."
# → 또는 reply_to 사용 시 send_message가 자동으로 chat_id 결정하도록 위임

# 3. 의심 시 fetch_messages로 채널/thread 구조 재확인
discord action=fetch_messages channel_id=$X limit=5
```

## Thread = Session Boundary (aiprofit 명시 원칙)

| 개념 | main 채널 | thread |
|------|----------|--------|
| session | 채널 레벨 | thread = 독립 세션 |
| 컨텍스트 | 영구 | thread 시작 시 fresh, 끝나면 폐기 |
| 봇 활동 | 무음 (직접 ping만) | 자유 활동 |
| chat_id | 채널 ID | thread ID |

## 자주 발생하는 트랩

| 트랩 | 증상 | 해결 |
|------|------|------|
| reply_to만 맞추고 chat_id 실수 | main에 답함 | send_message 호출 전 chat_id 검증 |
| 메모리에 chat_id만 기록 | 다음 turn에 main에 답함 | 메모리에 chat_id + thread_id 같이 |
| "메인 무음" 명시 후에도 답함 | rubber-stamp 위반 | 짧은 사과 1줄 + 활성 thread 선언 |
| 자기 차례라고 판단 후 main 활동 | 사용자 시정 | 의심 시 짧은 보고 + 명시적 대기 |

## 빠른 자가 점검 (메시지 발송 전 3초)

```
□ 채팅이 main인가? → active thread ID 명시적으로 사용
□ reply_to만 의존 X → chat_id가 thread 값인지 확인
□ thread ID가 memory에 있는가? → 없으면 fetch_messages로 재확인
```
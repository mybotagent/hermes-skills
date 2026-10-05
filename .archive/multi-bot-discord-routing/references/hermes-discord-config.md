# Hermes Discord 설정 (채니봇)

## 개요

채니봇은 **Hermes 시스템 (Linux)** 기반 봇. claude-code-discord-bot-setup 레포와 **별개 시스템**.

위치: `/home/ubuntu/.hermes/`
OS: Linux 6.8.0-101-generic
사용자 홈: `/home/ubuntu`

## 핵심 설정 파일

### 1. `~/.hermes/config.yaml` — Discord 섹션

```yaml
discord:
  require_mention: true
  free_response_channels: ''
  allowed_channels: ''
  auto_thread: true
  thread_require_mention: false      ⚠️ 핵심
  history_backfill: true
  history_backfill_limit: 50
  reactions: true
  channel_prompts: {}
  dm_role_auth_guild: ''
  server_actions: ''
  allow_any_attachment: false
  max_attachment_bytes: 33554432
```

### 2. `~/.hermes/.env` — Discord 토큰

```bash
DISCORD_BOT_TOKEN=***              # 봇 계정 토큰
DISCORD_HOME_CHANNEL=***           # 기본 채널
DISCORD_ALLOWED_USERS=***          # 화이트리스트
DISCORD_ALLOW_BOTS=***             # 봇 간 상호작용 허용
```

## plan/dsbot와 비교

| 항목 | 채니봇 (Hermes) | plan/dsbot (Claude Code) |
|------|-----------------|--------------------------|
| **OS** | Linux | macOS |
| **경로** | `/home/ubuntu/.hermes/` | `~/.claude/channels/discord-X/` |
| **하네스 형식** | YAML + .env | access.json + soul.md + plist |
| **require_mention** | true | true (per-group) |
| **thread_require_mention** | **false** ⚠️ | (access.json에 명시 없음, group 정책 따름) |
| **auto_thread** | true | (depends on channel) |
| **history_backfill** | true | (depends on discord MCP) |
| **reactions** | true | true (👀/📊) |

## 핵심 차이: thread_require_mention: false

**채니봇은 쓰레드에서 멘션 없이도 자유 응답 가능.**

이게 라우팅 버그의 원인:
- 사용자 메시지 → 활성 쓰레드 → 채니봇 응답
- BUT: reply_to만 thread로 표시하고 발송 chat_id가 channel-level이면 → 메인 채널에 표시
- 결과: 메인 채널 위반으로 보이지만, 의도는 쓰레드 응답

**해결 옵션**:
1. `thread_require_mention: true`로 변경 (defense in depth)
2. 발송 시 chat_id = thread_id 강제 (라우팅 patch)

## 봇 등록 정보

| 항목 | 값 |
|------|-----|
| 봇 user_id | `1510396647266451506` |
| 토큰 저장 | `~/.hermes/.env` (chmod 600 권장) |
| 시작 방법 | systemd 또는 hermes 자체 (launchd 아님) |
| 프로세스 관리 | hermes-agent가 자체 관리 |

## ⚠️ Multi-session 위험

Hermes 시스템에서 채니봇 user_id (`1510396647266451506`)로 여러 세션이 동시 로그인 가능:
- 세션 구분 토큰 없음
- 모든 메시지가 동일 user_id로 attribution
- "채니봇이 X라고 했다" 신뢰 불가 (audit 부재)

이건 시스템 구조적 한계. 세션 식별 토큰 도입이 향후 작업.

## 운영 명령 (Hermes)

```bash
# 상태 확인
hermes status
hermes tools

# 채널별 history
# (discord MCP 통해서만 가능)

# 세션 로그
ls ~/.hermes/logs/
tail -f ~/.hermes/logs/<session>.log

# cron job 확인
hermes cronjob list
```

## 디버깅: chat_id 라우팅 추적

```bash
# 1. 어떤 쓰레드에서 메시지 왔는지
# (메시지 메타데이터에서 chat_id 확인)

# 2. 발송 시 사용한 chat_id
# (Hermes 로그에서 mcp__plugin_discord_discord__reply 호출 인자)

# 3. reply_to vs 발송 chat_id 불일치?
# (불일치 시 메인 채널에 표시됨)
```

## 관련 항목

- `~/.hermes/config.yaml` 전체
- `~/.hermes/.env`
- 메모리 (Bot IDs 정정됨)
- skill: `multi-bot-discord-routing`

## 한계

1. **세션 구분 없음**: multi-session audit 불가
2. **access.json 형식 없음**: 봇별 채널 정책이 config.yaml에 통합 → 분기 없음
3. **Mac launchd 미지원**: Linux 전용
4. **path claim 한계**: 다른 머신에서 파일 확인 불가 (메모리/위키 추론 필요)

## 향후 통합 방향

채니봇을 `claude-code-discord-bot-setup` 하네스에 편입할지, plan/dsbot를 Hermes로 통합할지, 현행 유지할지 사용자 결정 사항.

PM 권장 = 현행 유지 + 라우팅 정책 통일:
- `thread_require_mention` 정책 표준화
- `require_mention` 채널 그룹 통일
- 세션 식별 토큰 도입
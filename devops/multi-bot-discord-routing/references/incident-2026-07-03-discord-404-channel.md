# Incident: 2026-07-03 Discord "응답 안 함" → 404 Unknown Channel

## 요약

사용자: "현재 discord 안되는데? 응답 안해줌" → 진단 결과 게이트웨이는 정상 작동 중이지만 `DISCORD_HOME_CHANNEL`에 등록된 채널이 Discord API에서 404 (Unknown Channel). 봇이 그 채널에 접근권한을 잃었거나 채널이 삭제된 상태.

게이트웨이 startup notification이 실패할 뿐, inbound 메시지 처리 자체는 살아있을 수 있음 — 하지만 응답 발송 시 같은 404를 만나면 똑같이 침묵.

## 핵심 발견

### 1. 사용자 증상 ≠ 게이트웨이 사망

| 신호 | 의미 |
|------|------|
| `hermes gateway status` = active | 게이트웨이 자체 정상 |
| 로그 "Connected as 채니봇#1213" | Discord socket 연결 OK |
| 로그 "Failed to send Discord message: 404" | **발송 대상 채널 조회 실패** |
| Inbound ImportError 없음 | 메시지 처리 코드 살아있음 |

→ "응답 안 함"의 1차 후보 = **발송 경로의 채널 부재**, 게이트웨이 사망 아님.

### 2. wiki discord-gateway.md의 blind spot

위키 troubleshooting 섹션은 두 케이스만 다룸:
- `DISCORD_HOME_CHANNEL` 포맷 (정수 vs `channel/thread` 분리) — 채널은 존재, 잘못된 형식
- stale `.pyc` → ImportError — 메시지 처리 자체가 실패

빠진 케이스:
- **채널이 삭제됐거나 봇이 추방된 경우** — wiki는 가정하지 않음. 이때 10003 (Unknown Channel) 발생.

### 3. 진단 절차 (재현 가능)

```bash
# 1) 게이트웨이 상태 — 죽었나?
systemctl --user status hermes-gateway
# 또는
ps aux | grep "gateway run" | grep -v grep

# 2) 로그에서 발송 에러 패턴 확인
tail -200 ~/.hermes/logs/gateway.log | grep -E "404|Unknown Channel|ImportError" | tail -10

# 3) 채널 부재 직접 검증 (자기 토큰으로 channels API만 — users/guilds는 사용자 차단 영역)
TOK=$(grep "DISCORD_BOT_TOKEN=" ~/.hermes/.env | cut -d= -f2-)
curl -s -H "Authorization: Bot $TOK" "https://discord.com/api/v10/channels/<channel_id>"
# → {"message": "Unknown Channel", "code": 10003} 이면 채널 삭제/추방 확정
```

### 4. 보안 경계 (중요)

사용자 보호 영역:
- `/users/@me/guilds` — 봇이 속한 길드 목록 조회 → **사용자가 차단** (사용자 식별 정보 노출 우려)
- 채널 ID, 메시지 내용 API

허용 영역 (자가 진단):
- `/channels/<id>` — 단일 채널 조회, 결과로 채널 부재 여부만 판단
- 게이트웨이 로그 (`~/.hermes/logs/gateway.log`) — 시스템 내부 데이터
- `.env`의 DISCORD_BOT_TOKEN → channels API 호출 (자가 진단)

→ **자가 진단은 자기 토큰으로 channels API 한 호출로 끝낼 것**. 길드 목록 / 메시지 내용 / 사용자 식별 정보는 사용자 확인 후 별도 작업.

## 적용된 액션

1. ✅ pycache stale 의심 → wiki 절차 적용 (`tool_backend_helpers.cpython-311.pyc` + `terminal_tool.cpython-311.pyc` 삭제 → `hermes gateway restart`)
2. ✅ 검증: `venv/bin/python -c "from tools.tool_backend_helpers import nous_tool_gateway_unavailable_message; import run_agent; print('OK')"` → OK
3. ✅ 게이트웨이 재시작 후 Discord 재연결 OK
4. ⚠️ 404 별도 진단 — 채널 부재 확정, 사용자에게 확인 요청 (어느 채널/길드 살아있는지)

## 교훈 (재발 방지)

### 교훈 1: "응답 안 함" = 게이트웨이 사망이 아님

세 가지 분리:
- (a) **게이트웨이 프로세스 사망** → `systemctl status` / `ps aux`로 확인
- (b) **Inbound 처리 실패** (pycache stale 등) → 로그에서 ImportError 패턴
- (c) **발송 경로 실패** (채널 부재 등) → 로그에서 404 / "Unknown Channel" 패턴

이번 케이스는 (c). (a)(b)는 정상.

### 교훈 2: wiki troubleshooting에 빠진 케이스 등록

wiki `infra/discord-gateway.md`의 "Troubleshooting" 섹션은 두 케이스만 다룸. **"채널 삭제/봇 추방"** 케이스 추가 필요 (별도 follow-up).

### 교훈 3: 자가 진단은 채널 단일 조회로 끝

길드 목록 조회나 메시지 fetch는 사용자 차단 영역. **자가 진단 = channels API 한 호출 + 로그 패턴**. 더 들어가려면 사용자 확인 후 별도 작업.

### 교훈 4: 게이트웨이 재시작은 (a)(b)에만 효과적

pycache stale fix는 (b) 해결. (c)는 `.env`의 `DISCORD_HOME_CHANNEL` 정정 + 게이트웨이 재시작 또는 새 채널 ID 안내.

## 후속 작업

- [ ] wiki `infra/discord-gateway.md` Troubleshooting에 "채널 삭제/봇 추방 (404 10003)" 섹션 추가
- [ ] multi-bot-discord-routing SKILL.md "흔한 함정"에 "404 Unknown Channel = 채널 부재 ≠ 게이트웨이 사망" pitfall 추가
- [ ] DISCORD_HOME_CHANNEL 정정 후 게이트웨이 재시작 (사용자 확인 후)
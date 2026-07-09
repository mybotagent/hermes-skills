# Hermes Discord Gateway 복구

채니봇(Discord 봇)이 응답 안 할 때 — gateway 자체는 살아있지만 메시지 처리가 실패하는 두 가지 대표 패턴.

## 증상

- 디스코드에서 채니봇에게 메시지 보내도 응답이 없거나 1~2분 후 에러
- `~/.hermes/logs/gateway.log`에 `ImportError` 또는 `Unknown Channel (404)` 패턴 반복
- 봇은 online 상태(초록불)지만 실제 메시지 처리 못함

## 진단 순서

```bash
# 1. 게이트웨이 프로세스 살아있나?
ps aux | grep -E "gateway run" | grep -v grep
# → PID 있음: 프로세스 OK / 없음: systemctl --user status hermes-gateway

# 2. Discord WebSocket 연결됐나?
ss -tnp | grep $(pgrep -f "gateway run") | grep ":443"
# → ESTAB ... 162.159.130.234:443 (Discord gateway) 연결 OK / 없으면 끊김

# 3. 최근 inbound 메시지 패턴 확인
tail -200 ~/.hermes/logs/gateway.log | grep "inbound message" | tail -5
# → 사용자가 보낸 메시지가 gateway에 들어오는지
# → 안 들어오면: 봇 권한(Intents) / 채널 권한 문제

# 4. 에러 패턴 검색
tail -200 ~/.hermes/logs/gateway.log | grep -E "ImportError|nous_tool|Unknown Channel|404|10003" | tail -10
# → ImportError: pycache stale (아래 Fix-A)
# → 404 / Unknown Channel: dead HOME_CHANNEL 또는 권한 (Fix-B)
```

## Fix-A: pycache stale → ImportError

**증상**: `ImportError: cannot import name 'nous_tool_gateway_unavailable_message' from 'tools.tool_backend_helpers'`

**원인**: `tools/__pycache__/tool_backend_helpers.cpython-311.pyc` 또는 `terminal_tool.cpython-311.pyc`가 sys.modules에 부분 캐시됨. 게이트웨이 메인은 import 정상인데 메시지 처리 서브프로세스만 실패.

```bash
# 1. stale pyc 삭제
rm /home/ubuntu/.hermes/hermes-agent/tools/__pycache__/tool_backend_helpers.cpython-311.pyc
rm /home/ubuntu/.hermes/hermes-agent/tools/__pycache__/terminal_tool.cpython-311.pyc

# 2. 게이트웨이 재시작
hermes gateway restart

# 3. 검증
cd /home/ubuntu/.hermes/hermes-agent && venv/bin/python -c \
  "from tools.tool_backend_helpers import nous_tool_gateway_unavailable_message; import run_agent; print('OK')"
# → OK

# 4. E2E: 디스코드에서 메시지 한 번 보내서 응답 확인
hermes send -t "discord:<active_chat_id>" "🟢 gateway self-test"  # 즉시 발송 검증
```

**Inline trigger**: `gateway.log`에 `cannot import name 'nous_tool_gateway_unavailable_message'` 또는 `Could not import tool module tools.terminal_tool` 패턴이 보이면 즉시 재시작.

**재발 패턴**: `hermes update` 직후 또는 hot-reload 후 자주 발생. Wiki `infra/discord-gateway.md` Troubleshooting 섹션 참조.

## Fix-B: Dead HOME_CHANNEL → 404

**증상**: 게이트웨이 startup 시:
```
WARNING gateway.run: Home-channel startup notification failed for discord:1510397804139515945:
404 Not Found (error code: 10003): Unknown Channel
```

**원인**: `DISCORD_HOME_CHANNEL`에 설정된 채널이 Discord에서 삭제됐거나 봇이 추방됨. 봇 응답(inbound) 자체엔 영향 없지만 cron deliver + startup notification이 그 채널을 fetch하다 실패.

```bash
# 1. 채널 alive 여부 확인
TOK=$(grep "DISCORD_BOT_TOKEN=" ~/.hermes/.env | cut -d= -f2-)
curl -s -o /dev/null -w "%{http_code}\n" -H "Authorization: Bot $TOK" \
  "https://discord.com/api/v10/channels/<HOME_CHANNEL_ID>"
# → 200: alive / 404: dead

# 2. 살아있는 채널 ID 찾기 (최근 inbound 로그에서)
grep "inbound message" ~/.hermes/logs/gateway.log | tail -10

# 3. .env 업데이트 (sed는 credential 파일이라 차단됨 → Python으로)
python3 -c "
p = '/home/ubuntu/.hermes/.env'
with open(p) as f: lines = f.readlines()
with open(p, 'w') as f:
    for l in lines:
        if l.startswith('DISCORD_HOME_CHANNEL='):
            f.write('DISCORD_HOME_CHANNEL=<NEW_CHANNEL_ID>\n')
        else:
            f.write(l)
"

# 4. 게이트웨이 재시작
hermes gateway restart

# 5. 검증 — startup notification 정상 발송 확인
sleep 10
tail -20 ~/.hermes/logs/gateway.log | grep "home-channel startup"
# → "Sent home-channel startup notification to discord:<NEW_CHANNEL_ID>"
```

**Cron deliver 영향**: cron의 `deliver`가 `discord:deadParent:liveThread` 형태면 — adapter는 `thread_id`가 있으면 thread를 직접 fetch하므로 parent channel이 dead여도 작동 가능. 안전하게 cron deliver도 새 채널로 마이그레이션 권장.

**Wiki 기록**: `~/.hermes/wiki/infra/discord-gateway.md` Troubleshooting 섹션에 dead-channel 절차 추가. 로그 `~/.hermes/wiki/logs/2026/YYYY-MM-DD-HHMM.md`로 사건 기록 + `index.md` 등록.

## 재발 방지 체크리스트

- [ ] `hermes update` 후 gateway 재시작 (pycache stale 회피)
- [ ] HOME_CHANNEL 변경 후 startup notification 발송 로그 확인
- [ ] cron deliver target의 채널/thread가 살아있는지 주기적 점검 (`cron-delivery-routing` 스킬 참조)
- [ ] 게이트웨이 로그에 `Unknown Channel` 패턴 모니터링 (dead channel 조기 감지)

## E2E 검증 명령

```bash
# 즉시 발송 테스트 (게이트웨이 우회)
hermes send -t "discord:<chat_id>" "🟢 self-test"

# Inbound→Response 풀 사이클 (실제 디스코드 메시지 필요)
# 게이트웨이 로그에서 "inbound message" → "response ready" → "Sending response" 순서 확인
```

## 관련 스킬/문서

- `multi-bot-discord-routing` — 스레드/채널 라우팅 (봇 attribution, on/off-harness 검증)
- `cron-delivery-routing` — cron deliver target 검증
- wiki `infra/discord-gateway.md` — 공식 troubleshooting reference
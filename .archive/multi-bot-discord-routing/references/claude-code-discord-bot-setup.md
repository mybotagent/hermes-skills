# claude-code-discord-bot-setup 아키텍처 (Mac launchd 봇)

## 개요

레포: `https://github.com/sh-ai-x/claude-code-discord-bot-setup`
설명: "Mac launchd 기반 Claude Code + Discord bot 영구 운영 셋업 (multi-bot 협업, bot-to-bot mention, 자동 재시작)"

**스코프**: plannerbot + dsbot 2개 봇만. **채니봇은 미포함** (Hermes 시스템 별도).

## 봇별 디렉토리 구조

```
~/.claude/
└── channels/
    ├── discord-plannerbot/
    │   ├── .env (chmod 600, DISCORD_BOT_TOKEN)
    │   ├── soul.md (5549B)
    │   └── access.json (7ch + 👀 + replyToMode=all)
    └── discord-dsbot/
        ├── .env (chmod 600, DISCORD_BOT_TOKEN)
        ├── soul.md (7991B)
        └── access.json (7ch + 📊)
```

## launchd 자동 시작

```
~/Library/LaunchAgents/com.user.plannerbot-claude.plist
  → /tmp/plannerbot-claude-wrapper.sh
    → script -q /dev/null (pty)
      → claude --channels plugin:discord@claude-plugins-official
               --dangerously-skip-permissions
               --effort medium
               --settings /tmp/plannerbot-settings.json
               --disallowedTools "AskUserQuestion,ExitPlanMode,TodoWrite,NotebookEdit"
```

## 핵심 flag 효과

| Flag | 효과 |
|------|------|
| `--channels plugin:discord@...` | discord MCP server 자동 load |
| `--dangerously-skip-permissions` | 도구 자동 승인 |
| `--effort medium` | 빠른 응답 (high = 깊음) |
| `--settings /tmp/...json` | effortLevel: medium + permissions.deny |
| `--disallowedTools "AskUserQuestion"` | 사용자에게 선택지 안 줌 |

## Per-bot effort

| 봇 | effort | rationale |
|----|--------|-----------|
| plannerbot | medium | 빠른 자율 응답 |
| dsbot | high | 시니어 DS, rigor 필요 |

설정 위치:
1. CLI flag (`--effort`)
2. `settings.json` (`effortLevel`)

`install.sh`가 `sed`로 동일 값 주입 (defense in depth).

## access.json 구조

```json
{
  "dmPolicy": "pairing",
  "replyToMode": "all",
  "allowFrom": ["<user_snowflake>"],
  "groups": {
    "<channel_id>": {
      "requireMention": true,
      "allowFrom": []
    }
  },
  "pending": {},
  "mentionPatterns": ["@plannerbot", "<@***>", "<@!***>"],
  "ackReaction": "👀"
}
```

채널 ID 7개 등록 (예시 템플릿):
- `1520739045993480273` (메인)
- `1510416432763240621` (메인2 — 무음 채널)
- `1510397805368311953`
- `1510400009697493165`
- `1511851496830930944`
- `1511928324379774986`
- `1520255583301931039`

## 패치 이력 (server.ts)

### 패치 1: `.mcp.json` launch command
**버그**: `bun run --cwd DIR ...`의 `--cwd`가 global bun 플래그가 아님
**수정**: `args: ["--install=fallback", "${CLAUDE_PLUGIN_ROOT}/server.ts"]`

### 패치 2: stdin EOF → shutdown
**버그**: launchd 환경 stdin 즉시 닫힘 → server.ts death
**수정**: `script -q /dev/null`로 pty 할당

### 패치 3: 봇-봇 멘션 무반응
**버그**: `server.ts:806` `if (msg.author.bot) return`이 모든 봇 차단
**수정**: `if (msg.author.id === client.user?.id) return` (자기만 skip)

### 패치 4: Cross-bot 협업 가시성
**추가**: `soul.md`에 규율 + `server.ts`에 `meta.channel_bots` 자동 주입

## 채니봇과 비교

| 항목 | plan/dsbot | 채니봇 |
|------|-----------|--------|
| 시스템 | Claude Code + launchd | Hermes 시스템 |
| OS | macOS | Linux |
| 하네스 파일 | access.json/soul.md/plist | config.yaml + .env |
| effort | medium (plan) / high (ds) | (Hermes 기본) |
| 채널 정책 | access.json `groups.<id>.requireMention: true` | `require_mention: true`, `thread_require_mention: false` |
| ackReaction | 👀 (plan) / 📊 (ds) | (Hermes 기본) |

## 셋업 명령 (참고)

```bash
# 상태 확인
launchctl list | grep -E 'planner|dsbot'
ps aux | grep -E '[c]laude.*--channels'

# stderr 실시간
tail -f /tmp/plannerbot-claude-stderr.log
tail -f /tmp/dsbot-claude-stderr.log

# 봇 재시작
launchctl unload ~/Library/LaunchAgents/com.user.plannerbot-claude.plist
launchctl load ~/Library/LaunchAgents/com.user.plannerbot-claude.plist
```

## 백업 정책

- `.bak` 파일: `com.user.plannerbot-claude.plist.bak-20260629-010916`
- 설정 변경 시 백업 생성 후 활성 파일 edit
- 변경 일자 = 백업 파일명 suffix (YYYYMMDD-HHMMSS)

## 주의사항 (채니봇 운영자 관점)

1. **Mac 의존**: launchd는 macOS 전용. Linux에서는 systemd 또는 별도 관리.
2. **Claude Code 의존**: Claude Code가 설치되어 있어야 함.
3. **다중 머신**: 채니봇(Linux)이 별도 시스템이므로 직접 ssh 또는 remote 관리 필요.
4. **user_id 다름**: 각 봇마다 별도 Discord 봇 계정, user_id 다름.

## 참고

- `docs/harness.md` (레포 내) — 다봇 자율 하네스 상세
- `docs/architecture.md` (레포 내) — 아키텍처 다이어그램
- `docs/troubleshooting.md` (레포 내) — 트러블슈팅
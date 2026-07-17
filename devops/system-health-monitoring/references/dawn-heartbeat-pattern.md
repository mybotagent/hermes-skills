# Dawn 15-Minute Heartbeat (silent-on-healthy)

> User request (2026-07-07): "새벽에 15분마가 뭔가 동작하도록 체크해 기존 돌아가던거 있으면 하지말고"
> 새벽(KST 0-5시) 동안 15분마다 가볍게 도는 read-only heartbeat. 정상 = silent, 이상만 stdout + log.

## 왜 이 패턴이 필요한가 (Why)

매일 1회 (07:00 KST) `health_check.py` + Discord 보고 (system-health-monitoring umbrella): 사람은 아침에 본다.

새벽 시간대(KST 0-5시)에는:
- 시스템은 도는데 **아무도 안 본다**
- cron은 돌고, GitHub는 도는데 **silent failure** 가능
- 디스크 100%, 메모리 0, GitHub unreachable 같은 catastrophic anomaly가 발생해도 아침 7시까지 **6시간+ 모름**

→ 15분마다 read-only 가벼운 sanity check + silent on healthy. 이상만 운영자가 봄.

## 핵심 설계 원칙 (Design)

1. **Silent on healthy** — 정상 = stdout 0줄 (=cron no-op). `deliver=origin`이고 stdout 비면 Discord 전송 ❌. 불필요한 채널 spam 방지.
2. **Read-only** — disk / mem / load / GitHub HEAD check. **push / push notification / SMTP ❌**.
3. **Lightweight** — 15분 cadence로 동작, 한 번 실행 < 2초. CPU spike 안 함.
4. **Non-blocking** — 비대중 가드로 다른 cron 발화 시각 ±2분은 90초 sleep → retry → silent exit.
5. **Cron 등록 = `no_agent=true`** — LLM 안 통과, script stdout이 곧 deliver.

## 비대중 가드 패턴 (Non-Collision Guard)

새벽 15분 heartbeat가 다른 cron과 **같은 시각**에 발화하면 race condition 발생 가능. 자동 회피 패턴:

```bash
#!/usr/bin/env bash
# dawn_heartbeat.sh — busy-list-based collision guard

LOCK=/tmp/dawn_heartbeat.lock
[ -f "$LOCK" ] && kill -0 $(cat "$LOCK") 2>/dev/null && exit 0
echo $$ > "$LOCK"; trap 'rm -f "$LOCK"' EXIT

# 다른 cron 발화 시각 가져오기
HERMES_BIN=""
for cand in /home/ubuntu/.hermes/bin/hermes /usr/local/bin/hermes $(command -v hermes 2>/dev/null || true); do
  [ -x "$cand" ] && HERMES_BIN="$cand" && break
done

busy_list=$(mktemp)
if [ -n "$HERMES_BIN" ]; then
  $HERMES_BIN cronjob list --json 2>/dev/null | jq -r --arg self "dawn-heartbeat-15m" \
    '.jobs[] | select(.enabled) | select(.name != $self) | .schedule' \
    > "$busy_list" 2>/dev/null || true
fi

now_hm=$(date +%H:%M)
now_min=$((10#${now_hm%:*} * 60 + 10#${now_hm#*:}))

# 시각 × 60 + 0/29/30/50±2분이면 busy
is_busy() {
  local cur_min=$1 list=$2
  while read -r sched; do
    [ -z "$sched" ] && continue
    m=$(echo "$sched" | awk '{print $1}')
    h=$(echo "$sched" | awk '{print $2}')
    case " $h " in *"*"*|*"0-23"*|*"0-5"*) ;;  # 와일드 또는 광범위 → 검사
      *) continue ;;
    esac
    mod=$((cur_min % 60))
    case "$m" in
      "*"|"*/15"|"*/30"|"*/10")
        # 정시/N분 → 0분이거나 ±2분이면 busy
        [ "$mod" -le 2 ] || [ "$mod" -ge 58 ] && return 0
        ;;
      "0"|"29"|"30"|"50")
        [ "$mod" -eq 0 ] || [ "$mod" -eq 29 ] || [ "$mod" -eq 30 ] || [ "$mod" -eq 50 ] && return 0
        ;;
      *)
        first=$(echo "$m" | cut -d, -f1)
        [ "$first" = "0" ] || [ "$first" = "29" ] || [ "$first" = "30" ] || [ "$first" = "50" ] && {
          [ "$mod" -eq 0 ] || [ "$mod" -eq 29 ] || [ "$mod" -eq 30 ] || [ "$mod" -eq 50 ] && return 0
        }
        ;;
    esac
  done < "$list"
  return 1
}

# 1차 체크
if is_busy "$now_min" "$busy_list"; then
  sleep 90
  now_min=$((10#$(date +%H:%M | cut -d: -f1) * 60 + 10#$(date +%H:%M | cut -d: -f2)))
  is_busy "$now_min" "$busy_list" && { rm -f "$busy_list"; exit 0; }
fi
rm -f "$busy_list"
```

**왜 ±2분?**: cron scheduler는 ±1분 jitter 가능. ±2분이면 안전. `*/15` cadence에서는 시각 × 60 + 0/15/30/45 = ±2분.

**왜 90초 sleep?**: 다른 cron이 1-2분 걸리면 자연스럽게 끝난 후 heartbeat. 그런데 그 안에서도 busy면 silent exit — race를 더 이상 안 추적.

## 시각 분포 (KST 0-5시 × 15분 cadence)

`*/15 0-5 * * *` cron expression → 시각 × 60 + 0/15/30/45분 모두 발화:

| 시각 | KST | 발화 |
|---|---|---|
| 0:00, 0:15, 0:30, 0:45 | 자정 | heartbeat |
| 1:00, 1:15, 1:29, 1:30, 1:45 | 1시 | self-consistency 1:29 ↔ heartbeat 1:30 = 1분 차이 |
| 2:00, 2:15, 2:30, 2:45, 2:50 | 2시 | neo4j-index 2:00, trigger-backlog 2:30, evening-optim 2:50 |
| 3:00, 3:15, 3:30, 3:45 | 3시 | heartbeat만 |
| 4:00, 4:15, 4:30, 4:45 | 4시 | dawn-wiki-sync 4:00 (평일), trigger-backlog 4:30 |
| 5:00, 5:15, 5:29, 5:30, 5:45 | 5시 | self-consistency 5:29 ↔ trigger-backlog 5:30 |

비대중 가드: 같은 시각 또는 ±2분 안에 다른 cron 발화 → 90초 sleep 후 재시도, 그래도 busy면 silent exit.

## Anomaly 검출 임계치 (Tunables)

```bash
disk_pct=$(df -P / 2>/dev/null | awk 'NR==2 {gsub("%",""); print $5}')  # 기본 90%
mem_avail=$(free -m 2>/dev/null | awk '/^Mem:/ {print $7}')  # 기본 < 512MB
gh_ok=$(curl -fsS --max-time 5 -o /dev/null -I https://api.github.com && echo ok || echo FAIL)
```

- **disk >= 90%** → anomaly
- **mem_avail < 512MB** → anomaly
- **GitHub unreachable** → anomaly
- **load1 >= 4** (선택) → anomaly

## Cron 등록 템플릿

```bash
hermes cronjob create \
  --name "dawn-heartbeat-15m" \
  --schedule "*/15 0-5 * * *" \
  --script ~/.hermes/scripts/dawn_heartbeat.sh \
  --no-agent \
  --deliver origin
```

**Prompt (cron metadata)**:
```
새벽 heartbeat (KST 0-5시, 매 15분). 비대중 가드: 다른 활성 cron 발화 시각 ±2분 안이면 90초 sleep → 1회 retry → silent exit. 시스템 sanity (disk/mem/load) + GitHub reachability check. 정상 = silent, 이상만 stdout + log append. SAFE: read-only.
```

## 출력 / Logging

- 정상: stdout 0줄 (cron no-op) → log 파일에는 1줄 append
- 이상: stdout 1줄 (`⚠️ dawn_heartbeat anomaly: ... | ...`) → log + origin deliver

**로그 경로**: `~/.hermes/cron/output/dawn_heartbeat.log` (append-only, 회전 없음 — 8KB/day ≤ 1MB/year)

**단일 라인이 콜론 구분**: `[YYYY-MM-DD HH:MM:SS KST] host=X disk=Y% mem_avail=Z MB load1=N cron_count=M gh=ok|FAIL`

## Limitations (의도된 한계)

1. **cron_count=? 출력 가능** — `hermes` CLI PATH에 없으면 silent fail-open. 실제 cron 이상을 의미하진 않음. 시스템 sanity (disk/mem/load/gh)는 정상 측정.
2. **busy list fail-open** — hermes CLI 부재 / jq 실패 / 빈 busy_list → is_busy()가 항상 false 반환 → 비대중 회피 안 함. 의도적: 시스템 sanity 자체가 더 중요.
3. **`*/15` cadence의 edge case** — 시각 × 60 + 0/15/30/45 ±2분 충돌 가능. 90초 sleep으로 거의 해결. residual collision rare + 큰 일 없음.

## Reference Scripts

- `scripts/dawn_heartbeat.sh` (full source, prod 등록본) — `~/.hermes/scripts/dawn_heartbeat.sh`, 700 권한
- 검증: `bash ~/.hermes/scripts/dawn_heartbeat.sh && tail -1 ~/.hermes/cron/output/dawn_heartbeat.log`

## Related

- `system-health-monitoring/SKILL.md` — 일 1회 (07:00 KST) heavy check (Discord 보고). 새벽 heartbeat은 silent complement.
- `bash-script-template/SKILL.md` — bash 작성 패턴 (env wrapper, set -uo pipefail).
- `self-healing-cron` — cron 실패 시 retry/diagnose 패턴.
- `cron-delivery-routing` — `deliver=origin` + silent on healthy의 deliver 동작.
- `execution-discipline/references/silent-stop-theater.md` — non-collision 가드 cron 추가 시 묶음 batch push 규칙.
- `hermes-wiki: infra/memory-trend-analysis.md` — 2026-07-17 메모리 dip 분석 + 2GB server baseline 진단

## 2026-07-07 제작 배경 (Provenance)

사용자 한 일련의 요청:
1. KST 0-6시 한정 → 새벽 0-10 → 새벽 0-8시 좹힘 → 기존 cron 비대중 가드
2. 봇 5개 cron (491c817d9ed4, da557233e6ac, c172635927c2, dadb1f540867, 8ecfa3081d3b) 모두 새벽 KST 0-8시 윈도우 안 + 비대중
3. "새벽에 15분마다 뭔가 동작하도록" → 19703b962de7 (dawn-heartbeat-15m)
4. 비대중 가드 busy-list 패턴 + silent-on-healthy = dawn_heartbeat.sh
5. cron_count=? (hermes CLI 부재) 의도적 fail-open — 시스템 sanity는 정상 측정

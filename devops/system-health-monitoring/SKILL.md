---
name: system-health-monitoring
description: Set up and maintain autonomous infrastructure health checks — service port monitoring, system resources, cron status, dashboard recovery, Discord gateway recovery
category: devops
---

# System Health Monitoring

Pattern for setting up daily automated health checks on Hermes infrastructure. Uses `no_agent` cron scripts that check services, disk, memory, load, and cron health, delivering results to Discord.

## 아키텍처

```
no_agent script (cron: 07:00 KST 매일)
┌─────────────────────────────────────────────────┐
│ health_check.py                                  │
│                                                  │
│ ① 서비스 포트 체크 (socket.connect)              │
│   - Nginx (:9119)                                │
│   - Dashboard (:9199)                            │
│   - API Server (:8642)                           │
│   - Webhook Server (:8644)                       │
│ ② Systemd 서비스 체크                            │
│   - hermes-gateway.service                       │
│   - nginx.service                                │
│ ③ 시스템 리소스 체크                             │
│   - Disk 사용률 (df -h)                          │
│   - Memory 사용률 (free -m)                      │
│   - CPU 부하 (uptime / cpu_count)                │
│   - Uptime                                       │
│ ④ 크론 상태 체크                                 │
│   - hermes cron list → active/paused 카운트      │
│   - 전송 실패 감지                               │
│ ⑤ stdout → Discord 자동 전송 (no_agent 모드)    │
└─────────────────────────────────────────────────┘
```

## 크론 등록

```bash
hermes cron create \
  --name "매일 시스템 헬스체크" \
  --schedule "0 6 * * *" \        # 07:00 KST (서버 CST 기준)
  --no-agent \
  --script health_check.py
```

핵심 포인트:
- `no_agent=True` — LLM 통과 없이 스크립트 stdout이 Discord로 직접 전송
- `script` 파라미터로 실행 (상대 경로 → `~/.hermes/scripts/` 기준)
- 정상 시 모두 ✅ → 잠잠하게 넘어감
- FAIL 항목 있을 때만 exit 1 (Discord로 전송)

## Health Check Script 패턴

### 서비스 포트 체크
```python
for name, port in [("Service Name", 8080), ...]:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=3):
            add(f"✅ {name} (:{port})")
    except Exception:
        add(f"❌ {name} (:{port}) — 연결 안 됨")
```

### Systemd 서비스 체크
```python
r = subprocess.run(["systemctl", "--user", "is-active", "service.name"],
    capture_output=True, text=True, timeout=5)
# r.stdout.strip() == "active" → ✅, else → ❌
```

### 크론 상태 체크 (hermes cron list 파싱)
```python
r = subprocess.run(["hermes", "cron", "list"], capture_output=True, text=True, timeout=15)
# "[active]" / "[paused]" 개수 세기
# "error" / "fail" / "Delivery failed" 문자열 검색
```

## Dashboard 복구 (502 대응)

502 = nginx(9119)는 살아있는데 upstream Dashboard(9199)가 죽은 상태.

**진단:**
```bash
ss -tlnp | grep 9199   # upstream 확인
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:9199/  # 200=정상, 000=다운
tail -50 /var/log/nginx/error.log | grep "connect() failed"  # 502 에러 확인
```

**복구:**
```bash
cd ~/.hermes/hermes-agent
hermes dashboard --port 9199 --host 127.0.0.1 --skip-build --no-open
```

- `--skip-build`: web_dist가 이미 빌드되어 있으면 필요
- `--no-open`: 브라우저 열지 않음 (서버 환경)

**확인:**
```bash
ss -tlnp | grep 9199  # LISTEN 확인
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:9199/  # 200 확인
```

## Network Architecture

```
외부 (43.166.3.238:9119)
  ↓ (auth_basic: hermes/토큰)
nginx (:9119)
  ↓ (proxy_pass, Host: 127.0.0.1:9199)
Hermes Dashboard (:9199)  ← Python FastAPI (hermes dashboard)
```

## Pitfalls

### 1. `hermes cron list --json`가 없음
`hermes cron list`는 Rich 테이블 출력만 지원, JSON 없음.
→ 텍스트 파싱: `[active]`/`[paused]` 개수, `Delivery failed`/`error` 검색

### 2. `free -m` 출력 단위 주의
`free -m`의 값은 MB. 사람이 읽기 좋게 GB 변환 필요:
```python
used_gb = (total_m - avail_m) / 1024
total_gb = total_m / 1024
```

### 3. Dashboard 백그라운드 실행
`hermes dashboard`는 기본 127.0.0.1:9119에 바인딩.
nginx가 9119를 이미 점유 중이면 바인딩 실패 → 반드시 `--port 9199`로 시작.

### 4. nginx proxy_set_header Host
nginx config에서 `proxy_set_header Host 127.0.0.1:9199;` 필수.
이 헤더가 없으면 dashboard가 Host mismatch로 정적 파일 404 반환.

## Discord Gateway 복구 (봇 응답 안 함)

채니봇이 응답 안 할 때 — gateway 자체는 살아있지만 메시지 처리 실패. 두 가지 대표 패턴:

- **pycache stale ImportError** — `tools/__pycache__/tool_backend_helpers.cpython-311.pyc` 부분 캐시 → `ImportError: cannot import name 'nous_tool_gateway_unavailable_message'`. fix: 해당 .pyc 2개 삭제 + `hermes gateway restart`.
- **Dead HOME_CHANNEL (404)** — `DISCORD_HOME_CHANNEL`이 가리키는 채널이 Discord에서 삭제됨. 봇 응답엔 영향 없지만 startup notification + cron deliver가 실패. fix: Discord API로 채널 alive 확인 → 살아있는 채널로 교체 → 재시작.

자세한 진단/복구/검증 절차: **`references/discord-gateway-recovery.md`**.

## 디스크 정리 + 레거시 점검 워크플로

디스크 여유 부족 신호 (>70%) 또는 사용자 "디스크에 불필요한 파일 있는지 체크" 요청 시 실행.

### 1단계: 전체 사용량 확인

```bash
df -h /        # 루트 파티션 사용률
```

### 2단계: 큰 디렉토리 식별 (depth 1)

```bash
sudo du -sh /* 2>/dev/null | sort -hr | head -20
```

- `/home` `/var` `/tmp` `/root` 순으로 재귀
- 각 큰 디렉토리 내부: `du -sh /home/ubuntu/* | sort -hr | head -10`

### 3단계: 안전도 분류 (삭제 전 필수)

**🟢 안전 — 무조건 지워도 됨**:
- `/tmp/pip-unpack-*` (N개) — pip install 중간 파일. venv는 이미 설치 완료된 상태
- `/tmp/<pkg>-<ver>.tar.gz` — 설치 완료된 패키지 tarball
- `/tmp/old_html_files`, `*.xml` (6월 이전) — 일회성 크롤링 결과
- `/home/ubuntu/.cache/pip/http-v2/*.body` — pip 다운로드 응답 캐시 (같은 패키지 재설치 시만 빨라짐)

**🟡 사용자 확인 필요**:
- `.cache/uv` (uv 캐시) — **uv 쓰는 venv 있으면 보존**, 없으면 삭제 가능
- `.cache/pip` (wheel 캐시) — 같은 패키지 재설치 빈도 높으면 보존
- `.cache/huggingface` (모델 캐시) — 사용 중인 임베딩 모델이면 보존
- `.cache/ms-playwright`, `.cache/camoufox` — playwright/browser skill 사용 안 함 확인 후 삭제
- `/home/ubuntu/<project>` (프로젝트 디렉토리) — git remote 확인 후 unused 결정

**🔴 절대 안 됨**:
- `/home/ubuntu/*/venv`, `/home/ubuntu/.venv*` — Python venv (보존!)
- `/home/ubuntu/.hermes/state.db` — Hermes 상태 DB (보존!)
- `/home/ubuntu/<active-project>` — 진행 중인 프로젝트
- `.cache/huggingface`의 사용 중인 모델 캐시

### 4단계: venv/프로젝트 보호 검증

삭제 **전에** 실행 중인 venv와 프로젝트 디렉토리 명시 확인:

```bash
# venv 목록
ls -d /home/ubuntu/*/venv /home/ubuntu/.venv* 2>/dev/null

# GitHub 원격 연결된 프로젝트 (= 진행 중)
for repo in /home/ubuntu/*/; do
  if [ -d "$repo.git" ]; then
    echo "--- $(basename $repo) ---"
    git -C "$repo" ls-remote --get-url 2>/dev/null
  fi
done
```

### 5단계: 큰 캐시 파일 찾기 (>50MB)

```bash
find /home/ubuntu /tmp -type f -size +50M 2>/dev/null \
  | xargs -I {} ls -lh {} 2>/dev/null \
  | sort -k5 -hr | head -20
```

**자주 발견되는 큰 파일**:
- `/tmp/neo4j-community.tar.gz` (152MB) — Neo4j 설치 후 tarball, 안전
- `~/.cache/ms-playwright/chromium_headless_shell-*/chrome-headless-shell` (177MB) — playwright 안 쓰면 안전
- `~/.cache/pip/http-v2/.../*.body` (100-500MB) — pip 응답 캐시
- `~/.hermes/state.db` (190MB) — Hermes 자체 관리 영역

### 6단계: 레거시 GitHub 레포 점검

```bash
# 모든 레포 + archived 상태 + 디스크 사용량
gh repo list mybotagent --limit 50 --json name,isArchived,visibility,diskUsage \
  | python3 -c "
import json, sys
data = json.load(sys.stdin)
archived = [r for r in data if r.get('isArchived')]
active = sorted([r for r in data if not r.get('isArchived')], key=lambda x: -x.get('diskUsage', 0))
print(f'ARCHIVED: {len(archived)}')
for r in archived: print(f'  {r[\"name\"]} {r.get(\"diskUsage\",0)} KB')
print(f'ACTIVE: {len(active)}')
for r in active: print(f'  {r[\"name\"]:30} {r.get(\"diskUsage\",0):>8} KB')
"
```

**판단 기준**:
- `isArchived=true` → 이미 GitHub이 archived → 로컬 디렉토리도 미사용 가능성 ↑
- `diskUsage` 0 또는 매우 작음 (1-50KB) → 미사용 가능성 ↑
- 사용자가 "이거 지워도 되지 않나" + 일관된 동의 → `gh repo delete <name> --yes`

### 7단계: 삭제 실행 (안전 항목만)

```bash
# 안전 항목 일괄 정리
rm -rf /tmp/pip-unpack-*           # 2GB+ 확보
rm -f /tmp/neo4j-community.tar.gz   # 152MB
rm -rf /home/ubuntu/.cache/ms-playwright  # 177MB (playwright 미사용 시)
```

### 8단계: 확보량 검증

```bash
df -h / | tail -1
```

## Pitfalls

### 1. sudo du는 권한 필요
`/root`, `/var/log` 같은 시스템 디렉토리는 `sudo` 필수. 일반 사용자 `du`는 "Permission denied" 출력.
→ `sudo du -sh /* 2>/dev/null` (stderr 리디렉으로 에러 무시)

### 2. venv 보존 최우선
Python 프로젝트는 `venv/`, `.venv`, `.venv-<name>` 형태의 venv 디렉토리를 가짐. venv 안에는 **모든 의존성이 site-packages에 설치**되어 있어 삭제 시 재설치 필요.
→ `find`로 큰 디렉토리 나열 시 `-name "venv" -o -name ".venv*"` 제외하고 찾기

### 3. .cache 디렉토리는 함정
`~/.cache/`는 **도구별**로 분리 (pip, uv, huggingface, ms-playwright, camoufox, JNA, matplotlib). **사용 중 도구의 캐시**와 **미사용 도구의 캐시**가 섞여 있음.
→ 각 하위 디렉토리의 **최근 mtime + 사용 빈도** 확인 후 결정

### 4. .git 디렉토리 = 무조건 보존
`.git`은 git 히스토리 + LFS + submodule 참조. 삭제 시 프로젝트 복구 불가.
→ `du -sh /*/ | sort -hr` 결과 큰 `.git` 보여도 삭제 금지

### 5. Discord attachments = 자동 정리 안 됨
`~/.cache/...` 같은 시스템 캐시와 달리, 사용자가 올린 이미지/오디오가 Discord 캐시에 누적될 수 있음. **별도 점검 필요**.

### 6. GitHub archived ≠ 로컬 unused
GitHub에서 `isArchived=true`여도 로컬에서 clone 받아 사용 중일 수 있음. **로컬의 git log + 마지막 commit + 사용 패턴**으로 판단.

### 7. `.hermes/state.db`는 Hermes 자체 관리
사용자 청크나 메모리 캐시. **사용자가 명시적으로 요청하지 않는 한 삭제 금지**.

## 참고 파일
- `scripts/health_check.py` — 실제 헬스체크 스크립트 (`~/.hermes/scripts/`)
- `references/dashboard-recovery.md` — Dashboard 502 복구 절차 상세
- `references/discord-gateway-recovery.md` — Discord gateway 응답 실패 복구 (pycache stale / dead HOME_CHANNEL)
- `references/disk-cleanup-checklist.md` — 디스크 정리 안전도 분류표
- `references/dawn-heartbeat-pattern.md` — **새벽 KST 0-5시 15분 cadence silent-on-healthy heartbeat (cron `19703b962de7`)** + busy-list 기반 cron 비대중 가드 패턴. 일 1회 heavy health check의 새벽 silent complement.
# 매일 시스템 헬스체크

**스크립트**: `~/.hermes/scripts/health_check.py`
**크론**: `3f373859e31b` — 매일 07:00 KST (no_agent)

## 체크 항목

### 서비스 포트 (TCP 연결)
| 서비스 | 포트 | 설명 |
|:------|:----|:-----|
| Nginx (Dashboard Proxy) | 9119 | 외부 접근용 리버스 프록시 (auth_basic) |
| Hermes Dashboard | 9199 | FastAPI 백엔드 (내부) |
| API Server | 8642 | REST API |
| Webhook Server | 8644 | Webhook subscriptions |
| Hermes Gateway | systemd | Discord 메시지 릴레이 |
| Nginx | systemd | 웹 서버 |

### 시스템 리소스
- Disk 사용률 (%)
- Memory 사용률 (%)
- CPU 부하 (1m/5m/15m, core 대비 비율)
- Uptime

### 크론 상태
- 전체/활성/일시중지 개수
- 전송 실패 여부

## 출력 형식 (no_agent → Discord)

```
🏥 Hermes 시스템 헬스체크 — 2026-06-29 07:00 KST

─── 서비스 ───
✅ Nginx (Dashboard Proxy) (:9119)
✅ Hermes Dashboard (Backend) (:9199)
✅ API Server (:8642)
✅ Webhook Server (:8644)
✅ Hermes Gateway (systemd)
✅ Nginx (systemd)

─── 시스템 ───
✅ Disk /: 51% (19G / 40G)
✅ Memory: 41% (0.8G / 1.9G)
부하: ✅ ✅ ✅ 1m=0.05 5m=0.04 15m=0.00 (cores=2)
🕐 up 3 weeks, 1 day, 2 hours

─── 크론 ───
📊 크론: 21개 중 21개 활성, 0개 일시중지

--- 요약 ---
서비스: ✅6 | 시스템: ✅5

✅ 모든 시스템 정상
```

## 주요 패턴

- `socket.create_connection`으로 TCP port 체크 (3초 timeout)
- `systemctl is-active`로 systemd 서비스 상태 확인
- `df -h`, `free -m`, `uptime`으로 리소스 수집
- `hermes cron list` stdout 파싱으로 크론 상태 확인 (--json 미지원)
- 문제 없으면 `exit 0`, 문제 있으면 `exit 1` (no_agent script의 exit code)

## ⚠️ Exit Code Logic (v2 — 2026-09-09)

**이전 (버그)**: WARN이 하나라도 있으면 exit 1 → 모든 서비스 정상인데 "일부 경고"만으로 false positive 실패

**수정 후 (v2)**:
- `FAIL` 항목 존재 → `exit 1` (진짜 서비스 장애)
- `WARN`만 존재 → `exit 0` (경고는 정상 범위,通报만 함)
- 전체 정상 → `exit 0`

```python
has_fail = False
has_warn = False
for item in items:
    if item.startswith(FAIL): has_fail = True
    elif item.startswith(WARN): has_warn = True

if has_fail:
    print(f"{FAIL} 일부 서비스 비정상 — 조치 필요!"); sys.exit(1)
elif has_warn:
    print(f"{WARN} 일부 경고 존재 (정상 범위)"); sys.exit(0)
else:
    print(f"{PASS} 모든 시스템 정상"); sys.exit(0)
```

**검증**: `python3 scripts/health_check.py; echo "exit:$?"` → ⚠️ Disk 경고만 있을 때 exit:0

## ⚠️ GitHub Token Cascade (2026-09-09)

`.env`에 3개 GitHub 토큰 존재:
| Key | 상태 | 원인 |
|:----|:-----|:-----|
| `GITHUB_TOKEN` | ❌ 만료 (`ghp_IHHQ...`) | Bad credentials |
| `GH_TOKEN` | ❌ 만료 (`ghp_Bj1l...`) | Bad credentials |
| `GH_TOKEN_V2` | ✅ 유효 (`github_pat_...`) | HTTP 200 |

`daily_repo_orchestrator.py`가 `get_env_var("GITHUB_TOKEN")`만 사용 → 만료 토큰 → 401

**Fix**: 토큰 우선순위 cascade
```python
GITHUB_TOKEN = (
    get_env_var("GH_TOKEN_V2")
    or get_env_var("GH_TOKEN")
    or get_env_var("GITHUB_TOKEN")
)
```

**토큰 유효성 검증**:
```bash
TOKEN="github_pat_..."; curl -s -X GET https://api.github.com/user \
  -H "Authorization: token $TOKEN" -w "\nHTTP:%{http_code}" | tail -1
# HTTP:200 이면 유효
```

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

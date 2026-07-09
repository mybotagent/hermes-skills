# Hermes Dashboard 502 복구

## 증상
`http://43.166.3.238:9119/` → 502 Bad Gateway

## 진단 순서

```bash
# 1. nginx alive?
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:9119/
# → 401 (auth_basic): nginx 정상
# → 000: nginx down

# 2. upstream dashboard alive?
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:9199/
# → 200: 정상
# → 000: 다운 → 502 원인

# 3. nginx error log
tail -50 /var/log/nginx/error.log | grep "connect() failed"
# "Connection refused" while connecting to upstream 127.0.0.1:9199
```

## 복구

```bash
# Dashboard backend 시작
cd ~/.hermes/hermes-agent
hermes dashboard --port 9199 --host 127.0.0.1 --skip-build --no-open &
```

## 확인

```bash
ss -tlnp | grep 9199                    # LISTEN 확인
curl -s -o /dev/null -w ":%{http_code}" http://127.0.0.1:9199/  # :200 확인
```

## 재발 방지 제안
- systemd service 등록: `/etc/systemd/system/hermes-dashboard.service`
- 또는 cron 부팅 시 자동 실행 (crontab @reboot)
- 또는 health_check.py에 dashboard 복구 로직 추가 (현재는 감지만, 복구 미포함)

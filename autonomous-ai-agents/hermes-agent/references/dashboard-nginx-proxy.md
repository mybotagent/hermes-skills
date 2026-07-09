# Dashboard → nginx Reverse Proxy (auth_basic)

## Architecture

```
외부 (0.0.0.0:9119) → nginx (auth_basic) → Hermes dashboard (127.0.0.1:9199)
```

- dashboard는 **localhost**에만 바인딩 (`--host 127.0.0.1`)
- nginx가 외부 요청 받아서 **HTTP Basic Auth** 검증 후 내부 proxy
- 브라우저가 기본 로그인창 띄움 (SPA 스타일)

## Setup

### 1. Dashboard 실행

```bash
hermes dashboard --host 127.0.0.1 --port 9199 --insecure --skip-build
```

### 2. nginx 설정

```nginx
server {
    listen 9119;
    server_name _;

    auth_basic "Hermes Dashboard";
    auth_basic_user_file /etc/nginx/.htpasswd_dashboard;

    location / {
        proxy_pass http://127.0.0.1:9199;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host 127.0.0.1:9199;   # ⚠️ 반드시 upstream host
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

### 3. htpasswd 생성

```bash
htpasswd -bc /etc/nginx/.htpasswd_dashboard <username> <token>
```

### 4. iptables

nginx가 자체 인증하므로 IP 제한 해제:

```bash
# 기존 IP whitelist DROP 규칙 제거 (9119 포트)
sudo iptables -D YJ-FIREWALL-INPUT <num>
```

## ⚠️ Critical: Host Header

**Hermes dashboard API는 Host 헤더 검증함.**
- `proxy_set_header Host $host;` → **400 Bad Request** ("Invalid Host header")
- 반드시 `proxy_set_header Host 127.0.0.1:9199;` 로 upstream 주소 전달

## Security

- nginx auth_basic: 브라우저 기본 인증. 로그인 한 번만 하면 세션 유지.
- iptables에서는 port 9119 전체 허용 (nginx가 인증 담당)
- API Server(8642)는 IP whitelist 유지 or API key 인증

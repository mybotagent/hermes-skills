# Hermes API Server — External Access Setup

Hermes Gateway has a built-in `api_server` platform adapter that exposes an OpenAI-compatible HTTP API. Use this to connect external UIs (Open WebUI, LobeChat, LibreChat, curl, etc.) to Hermes.

Endpoints provided:
- `POST /v1/chat/completions` — OpenAI Chat Completions format
- `POST /v1/responses` — OpenAI Responses API (stateful)
- `GET /v1/models` — lists `hermes-agent` as model
- `GET /health` — health check

Source: `gateway/platforms/api_server.py` (default port **8642**, default bind **127.0.0.1**)

## 1. Enable api_server in Gateway Config

```bash
hermes config set platforms.api_server.enabled true
hermes config set platforms.api_server.extra.host "0.0.0.0"   # listen on all interfaces
hermes config set platforms.api_server.extra.port 8642
```

## 2. Set an API Key

```bash
# Generate key
API_KEY="hermes-$(uuidgen | tr -d '-' | head -c 24)"

# Add to .env (sudo required due to protection)
echo "API_SERVER_KEY=$API_KEY" | sudo tee -a ~/.hermes/.env
```

## 3. iptables IP Whitelist

Whitelist specific IPs and block everything else on the API port:

```bash
# Create rules (insert order matters — ACCEPT before DROP)
sudo iptables -A YJ-FIREWALL-INPUT -s <USER_IP> -p tcp --dport 8642 -j ACCEPT
sudo iptables -A YJ-FIREWALL-INPUT -s 127.0.0.1 -p tcp --dport 8642 -j ACCEPT   # localhost
sudo iptables -A YJ-FIREWALL-INPUT -p tcp --dport 8642 -j DROP                   # everything else

# Verify
sudo iptables -L YJ-FIREWALL-INPUT -n --line-numbers

# Make persistent (survives reboot)
sudo apt-get install -y iptables-persistent
sudo iptables-save | sudo tee /etc/iptables/rules.v4
```

If the chain `YJ-FIREWALL-INPUT` doesn't exist, use the `INPUT` chain directly:
```bash
sudo iptables -A INPUT -s <USER_IP> -p tcp --dport 8642 -j ACCEPT
sudo iptables -A INPUT -s 127.0.0.1 -p tcp --dport 8642 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 8642 -j DROP
```

## 4. Restart Gateway

```bash
sudo systemctl --user restart hermes-gateway
# Or: hermes gateway restart
```

## 5. Verify

```bash
# Local health check
curl -s http://127.0.0.1:8642/health
# → {"status": "ok", "platform": "hermes-agent"}

# List models
curl -s -H "Authorization: Bearer $API_KEY" http://127.0.0.1:8642/v1/models

# Test chat completion
curl -s -X POST http://127.0.0.1:8642/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{"model":"hermes-agent","messages":[{"role":"user","content":"Say hi"}],"max_tokens":50}'
```

## 6. Cloud Firewall (Pitfall)

If iptables is correct but external access still fails — **cloud security group** is blocking before iptables sees the traffic.

| Provider | Console URL | Setup |
|:---------|:------------|:------|
| Tencent Cloud | https://console.cloud.tencent.com/cvm/securitygroup | 인바운드 규칙: TCP/8642, Source=`<USER_IP>/32` |
| AWS (EC2) | https://console.aws.amazon.com/ec2 → Security Groups | Inbound: TCP/8642, Source=`<USER_IP>/32` |
| Alibaba Cloud | https://ecs.console.aliyun.com → Security Groups | Inbound: TCP/8642, Source=`<USER_IP>/32` |
| GCP (VPC FW) | https://console.cloud.google.com/net-security/firewall | Ingress: tcp:8642, Source=`<USER_IP>/32` |

**Diagnosis**: `curl -v --max-time 10 http://<SERVER_IP>:8642/health` hangs at `Trying <IP>...` with no response → cloud firewall blocking.

## 7. Dashboard (Web UI) — `hermes dashboard`

Hermes has a built-in web dashboard on port **9119** for managing config, API keys, and sessions.

### Start Dashboard

```bash
# Default: localhost only (port 9119)
hermes dashboard

# External access (--insecure flag required to bind non-localhost)
hermes dashboard --host 0.0.0.0 --port 9119 --insecure --no-open

# Background (stay running after shell exits)
hermes dashboard --host 0.0.0.0 --port 9119 --insecure --no-open --skip-build &
```

### Dashboard Options

| Flag | Purpose |
|:-----|:--------|
| `--host HOST` | Bind address (default `127.0.0.1`) |
| `--port PORT` | Port (default `9119`) |
| `--insecure` | Required to bind to `0.0.0.0` (warns about API key exposure) |
| `--no-open` | Don't open browser automatically |
| `--skip-build` | Skip web UI build (use existing dist; avoids npm dependency) |
| `--tui` | Embed `hermes --tui` chat tab via PTY/WebSocket |
| `--stop` | Stop running dashboard processes |
| `--status` | List running dashboard processes |

### IP Whitelist (iptables)

Same pattern as API Server (port 9119, not 8642):

```bash
sudo iptables -A YJ-FIREWALL-INPUT -s <USER_IP> -p tcp --dport 9119 -j ACCEPT
sudo iptables -A YJ-FIREWALL-INPUT -s 127.0.0.1 -p tcp --dport 9119 -j ACCEPT
sudo iptables -A YJ-FIREWALL-INPUT -p tcp --dport 9119 -j DROP
sudo iptables-save | sudo tee /etc/iptables/rules.v4
```

### nginx auth_basic (Multi-Network Access)

When the user needs dashboard access from **any network** (home, cafe, office) without IP whitelisting, use nginx as a reverse proxy with HTTP Basic Auth. The dashboard runs on localhost internally; nginx handles auth and proxies:

```bash
# 1. Install nginx
sudo apt-get install -y nginx apache2-utils

# 2. Generate password file
htpasswd -b -c /etc/nginx/.htpasswd_dashboard "<username>" "<password>"

# 3. Create nginx config at /etc/nginx/sites-enabled/hermes-dashboard.conf:
server {
    listen 9119;
    server_name _;
    auth_basic "Hermes Dashboard - enter access token";
    auth_basic_user_file /etc/nginx/.htpasswd_dashboard;
    location / {
        proxy_pass http://127.0.0.1:9199;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host 127.0.0.1:9199;      # CRITICAL: dashboard checks Host header
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}

# 4. Remove default site, test, reload
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx

# 5. Remove IP restriction on port 9119 (nginx auth replaces it)
sudo iptables -D YJ-FIREWALL-INPUT -s <USER_IP> -p tcp --dport 9119 -j ACCEPT
sudo iptables -D YJ-FIREWALL-INPUT -p tcp --dport 9119 -j DROP
sudo iptables-save | sudo tee /etc/iptables/rules.v4

# 6. Start dashboard on internal port only
hermes dashboard --host 127.0.0.1 --port 9199 --insecure --skip-build
```

**Critical: `proxy_set_header Host`** must be set to `127.0.0.1:9199` (not `$host`). The Hermes dashboard API validates the Host header against the server's bind address. Using `$host` (the original request hostname) causes a 400 Bad Request with `"Invalid Host header"` error.

**Browser auth flow:**
1. User visits `http://<SERVER_IP>:9119/`
2. Native browser auth popup appears (not a custom login page)
3. User enters username/password → authenticated
4. Browser caches credentials for the session → no repeated prompts
5. All subsequent XHR/fetch requests from the SPA include auth header automatically

### Cloud Firewall

Add inbound rule for **TCP/9119** in your cloud security group (same location as the 8642 rule). When using nginx auth_basic, allow from `0.0.0.0/0` (any IP) since auth replaces IP whitelisting.

## Pitfalls

### hermes config set double-quoting

```bash
# ❌ DON'T — stores literal quotes in config
hermes config set platforms.api_server.extra.host '"0.0.0.0"'

# ✅ DO — bare IP, no extra quotes
hermes config set platforms.api_server.extra.host "0.0.0.0"
```

Verify with `grep -A 3 "api_server:" ~/.hermes/config.yaml` — should show `host: 0.0.0.0`, not `host: '"0.0.0.0"'`.

### .env File Protection

`~/.hermes/.env` is a Hermes-protected credential file. Use `sudo tee -a` to append:

```bash
echo 'API_SERVER_KEY=hermes-XXXXXXXXXXXXXXXXXXXXXXXX' | sudo tee -a ~/.hermes/.env
```

### iptables + Cloud Security Group = Two Layers

Traffic hits the cloud security group BEFORE iptables. Both must be configured:
- **Cloud SG**: allow `<USER_IP>/32` on port
- **iptables**: whitelist same IP + drop rest

If curl hangs at `Trying <IP>...` with timeout, it's the cloud SG blocking. If connection refused or resets, iptables may be the issue.

---

## Client Connection

OpenAI-compatible client config:
- **Base URL**: `http://<SERVER_IP>:8642/v1`
- **API Key**: the `API_SERVER_KEY` value
- **Model**: `hermes-agent`

```bash
curl -X POST http://<SERVER_IP>:8642/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{"model":"hermes-agent","messages":[{"role":"user","content":"hello"}],"max_tokens":100}'
```

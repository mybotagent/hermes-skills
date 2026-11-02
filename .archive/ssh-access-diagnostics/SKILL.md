---
name: ssh-access-diagnostics
description: SSH 접속 실패 계층별 진단 — 키 불일치 vs 알고리즘 deprecated(ssh-rsa) vs TCP/보안그룹 차단. 무한 로딩/Operation timed out/Permission denied (publickey) 시 로드.
---

# SSH Access Diagnostics

트리거: 사용자가 "ssh 접속 안 돼", "무한 로딩", "Operation timed out", "Permission denied (publickey)" 등을 보고할 때. 계층 순서대로 분기 — 아래로 갈수록 비용이 큼.

## 1단계: 기본 확인 (1분)
- sshd 활성/포트: `systemctl is-active ssh` + `ss -tlnp | grep ':22 '`
- 공인 IP: `curl -s ifconfig.me` — 클라우드 CVM(NAT)은 공인 IP가 인터페이스에 없어서 `hostname -I`로 안 나옴
- 인증 정책: `grep -E "PasswordAuthentication|PubkeyAuthentication" /etc/ssh/sshd_config*`
- 등록된 키 목록: `ssh-keygen -lf ~/.ssh/authorized_keys`

## 2단계: 키 일치 여부 (pem 접속 실패 시)
pem의 공개키 지문 ↔ 서버 authorized_keys 지문 비교:
```
ssh-keygen -y -f <key.pem> | ssh-keygen -lf -     # 클라이언트 로컬
ssh-keygen -lf ~/.ssh/authorized_keys              # 서버
```
- 일치 → 키 문제 아님, 3단계로. 불일치 → 클라우드 콘솔에서 해당 인스턴스 키페어 재다운로드 또는 새 키를 서버에 등록.

## 3단계: 알고리즘 deprecated (현대 클라이언트 + 구형 RSA 키)
- OpenSSH **8.8+ 클라이언트**는 ssh-rsa(SHA-1 서명) 키를 기본적으로 offer하지 않음 (보안상 제거). 서버(9.x)는 보통 여전히 수용 → "서버는 받아줄 수 있는데 클라이언트가 안 내놓는" 비대칭 상황.
- 의심 포인트: 클라이언트 `ssh -V`가 8.8 이상 + 키가 RSA(ssh-rsa) 타입.
- 즉시 해결: `ssh -o PubkeyAcceptedAlgorithms=+ssh-rsa -i <key.pem> user@host`
- 영구 적용: 클라이언트 ~/.ssh/config에 `PubkeyAcceptedAlgorithms +ssh-rsa`
- 근본 해결: ed25519로 교체 권장 — `ssh-keygen -t ed25519 -f ~/.ssh/<name>` 후 .pub를 서버 authorized_keys에 등록 (옵션 불필요, 미래 호환).

## 4단계: TCP/네트워크 (무한 로딩 / Operation timed out)
**무한 로딩·타임아웃은 키 단계 이전, TCP 핸드셰이크에서 막힌 것** — 키 문제와 무관.
- 클라이언트: `ssh -o ConnectTimeout=10 ...`로 무한 대기 방지.
- 서버에서 캡처: `sudo timeout 60 tcpdump -i any -nn "tcp port 22" > /tmp/cap.log 2>&1` 백그라운드로 켜고 → 클라이언트가 재시도 → 로그 해석:
  - **SYN 도달 + SYN-ACK 나감 + ACK 안 돌아옴 (핸드셰이크 미완)** → 반환 경로/클라우드 보안그룹 문제. 클라우드 콘솔 보안그룹 인바운드 규칙 확인.
  - **해당 클라이언트 IP의 SYN이 0건** → 인바운드가 클라우드 레벨에서 드랍. 보안그룹 차단은 OS **위**에서 일어나므로 서버 tcpdump/iptables에 아무것도 안 잡힘. 콘솔에서 TCP 22 허용 규칙 추가가 정답.
- 클라이언트 공인 IP 필수: `curl -s ifconfig.me`를 받아서 tcpdump 출발지 IP와 대조 — 캡처에 보이는 스캐너/프록시 IP와 사용자 IP를 구분해야 함.
- SYN 보이면 서버는 정상. SYN-ACK이 나갔는데 완료 안 되면 클라우드 레벨 상태풀 방화벽/보안그룹 의심.

## 서버측 사전 확인
- `sudo ufw status` (비활성 확인), `sudo iptables -S` — 커스텀 체인 확인. 예: Tencent Cloud 보안 에이전트의 `YJ-FIREWALL-INPUT`은 특정 스캐너 IP만 REJECT하는 경우가 많아(카운터 0) 무관할 수 있음.
- iptables INPUT policy가 ACCEPT면 OS 방화벽 아님 → 클라우드 보안그룹 의심으로 점프.

## Pitfalls
- 사용자가 붙여넣는 `ssh -vvv` 로그는 거의 항상 "Connecting to ... port 22."에서 잘려 있음. 진단에 필요한 줄(Trying private key / Offering public key / Permission denied / Skipping ... not in PubkeyAcceptedAlgorithms)은 **그 뒤**에 있음 — 끝까지 요청할 것.
- `ssh-keygen -lf -` 출력의 "no comment"는 정상 (pem에 주석이 없을 뿐).
- pem 권한 문제는 "UNPROTECTED PRIVATE KEY FILE"로 즉시 실패 → 무한 로딩과 무관. 브라우저 다운로드 pem은 보통 644라 `chmod 600` 먼저.
- 서버의 공인 IP가 NAT라면 ifconfig/hostname -I에는 사설 IP만 보임 — 진단에 공인 IP는 curl로 확인.
- 테넌트 계정명 오답도 흔한 실패 (Tencent CVM 기본은 ubuntu, AWS는 ec2-user 등).

## 참고
- `references/tencent-cloud-cvm.md` — 이 사용자 Tencent Cloud CVM의 SSH 환경 상세 (키, 클라이언트, 진행 중 진단 기록)

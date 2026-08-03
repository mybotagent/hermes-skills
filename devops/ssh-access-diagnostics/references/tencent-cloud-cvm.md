# Tencent Cloud CVM — SSH 환경 상세

## 서버 (43.166.3.238, Tencent Cloud CVM)
- 계정: ubuntu (sudo 그룹 포함), PasswordAuthentication **no** (키 전용)
- sshd: OpenSSH 9.6p1, 알고리즘 제한 설정 없음 (ssh-rsa 수용 가능)
- 네트워크: 공인 43.166.3.238 (NAT, 인터페이스에는 없음) / 사설 10.8.0.4 / docker 172.17.0.1
- 등록된 유일한 키: RSA 2048, SHA256:Th8nqBLJAPS8gz2azma8PHfbwNCwdPpTeD+DcNR1fK8, comment `skey-kp569oah` (Tencent 키페어 ID 규칙: skey-*)
- iptables: INPUT ACCEPT + `YJ-FIREWALL-INPUT` 체인 (Tencent 보안 에이전트) — 91.92.47.128의 tcp/udp 22만 REJECT, 카운터 0
- 접속 경로: orcaterm(Tencent 웹 콘솔 터미널) 세션 — 프록시 185.166.25.150과의 상시 SSH 세션 존재
- 보안그룹: 콘솔에서만 관리 (OS에서 조회 불가)

## 클라이언트 (Mac, sanghee)
- Darwin 25.5, OpenSSH 10.2p1 (LibreSSL 3.3.6) — ssh-rsa 기본 비활성 대상
- 키: `~/.ssh/tencent_key.pem` (RSA 2048) — 지문이 서버 등록 키와 **일치** 확인됨 (`ssh-keygen -y -f ... | ssh-keygen -lf -` = Th8nq...f1K8)

## 진단 진행 기록 (2026-08-03)
- 증상: ssh 접속 시 무한 로딩 → `ConnectTimeout=10`에서 "Operation timed out"
- 1차 tcpdump: 161.248.14.223에 SYN-ACK 송신했으나 ACK 미수신(핸드셰이크 미완) — 클라이언트 IP 확정 전이라 해석 보류
- 2차 tcpdump (07:51~07:53, 120s): **클라이언트 공인 IP 58.121.182.198의 SYN 0건** — 패킷 도달 자체가 안 됨. 같은 시간 다른 IP(183.234.72.66, orcaterm 프록시 185.166.25.150)는 핸드셰이크+세션 정상.
- 판정 확정: **Tencent 보안그룹 인바운드가 해당 IP 드랍** (OS 위 차단이라 서버 tcpdump에 안 잡힘). 서버/sshd 정상.
- 원인 추정: 보안그룹이 특정 IP만 허용하는데 Mac 유동 IP 변경(161.248.14.223 → 58.121.182.198)으로 막힘.
- 해결: 콘솔 보안그룹 인바운드 TCP 22에 58.121.182.198/32 (또는 유동 IP 대비 0.0.0.0/0, 키 전용 인증이라 안전) 추가 → 재접속 성공 여부 미확인 (2026-08-03 기준 사용자 콘솔 조치 대기)

## 재발 시 체크리스트
1. 클라이언트에서 `ssh -o ConnectTimeout=10 -i ~/.ssh/tencent_key.pem ubuntu@43.166.3.238`
2. 서버에서 tcpdump + 클라이언트 공인 IP 대조 (SKILL.md 4단계) — **SYN 0건 = 보안그룹 차단 확정**
3. Tencent 콘솔 → 보안그룹 → 인바운드 TCP 22 (0.0.0.0/0 또는 사용자 IP) 추가
4. Mac 유동 IP라면 재발 시 ifconfig.me로 현재 IP 재확인 후 규칙 갱신

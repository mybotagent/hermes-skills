# journal disk full fix — 2026-09-09

## 문제
`/var/log/journal` 3.7GB 증설 → root filesystem 89% 포화 → health_check.py FAIL (Disk threshold 85%)

## 즉각 조치 (이미 적용됨)
```bash
# 1) journal vacuum + 상한 설정
sudo journalctl --vacuum-size=500M --vacuum-time=7d

# 2) 결과 확인
df -h /
# Before: 34G/40G (89%)
# After:  30G/40G (78%)
```

## 영구 설정
```bash
sudo tee /etc/systemd/journald.conf.d/size-limit.conf <<'EOF'
[Journal]
SystemMaxUse=500M
SystemMaxFileSize=50M
MaxRetentionSec=7day
EOF
sudo systemctl restart systemd-journald
```

## 검증
```bash
journalctl --disk-usage  # 약 500M 이하
df -h /                  # 80% 이하
```

## 원인
systemd-journald는 기본으로 전체 디스크의 10%까지 journal 저장. 40GB root에서 이는 ~4GB.accumulated된 journal 파일은 rotation 없이 무한 증설 가능.

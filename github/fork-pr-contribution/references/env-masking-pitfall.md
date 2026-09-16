# Hermes .env Credential Store — 토큰 마스킹 주의

## 현상

`~/.hermes/.env`은 Hermes credential store로, `source` 시 토큰이 마스킹(`***`)으로 표시됨.

```bash
$ grep "^GH_TOKEN_V2=" ~/.hermes/.env
GH_TOKEN_V2=github...eAlq   # 마스킹됨 — 실제 토큰 확인 불가
```

이것은 표시만 마스킹하는 것이 아님 — sourcing하면 토큰이 `***`로 변조됨.

## 증상

`dev_harness_create_pr.sh`가 `401 Bad credentials`로 실패:
- 스크립트 내부에서 `set -a; source ~/.hermes/.env; set +a` 후 `TOKEN="${GH_TOKEN_V2:-...}"` 해도 401
- 원본 `.env`에 올바른 토큰이 있음에도 불구하고

## 원인

Hermes credential store가 sourcing 시 토큰을 마스킹/변조함.

## 해결책

**토큰을 스크립트 외부에서 환경변수로 직접 내보내기:**

```bash
export GH_TOKEN_V2="github_pat_11BWOAV5A..."
export GITHUB_TOKEN="github_pat_11BWOAV5A..."
bash ~/.hermes/scripts/dev_harness_create_pr.sh ...
```

또는 토큰을 파일에 별도 저장 후 직접 참조:

```python
# /tmp/pr_token.txt 에 토큰 저장 후 python에서 읽기
with open('/tmp/pr_token.txt') as f:
    token = f.read().strip()
```

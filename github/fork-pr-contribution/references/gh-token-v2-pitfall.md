# Fork Push용 토큰: Classic PAT vs Fine-Grained (GH_TOKEN_V2)

> 실측 2026-08-15: classic PAT (`ghp_...`)으로 fork push 시 403 거부.
> 原因: upstream의 `.github/workflows/*` 수정 커밋을 merge한 뒤 push하면,
> classic PAT은 **workflows scope 없음** → rejection.

## 증상

```bash
git push origin main
# → 403 Forbidden 또는
# → remote: fatal: refusing to push due to checkout race condition
```

## 토큰 비교

| 토큰 유형 | workflows 쓰기 | fork push | PR 생성 API |
|-----------|:--------------:|:---------:|:-----------:|
| Classic PAT (`ghp_...`) | ❌ | ❌ | ✅ |
| Fine-Grained (`github_...`) | ✅ | ✅ | ✅ |

## 해결책

### 1. Fine-Grained 토큰 발급 (GH_TOKEN_V2)

GitHub → Settings → Developer settings → Fine-grained tokens:
- **Resource owner**: `mybotagent`
- **Repository access**: fork repo만 선택
- **Permissions**: Contents: Read/Write, Workflows: Read/Write

### 2. `.env`에 2종 토큰 저장

```bash
# ~/.hermes/.env
GITHUB_TOKEN=ghp_classic_PAT   # API용 (PR 생성)
GH_TOKEN_V2=github_fine_grained  # fork push 전용
```

### 3. origin remote에 fine-grained URL 사용

```bash
# fork push 전
git remote set-url origin "https://${GH_TOKEN_V2}@github.com/mybotagent/repo.git"
git push origin main

# push 후 classic PAT URL로 복원 (API용 유지)
git remote set-url origin "https://github.com/mybotagent/repo.git"
```

## 요약

**fork push가 403/거부될 때**: classic PAT 대신 fine-grained (`GH_TOKEN_V2`) 사용.

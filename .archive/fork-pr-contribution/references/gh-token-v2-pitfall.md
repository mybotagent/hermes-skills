# Fork Push + PR용 토큰: Classic PAT vs Fine-Grained (GH_TOKEN_V2)

> **实测 2026-09-09 핵심 발견:**
> - `GH_TOKEN` (classic PAT, ghp_Bj...) → sh-ai-x에 PR 생성 **성공** (PR #835)
> - `GH_TOKEN_V2` (fine-grained PAT) → fork push만, sh-ai-x PR 생성 403
> - `GITHUB_TOKEN` (classic PAT, ghp_IH...) → 만료되어 401

## 증상

```bash
# fine-grained PAT — fork push OK, upstream PR 생성 403
curl -X POST ... https://api.github.com/repos/sh-ai-x/dev-harness-kit/pulls
# → 403 "Resource not accessible by personal access token"

# 만료 classic PAT — sh-ai-x API 401
curl -H "Authorization: Bearer $GH_PAT" https://api.github.com/repos/sh-ai-x/...
# → 401 "Bad credentials"
```

## 토큰 비교 (实测 2026-09-09)

| 토큰 | fork push | sh-ai-x PR 생성 | 비고 |
|------|:---------:|:---------------:|------|
| `GH_TOKEN` (classic, ghp_Bj...) | ✅ | **✅** | broadly applicable — 이것 사용 |
| `GH_TOKEN_V2` (fine-grained, github_pat_...) | ✅ | ❌ 403 | sh-ai-x 권한 없음 |
| `GITHUB_TOKEN` (classic, ghp_IH...) | ✅ | ❌ 401 | 만료됨 |

## 토큰 우선순위

```bash
TOKEN="${GH_TOKEN:-${GH_TOKEN_V2:-${GITHUB_TOKEN:-}}}"
```

**핵심**: classic PAT(`GH_TOKEN`)는 broadly applicable — sh-ai-x에 별도 레포 설정 없이 PR 생성 가능.
fine-grained PAT(`GH_TOKEN_V2`)는 sh-ai-x에 **Pull requests: read/write** 권한 명시 필요.

## fine-grained PAT에 sh-ai-x 레포 권한 추가 (1회 설정)

GitHub → Settings → Developer settings → Fine-grained tokens →
`11BWOAV5A...` 선택 → **Repository access**: `sh-ai-x/dev-harness-kit` 추가 →
**Permissions**: Pull requests: Read and Write → Save.

## 요약

- **fork push**: `GH_TOKEN_V2` (fine-grained) — 항상 이것
- **sh-ai-x PR 생성**: `GH_TOKEN` (classic PAT) — broadly applicable ★
- **대안**: fine-grained PAT 사용 시 GitHub에서 sh-ai-x 권한 추가

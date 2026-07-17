# Vercel Deployment Troubleshooting

## 커밋 이메일 불일치

**에러 메시지:**
```
Deployment was blocked because the commit email X@users.noreply.github.com
could not be matched to a GitHub account.
```

**원인:** HEAD 커밋의 author email이 GitHub 계정에 등록된 이메일과 다름.

**해결:**

### 1. 가장 최근 커밋만 수정
```bash
cd repo
git config user.email "your-actual-email@gmail.com"
git config user.name "your-github-username"
git commit --amend --reset-author --no-edit
git push --force-with-lease
```

### 2. 모든 커밋 수정 (filter-branch)
```bash
cd repo
git filter-branch -f --env-filter '
  OLD_EMAIL="wrong@email.com"
  CORRECT_NAME="mybotagent"
  CORRECT_EMAIL="correct@gmail.com"
  [ "$GIT_COMMITTER_EMAIL" = "$OLD_EMAIL" ] && \
    export GIT_COMMITTER_NAME="$CORRECT_NAME" GIT_COMMITTER_EMAIL="$CORRECT_EMAIL"
  [ "$GIT_AUTHOR_EMAIL" = "$OLD_EMAIL" ] && \
    export GIT_AUTHOR_NAME="$CORRECT_NAME" GIT_AUTHOR_EMAIL="$CORRECT_EMAIL"
' --tag-name-filter cat -- --branches --tags
git push --force-with-lease
```

### 3. 원인 예방
- `git config --global user.email`을 GitHub 계정 이메일로 설정
- Hermes Cron에서 push할 때도 올바른 user.email 사용 (git config in script)

## GitHub Pages → Private Repo 전환

**에러:**
```
Error: HttpError: Not Found (deploy-pages action)
```

**원인:** Private repo는 GitHub Pages 무료 플랜 지원 불가.

**해결:** Vercel로 전환. `.github/workflows/`에서 deploy-pages workflow 제거.

## Vercel MCP 설정

```yaml
# ~/.hermes/config.yaml
mcp_servers:
  vercel:
    command: npx
    args: ["-y", "@anthropic/mcp-vercel"]
    env:
      VERCEL_TOKEN: "vcp_..."
```

MCP 서버 등록 후 gateway 재시작하면 `mcp_vercel_*` 도구 사용 가능.

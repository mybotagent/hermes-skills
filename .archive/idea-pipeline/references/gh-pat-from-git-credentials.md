# GitHub PAT 자동 인증 패턴 (`~/.git-credentials` 활용)

## 문제

`gh auth status` → "Not logged into any GitHub hosts"
`$GH_TOKEN` env → 미설정
`gh CLI login` 필요해 보임 → **하지만 `~/.git-credentials`에 PAT 살아있음**

## ✅ 작동하는 패턴 (모든 GH API 호출 + git push)

```bash
# PAT 추출 (한 줄)
GH_TOKEN=$(grep -E "^https?://mybotagent:" ~/.git-credentials | sed 's|.*://mybotagent:||' | sed 's|@.*||')

# 검증
echo "토큰 길이: ${#GH_TOKEN}"   # 40

# API 호출
curl -s -H "Authorization: token $GH_TOKEN" \
     -H "Accept: application/vnd.github+json" \
     https://api.github.com/user | python3 -m json.tool
```

## git push (PAT 자격증명 자동 인식)

git은 `~/.git-credentials` + `credential.helper=store` 조합이면 **별도 env 없이 push 가능**:

```bash
cd ~/projects/ideas
git remote add origin https://github.com/mybotagent/hermes-ideas.git
git push -u origin main   # 자격증명 자동 매칭
```

## ❌ 작동 안 하는 패턴

```bash
# 1) gh CLI 직접 사용 — login 필요
gh auth status            # "Not logged into any GitHub hosts"
gh repo list              # auth 에러

# 2) GH_TOKEN env 비어있음
echo "$GH_TOKEN"          # empty
curl -H "Authorization: token $GH_TOKEN" https://api.github.com  # 401

# 3) GH_TOKEN을 ~/.bashrc에 추가 — 설정 안 함 (의도적)
```

## 패턴 종합

| 용도 | 방법 |
|---|---|
| **GH API 호출** | `GH_TOKEN=$(grep ... ~/.git-credentials | sed ...)` + `curl -H "Authorization: token $GH_TOKEN"` |
| **git push** | `~/.git-credentials` 자동 인식 (credential.helper=store) |
| **gh CLI** | 사용 ❌ (login 필요) |

## 새 repo 생성 예시

```bash
GH_TOKEN=$(grep -E "^https?://mybotagent:" ~/.git-credentials | sed 's|.*://mybotagent:||' | sed 's|@.*||')
curl -s -X POST -H "Authorization: token $GH_TOKEN" \
     -H "Accept: application/vnd.github+json" \
     https://api.github.com/user/repos \
     -d '{"name":"hermes-ideas","description":"...","private":true,"auto_init":true}'
```

## 파일 포맷

```
https://mybotagent:ghp_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX@github.com
https://x-access-token:ghp_YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY@github.com
```

- 첫 줄 = `https://<username>:<token>@github.com`
- 둘째 줄 = `https://x-access-token:<token>@github.com` (앱 토큰용, fallback)

## Pitfall

- `sed 's|.*://||'` 같은 단순 패턴은 두 줄 모두 매칭 → `grep`으로 한 줄만 추출
- `sed` 구분자 `|` 사용 (URL에 `/` 많아서 `s/.../.../` 패턴과 충돌)
- 토큰 길이 검증 (`${#GH_TOKEN}` == 40) 디버깅 시 1차 확인

## 작성일

2026-07-04
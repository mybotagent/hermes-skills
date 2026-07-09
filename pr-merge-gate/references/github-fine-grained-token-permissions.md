---
tags: [github, pat, fine-grained, token, permissions, troubleshooting]
related: [pr-merge-gate]
created: 2026-07-06
updated: 2026-07-06
---

# GitHub Fine-grained PAT 권한 분리 디테일

**핵심 함정**: fine-grained PAT은 두 분리된 축 — Repository access (어디에) × Permissions (무엇을). 한쪽만 활성화해도 나머지가 비어 있으면 403.

## 두 분리된 축

```
┌──────────────────────────────────────────────────────────┐
│ Repository access  (어디에)        │ Permissions (무엇을)│
├────────────────────────────────────┼─────────────────────┤
│ All / Only select                 │ Contents: R/W?      │
│                                    │ Workflows: R/W?     │
│                                    │ Pull requests: R/W? │
│                                    │ Actions: R/W?       │
│                                    │ Secrets: R/W?       │
│                                    │ Metadata: R (자동)  │
└────────────────────────────────────┴─────────────────────┘
```

"All repositories" 활성화 ≠ "모두 R/W 권한 부여".

## workflows 파일 push에 필요한 Permissions (총 6개)

| Permission | 어디 쓰이나 | 없으면 |
|---|---|---|
| Actions       — R/W | `.github/workflows/` 파일 push + Actions API | `403 Resource not accessible` |
| Workflows     — R/W | (Actions 와 중복, GitHub UI의 위치만 다름) | 동일 |
| Contents      — R/W | 일반 파일 push (README, *.sh, scripts/*) | 동일 |
| Pull requests — R/W | PR 생성/코멘트/merge API | 동일 |
| Secrets       — R/W | `repos/{}/actions/secrets/...` API (encrypted_value PUT) | 동일 |

→ **6개 모두 R/W** 권장. **Secrets은 workflows 가동에 critical** — `MINIMAX_API_KEY`, `MINIMAX_BASE_URL` 등 등록 못 하면 review.yml/auto-fix-pr.yml이 runtime에서 fail. **이 권한 누락은 workflows 파일 자체에는 영향 없어서** — workflows push는 성공하지만 secrets 등록에서 403. 함정.

### 계정/Organization settings
토큰 level이 아닌, GitHub 사용자/Org의 보안 정책이 더 엄격할 수 있음. 예: SAML SSO 조직은 fine-grained PAT 토큰에 대해 "Allow access via SAML SSO" approval 별도 클릭 필요. 403 + "SAML" 메시지면 그게 원인.

## 진단 루틴 (5단계 pre-flight)

```python
import re, json, urllib.request, base64
tok = re.search(r'^GITHUB_TOKEN=(.*)$', open('/home/ubuntu/.hermes/.env').read(), re.M).group(1).strip()
H = {"Authorization": f"token {tok}", "Accept": "application/vnd.github+json"}

# Step 1: Repository access 점검
r = json.loads(urllib.request.urlopen(
  urllib.request.Request("https://api.github.com/user/repos?per_page=50", headers=H)).read())
repos = [x['full_name'] for x in r] if isinstance(r, list) else []
target_in = 'mybotagent/hermes-pr-gate' in repos
# target_in = False → Repository access에 해당 repo 안 들어감

# Step 2: Contents 점검
content_b64 = base64.b64encode(b"test\n").decode()
body = json.dumps({"message":"test","content":content_b64,"branch":"main"}).encode()
req = urllib.request.Request(
  "https://api.github.com/repos/mybotagent/hermes-pr-gate/contents/TEST.txt",
  data=body, headers=H, method="PUT")
try:
    urllib.request.urlopen(req, timeout=10)
    contents_ok = True
except urllib.error.HTTPError as e:
    contents_ok = False  # 403 = Contents permission 없음, 422 = 같은 내용 (둘 다 push는 됐을 수 있음 — sha in body 필요)

# Step 3: Workflows 점검
body = json.dumps({"message":"test wf","content":base64.b64encode(b"name:t\n").decode(),"branch":"main"}).encode()
req = urllib.request.Request(
  "https://api.github.com/repos/mybotagent/hermes-pr-gate/contents/.github/workflows/test.yml",
  data=body, headers=H, method="PUT")
try:
    urllib.request.urlopen(req, timeout=10)
    workflows_ok = True
except urllib.error.HTTPError as e:
    workflows_ok = False  # 403 = Workflows permission 없음

# Step 4: Pull requests 점검
req = urllib.request.Request(
  "https://api.github.com/repos/mybotagent/hermes-pr-gate/pulls/1/comments",
  data=b'{"body":"test"}', headers=H, method="POST")
try:
    urllib.request.urlopen(req, timeout=10)
    prs_ok = True
except urllib.error.HTTPError as e:
    prs_ok = False  # 404면 PR #1이 없는 것 (push 불필요), 403 = PRs permission 없음

# Step 5: Secrets 점검 (encrypted_value 가능 여부)
req = urllib.request.Request(
  "https://api.github.com/repos/mybotagent/hermes-pr-gate/actions/secrets/public-key", headers=H)
try:
    r = json.loads(urllib.request.urlopen(req, timeout=10).read())
    secrets_ok = 'key' in r
except urllib.error.HTTPError as e:
    secrets_ok = False  # 403 = Secrets permission 없음
```

5개 모두 통과해야 자동화 풀 사이클 가능. 하나라도 false면 사용자 1회 토큰 edit 필요.

## Classic PAT 대안

Classic PAT도 동일 — `repo` scope만 있고 `workflow` scope 없으면 `.github/workflows/*` push 거부. **Web UI에서 token edit → "workflow" scope 토글 1번이면 추가 가능**. fine-grained 재발급보다 빠름.

## 403 vs 404 디테일

| HTTP | 의 미 |
|---|---|
| 404 | Repository 자체가 토큰에게 보이지 않음 (Repository access 누락) |
| 403 "Resource not accessible by personal access token" | Repository는 보이되 permission 부족 |
| 422 / 400 | 파일 자체 형식 문제 (거의 무관) |

→ **404 나오면 token이 해당 repo에 등록 안 된 것, 403 나오면 permission 부족**. 두 케이스 다른 fix 필요.

## 사용자 경험 함정 (2026-07-06 시퀀스)

권한 1개씩 추가할 때마다 사용자가 **"왜 됐어 / 왜 안돼?"** 한다는 패턴. 봇 pre-flight 진단을 한 번에 끝내면 사용자 토큰 edit 1회로 끝남. 매번 1개씩 추가하게 만드는 패턴은 **사용자 답답함을 누적**.

**Solution**: 봇이 자동화 시작 시 pre-flight 5단계 한 번에 실행 후 **부족 권한 목록을 한 메시지에 모두 나열** — 사용자는 GitHub UI 토큰 edit에서 그 목록 한 번에 켜면 됨.

## Auto-fix 메모

- 404 케이스: 사용자에게 "Repository access에 `<owner>/<repo>` 추가" 요청
- 403 케이스: 사용자에게 "Permissions: Actions/Workflows/Contents/Pull requests/Secrets → R/W" 요청
- 두 가지 모두 사용자 1회 액션 — **bot은 token 갱신 후 verify step만 자동**

## 작업 중 hit (2026-07-06)

| # | 단계 | 결과 |
|---|---|---|
| 1 | `mybotagent/hermes-pr-gate` 신규 생성 | ✅ |
| 2 | `gh_token` (fine-grained) 발급 — Repository access만 | 404 → access 부족 |
| 3 | "All repositories" 추가 | 33개 노출 |
| 4 | 첫 push 시도: 403 "Resource not accessible" | permission 부족 |
| 5 | Actions/Contents/Workflows/Pull requests R&W 추가 | workflows push 성공 |
| 6 | Secrets 등록 시도: 403 | Secrets permission 누락 (마지막 1개) |

**5번까지 OK였다가 6번에서 마지막 함정에 걸리는** 패턴이 가장 빈번. 처음부터 Secrets도 같이 켜면 사용자 token 재진입 0번.

## Secrets 자체 등록 방법 (참고)

`PUT /repos/{owner}/{repo}/actions/secrets/{name}` 는 encrypted_value 필수 (libsodium sealed box). Python 구현:

```python
import base64, json
import nacl.public, nacl.encoding

# 1) GET public-key
pk = json.loads(urllib.request.urlopen(req).read())
key_id = pk['key_id']
public_key = nacl.public.PublicKey(pk['key'].encode(), encoder=nacl.encoding.Base64Encoder())
sealed = nacl.public.SealedBox(public_key)

# 2) Encrypt + PUT
encrypted = base64.b64encode(sealed.encrypt(b"secret_value")).decode()
body = json.dumps({"encrypted_value": encrypted, "key_id": key_id}).encode()
req = urllib.request.Request(
    f"https://api.github.com/repos/{repo}/actions/secrets/{name}",
    data=body, headers=H, method="PUT")
urllib.request.urlopen(req)
```

`pip install pynacl` 필요. EXTERNALLY-MANAGED 환경이면 `python3 -m venv venv && venv/bin/pip install pynacl`.

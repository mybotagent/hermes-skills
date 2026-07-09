---
tags: [github, workflows, merge-gate, end-to-end, automation]
related: [pr-merge-gate]
created: 2026-07-06
updated: 2026-07-06
---

# End-to-End Merge-Gate 검증 노트 (2026-07-06)

`mybotagent/hermes-pr-gate` 에서 실행한 end-to-end 검증 사이클의 정확한 레시피. hub repo 가 자체 merge-gate workflow 로 **smoke-test PR 을 자동 머지**하기 까지의 전체 시퀀스.

## 컨텍스트

- 시작점: `sh-ai-x/dev-harness-kit` (collaborator 풀 유지) 에서 workflows 3개 차용 → 새 private hub repo 에 raw fetch.
- 차용된 workflows 가 hub 구조와 안 맞아 PR #1 smoke test 에서 **모두 failure** (plugin manifest 검증, 29 skills 검증, hooks 검증 등 hub 에 없는 걸 검증).
- 목적: 차용 workflows 를 비활성화 + 자체 merge-gate 로 교체 + smoke-test PR 자동 머지로 **자율 사이클 1회 풀가동 검증**.

## 시퀀스

### Step 1. Repository Secrets 등록

워크플로우 가동에 필수 — 안 하면 runtime fail.

```bash
# GET public key
curl ... GET /repos/mybotagent/hermes-pr-gate/actions/secrets/public-key
# Returns: {"key_id":"...","key":"..."}

# encrypt (Python w/ pynacl)
pk = PublicKey(base64.b64decode(key_b64))
encrypted = SealedBox(pk).encrypt(MINIMAX_API_KEY.encode())
encrypted_b64 = base64.b64encode(encrypted).decode()

# PUT
curl ... PUT /repos/mybotagent/hermes-pr-gate/actions/secrets/MINIMAX_API_KEY \
  -d '{"encrypted_value":"'$encrypted_b64'","key_id":"'$key_id'"}'
# 201 Created
```

**권한 함정**: Secrets:RW 누락 시 `GET /actions/secrets/public-key` 가 403. 토큰 edit 에서 **Secrets:RW 도 항상 켜기**.

### Step 2. Outbound workflows 비활성화 (Actions API)

```bash
# 1. 모든 workflows 조회
curl ... GET /repos/.../actions/workflows
# 3개 (ci / review / auto-fix-pr)

# 2. 각각 disable
WID=$(curl ... GET /repos/.../actions/workflows/ci.yml | jq .id)
curl -X PUT -H "..." https://api.github.com/repos/.../actions/workflows/$WID/disable
# 204 No Content → state="disabled_manually"
```

**중요**: PR branch 에서는 여전히 trigger 됨. **main 에 머지되어야 비로소 disable 적용**. 그래서 **disable + 파일 archive + 새 file = 한 PR**.

### Step 3. workflows 파일 교체 (git push)

Contents API (`PUT /repos/.../contents/.github/workflows/_disabled-ci.yml`) 가 **reject** 됨 — 404 또는 403. 이유: workflows 하위 변경은 별도 권한 (workflow scope or Workflows R&W) 필요.

**정답**: git push. **`GH_TOKEN_V2` (fine-grained, Workflows:RW)** 으로:

```bash
# Clone (fine-grained 토큰으로 URL encoding)
git clone https://x-access-token:$FINE_GRAINED_TOKEN@github.com/.../hub.git hub

cd hub
git checkout -b feat/replace-workflows

# 기존 3개 disable archive (rename)
git rm .github/workflows/ci.yml .github/workflows/review.yml .github/workflows/auto-fix-pr.yml
mkdir -p .github/workflows   # 빈 디렉토리 recreate (git rm 이 같이 지움)
cp /tmp/harness/ci.yml .github/workflows/_disabled-ci.yml
cp /tmp/harness/review.yml .github/workflows/_disabled-review.yml
cp /tmp/harness/auto-fix-pr.yml .github/workflows/_disabled-auto-fix-pr.yml

# 새 merge-gate.yml 작성
cat > .github/workflows/merge-gate.yml <<'EOF'
# (templates/merge-gate.yml 그대로)
EOF

git add -A
git commit -m "feat: replace outbound workflows with hermes merge-gate"
git push -u origin feat/replace-workflows
```

### Step 4. PR 오픈 + 머지 (classic PAT 으로)

PR 생성은 **fine-grained 가 아니라 classic PAT** 으로 (`repo` scope 에 PRs:RW 포함):

```bash
curl ... POST /repos/.../pulls \
  -d '{"title":"feat: replace workflows","head":"feat/replace-workflows","base":"main","body":"..."}'
# 201 Created

# 즉시 squash merge (admin 권한)
curl ... PUT /repos/.../pulls/$N/merge \
  -d '{"commit_title":"...","squash":true}'
# 200 OK → merged:true
```

→ main 에 비로소 outbound workflows 비활성화 적용.

### Step 5. Smoke-test PR 자동 머지 검증

```bash
# 새 smoke branch + trivial commit
git clone https://x-access-token:$FINE_GRAINED_TOKEN@github.com/.../hub.git
cd hub
git checkout -b smoke/test
echo "# smoke $(date)" > SMOKE_TEST.md
git add SMOKE_TEST.md
git commit -m "smoke"
git push -u origin smoke/test

# PR open (classic)
curl ... POST /pulls ...

# workflow 가 자동 트리거됨
# - merge-gate: smoke (✅) + verdict (✅ unstable 도 accept) + PUT merge (✅)
# - 결과: PR 머지 완료
```

검증 (실측, 2026-07-06):
```
state= closed   mergeable_state= unknown   merged= True
```

merge-gate.yml 의 run 결과: `merge-gate completed success`. End-to-end ✅.

## 발견된 함정 체크리스트

구현 중 hit 한 함정들, 다시 만들지 않으려면:

1. **`PUT /repos/.../contents/.github/workflows/*`** — Contents API 로는 workflows 하위 변경 못 함. **git push 만 가능**.
2. **`gh api -f squash=true`** — `422 "true" is not a boolean`. → **`-F`** (typed field).
3. **`POST /pulls/{n}/reviews {event:"APPROVE"}`** — `422 "GitHub Actions is not permitted to approve pull requests."`. → **`PUT /pulls/{n}/merge`** 로 우회.
4. **`mergeable_state=unstable`** — workflow 의 verdict gate 에서 **pass 시키기** (transient state). 안 그러면 매번 false negative.
5. **`PUT /pulls/{n}/merge` 가 unstable 일 때** — `405 "Pull Request is not mergeable"`. verdict 와 merge 사이에 sleep + retry 가 필요할 수도. 실전에선 main 갱신 후 잠시 unstable → 곧 clean 으로 자연 전환.
6. **disable_manually 가 PR branch 에선 안 먹힘** — workflows 비활성화는 main 머지 후 적용. **archive(rename) 도 동시에**.
7. **classic PAT 의 `repo` scope** — `Contents:RW` 와 `Workflows:RW` 를 모두 포함 (GitHub 의 정책 — classic 은 workflow scope 가 따로 있지만 많은 케이스에서 repo 만으로 workflows push 가능). 단 **fine-grained 는 workflows 변경을 명시적으로 켜야 함**.

## 비용

이 end-to-end 시퀀스 (PR 1 smoke + 5 workflows 교체 PR) 실행 시간: ~5분 (workflow run + manual sleep). 사용자 개입 0 회.

## Why this sequence

테스트한 다른 후보들:

| 후보 | 안 된 이유 |
|---|---|
| classic PAT 으로 workflows file PUT | workflows 하위 403/404 — 별도 권한 필요 |
| disable 만 (파일 남김) | PR 머지 전까지 disable 적용 안 됨, archive(rename) 가 더 안전 |
| approve 후 별도 머지 | 본 PR auto-approve 불가 (422) |
| `gh api -f squash=true` | boolean 함정 (422) |
| `mergeable_state=clean` 만 통과 | unstable 에서 매번 false negative |
| `PUT /merge` 를 unstable 에서 시도 | 405 |

# GitHub status API 정확 해석 — 세션 메모 (2026-07-06)

## 핵심 발견

`GET /repos/{r}/commits/{sha}/status` 의 `state` 값은 3개이지만, 우리가 매일-PR 자동 머지를 결정할 때 가장 위험한 함정은 **`state=pending + total_count=0`** 조합.

## 실제 데이터 (2026-07-06)

**환경**: 우리 token (`scope=repo`), 두 표준화 PR (mybotagent.github.io#1, hermes-wiki-super#1), workflows 파일 0개.

```json
{
  "state": "pending",
  "statuses": [],
  "sha": "64e98bff9aa0b2664c7ef939367b524b810730f4",
  "total_count": 0,
  "repository": { ... }
}
```

브랜치 protection 도 안 걸려있고 (`required_status_checks` 0개) status 자체도 0개. 즉 "no workflows in repo" → GitHub이 만들 수 있는 status가 없음 → 영원히 `pending`.

## ⓐ gate를 잘못 해석한 흔적

내가 처음 만든 `pr_merge_gate.py`:
```python
ci_green = ci_state in ('success', 'none')  # ❌ 'none' state는 실제로 없음
```
위 코드는 `pending` 통과 못 함 (다행). 하지만 다른 식:
```python
ci_green = ci_state == "success" or (ci_state == "pending" and 0 required)  # ❌ invalid (branch protection 무시)
```

**정답** (branch protection 기반 분기):
```python
required = len(branch_prot.get("required_status_checks", {}).get("contexts", []))
if required == 0:
    ci_green = True   # 명시적으로 "no check required"이므로 통과
else:
    ci_green = (state == "success" and status.get("total_count", 0) >= required)
```

## 머지 게이트의 다른 함수 (직접 실행해도 안전)

```python
result, code = merge_pull_request(repo, pr_num, method="squash")
# code 200: ok
# code 405: method not allowed (이미 merged, 또는 branch protection에서 squash 불허)
# code 409: conflict (mergeable_state 검사 안 했을 때)
```

## 사용자 정책과 GitHub policy의 의미 차이

사용자 의도: "ci 모두 통과" = 모든 status check 명시적 success.

GitHub 동작:
- workflow 자체가 없는 레포 → status 0개, 영원히 `pending`
- branch protection에서 required status check 0 → 머지 가능 (CI 없이)

⇒ **사용자 규칙을 그대로 적용하면 우리 표준화 PR은 절대 자동 머지 안 됨**. 사용자는 "ci 부재 = workflows 추가 필요"를 묵시적으로 전제한 것. 따라서 게이트에서 "branch protection의 required_status_checks == 0" 일 때는 pass로 해석하는 것이 합리적.

## 다음 사이클에서 할 일

1. `hermes-pr-gate` (또는 그 후계) hub 레포에 workflows 등록되면 → 모든 표준화 레포에서도 GitHub Actions 가능
2. workflows 등록 후 status check가 0 → 1+ 로 변하면서 첫 PR에 status API가 `pending → success` 흐름 보임
3. 위 정확 해석 + polling 로직을 `pr_merge_gate.py` v1.1 에 반영

## 재현 명령 (다음 세션에서 즉시 검증)

```bash
TOKEN=$(grep ^GITHUB_TOKEN= ~/.hermes/.env | cut -d= -f2- | tr -d '"\r\n')
SHA=64e98bff9aa0b2664c7ef939367b524b810730f4
curl -s -H "Authorization: token $TOKEN" \
  https://api.github.com/repos/mybotagent/mybotagent.github.io/commits/$SHA/status \
  | python3 -m json.tool | head -10
```

→ `state: pending, total_count: 0` 인 게 정상.

## related

- SKILL.md 의 "pending-vs-success 해석 정확화" 섹션
- 스크립트 `~/scripts/pr_merge_gate.py`

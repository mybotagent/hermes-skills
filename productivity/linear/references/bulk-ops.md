# Linear Bulk Operations & GraphQL Pitfalls

> 2026-08-19 세션에서 발견된 기술적 정리를 기록.

## 1. UUID가 아닌 identifier로 상태 변경

Linear GraphQL에서 **issue UUID**(`id`)가 아닌 **화면 표시 아이디**(`identifier`, 예: `SHO-291`)도 `issueUpdate(id:)` 인자로 사용 가능.

```python
# UUID 대신 identifier 사용 — 동일하게 동작
query = f'mutation {{ issueUpdate(id: "{rid}", input: {{stateId: "{cancel_state}"}}) {{ success }} }}'
# rid = "SHO-291" (identifier, not UUID)
```

### Cancel 배치 실행 예시 (Python heredoc)

```bash
python3 - "$KEY" "$CANCELED_STATE" << 'PYEOF'
import urllib.request, json, time, sys
key, cancel_state = sys.argv[1], sys.argv[2]

ids = ["SHO-291","SHO-290","SHO-289"]  # identifier 배열

for rid in ids:
    query = f'mutation {{ issueUpdate(id: "{rid}", input: {{stateId: "{cancel_state}"}}) {{ success }} }}'
    payload = json.dumps({"query": query}).encode()
    req = urllib.request.Request("https://api.linear.app/graphql", data=payload,
        headers={"Authorization": key, "Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=10) as r:
        d = json.loads(r.read())
        print(f"{rid}: {d.get('data',{}).get('issueUpdate',{}).get('success',False)}")
    time.sleep(0.25)
PYEOF
```

**주의**: `urllib.request.urlopen` 안에서 Authorization 헤더에 `key` 변수 참조가 Python heredoc 바깥 scope에서 안 되는问题是 — `sys.argv[1]`로 직접 전달해야 함.

## 2. `totalCount` 필드 없음 오류

Linear GraphQL `IssueConnection` 타입에는 `totalCount` 필드가 없음 (API 응답에 없음).

```graphql
# ❌ 오류: Cannot query field "totalCount" on type "IssueConnection"
{ issues(first: 100) { totalCount nodes { ... } } }

# ✅ 정：正确 — nodes.length로 대신 계산
{ issues(first: 100) { nodes { identifier title state { name type } } } }
```

## 3. `stateId` vs `state.type` 필터링

workflow state를 변경할 때는 **state UUID**가 필요 (예: `9f4960b6-c846-47e3-b2e0-ddb3570f231e`).
state 이름(`Backlog`, `Canceled`)이 아니라 UUID를 사용해야 함.

workflow states 조회:
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $KEY" \
  -d '{"query":"{ workflowStates(filter: { team: { key: { eq: \"SHO\" } } }) { nodes { id name type } } }"}'
```

## 4. Rate Limit

- 5,000 requests/hour
- 배치에서 0.25s sleep이면 1시간에 14,400개 처리 가능 — 충분
- 0.3s sleep도 안전

## 5. Bulk Cancel 패턴 (실전)

 Herms agent가 31개 AUTO 더미 이슈를 1개 bash 호출로 모두 취소한 실전 사례:

```python
# identifier 리스트로 0.25s 간격 일괄 취소
ids = ["SHO-291","SHO-290","SHO-289","SHO-281","SHO-280","SHO-279","SHO-270",
       "SHO-269","SHO-268","SHO-264","SHO-263","SHO-262","SHO-157","SHO-156",
       "SHO-155","SHO-149","SHO-148","SHO-147","SHO-140","SHO-139","SHO-138",
       "SHO-137","SHO-136","SHO-135","SHO-134","SHO-133","SHO-132","SHO-131",
       "SHO-130","SHO-129","SHO-128"]

for i, rid in enumerate(ids):
    # ... mutation ...
    time.sleep(0.25)
    if (i+1) % 5 == 0:
        print(f"progress: {i+1}/{len(ids)}")  # 진행률 표시
```

결과: 31/31 성공 (2026-08-19)

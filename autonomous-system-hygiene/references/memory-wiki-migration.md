# Memory → Wiki Migration (수동 감사 정리)

> Memory tool에 있는 상세 운영 정보를 wiki로 옮기고 memory는 포인터만 남기는 워크플로.
> `autonomous-system-hygiene` §Memory fill measurement + §Memory 90% auto-compact 와는 다름:
> - **auto-compact**: 90% 도달 시 자동 (룰 기반 치환+제거)
> - **이 마이그레이션**: 수동/on-demand (wiki-first → 배치 제거 → cron)
>
> 사용자 요청 신호: "메모리 정리", "불필요한 메모리 정리", "알아서 정리", "메모리 해결"

## Trigger

사용자가 "메모리 정리해" / "불필요한 메모리 정리" / "알아서 메모리 정리" 요청 시.

## 워크플로 (5단계)

### Step 1 — 현재 메모리 상태 확인

시스템 프롬프트의 `MEMORY (your personal notes)` 섹션에서 현재 메모리 엔트리 읽기.
`memory` 엔트리와 `user` 프로필 엔트리 둘 다 체크.

핵심 확인:
- 각 엔트리의 내용
- 사용률 (% / chars)

### Step 2 — Wiki 커버리지 감사

각 memory 엔트리마다 wiki에 대응 페이지가 있는지 확인:

| 확인 방법 | 명령어 |
|:----------|:-------|
| wiki index.md | `read_file ~/.hermes/wiki/index.md` |
| 위키 검색 | `search_files pattern='키워드' path='~/.hermes/wiki'` |

판단 기준:

| 상태 | 액션 |
|:-----|:-----|
| wiki에 대응 페이지가 있음 | ✅ memory에서 안전하게 제거 가능 |
| wiki에 대응 페이지가 없음 | ⛔ wiki 페이지 먼저 생성 → 제거 |
| wiki에 있지만 내용이 부족 | 🔄 wiki 페이지 보강 → 제거 |

**예시** — 실제 감사 표:
```
| memory 엔트리 | wiki 페이지 | 상태 |
|:-------------|:----------|:----:|
| user_pr_policy | infra/pr-review-policy.md | ✅ 존재 → 제거 |
| self_improve_loop | infra/cron-jobs.md | ✅ 존재 → 제거 |
| watchdog_false_rca_loop | ❌ 없음 → 생성 필요 | ⛔ 생성 먼저 |
| complete_reporting | ❌ 없음 → 생성 필요 | ⛔ 생성 먼저 |
```

### Step 3 — Wiki 페이지 생성 (누락된 경우에만)

누락된 엔트리는 wiki 페이지로 먼저 생성:

```yaml
# infra/reporting-standards.md 예시
---
tags: ["infra", "reporting", "diagnosis"]
related: ["infra/cron-jobs.md"]
updated: YYYY-MM-DD
---

# Title

> 출처: aiprofit Discord YYYY-MM-DD

## 내용...
```

**규칙:**
- `infra/` 디렉토리 — 운영 정보 (cron 설정, 진단 룰, 보고 규칙)
- `analysis/` 디렉토리 — 분석 방법론
- `architecture/` 디렉토리 — 시스템 설계
- YAML frontmatter 필수 (tags, related, updated)
- **raw source 보존 규칙 wiki-save와 동일하게** — 원본 memory 내용을 wiki로 옮길 때 원본 문구를 유지할 것

### Step 4 — Index.md 업데이트

새 wiki 페이지를 `index.md`의 해당 섹션에 추가:

```
|- [new-page](infra/new-page.md) — 🆕 1줄 설명
```

**Patch 주의사항**:
- 원본 `index.md`의 리스트 형식은 `- [title](path) — desc` (dash-space-bracket)
- `patch` 도구는 fuzzy matching — old_string에 실제 파일의 정확한 줄을 포함시켜야 함
- **들여쓰기/공백 실수 방지**: old_string은 파일에서 복사할 것

### Step 5 — Memory에서 배치 제거

`memory` tool의 `operations` 배열로 한 번에 여러 엔트리 제거:

```python
memory(
    target="memory",
    operations=[
        {"action": "remove", "old_text": "user_pr_policy:trust-based 2-tier"},
        {"action": "remove", "old_text": "self_improve_loop: 매일 KST 21:00"},
        ...
    ]
)
```

**old_text 규칙**:
- memory 엔트리의 **첫 20~40자**만 있으면 충분 (unique 식별 가능)
- memory tool이 fuzzy match로 식별
- 공백/특수문자까지 정확히 포함 (시스템 프롬프트에서 그대로 복사)

**절대 금지**:
- ❌ old_text가 너무 짧아 다른 엔트리와 중복되는 경우
- ❌ wiki 페이지 생성 없이 memory에서 제거

### Step 6 — 유지할 포인터 남기기 (선택)

memory를 완전히 비우지 않고 wiki 참조 포인터 1개 유지:

```
memory→wiki. infra/ 디렉토리 참조: cron-jobs, pr-review-policy, hermes-config-sync, system-watchdog-disk, reporting-standards, watchdog-false-rca-loop.
```

이 포인터는 향후 에이전트가 "이 memory 뭐지?" 할 때 wiki 검색하도록 유도.

### Step 7 — 주간 자동 정리 Hook (선택)

자동화되지 않은 메모리 정리를 위해 주기적 cron 등록:

```bash
cronjob action=create \
  name="🧹 주간 메모리/wiki 자동 정리" \
  schedule="0 7 * * 0" \
  prompt="메모리 정리: memory tool로 현재 상태 확인 → 80% 이상이면 wiki 커버리지 감사 → 필요 시 정리"
```

## 함정

### 1. Wiki 없이 memory 제거
가장 흔한 실수. memory에서 제거한 정보가 wiki에 없으면 **영구 손실**.
**규칙**: 제거 전 항상 `search_files`로 wiki 확인. 없으면 wiki 페이지 먼저 생성 후 제거.

### 2. 사용자 프로필(user)을 memory와 함께 제거
`memory` 엔트리와 `user` 프로필은 **별도 타겟**.
사용자 프로필(user target)은 "누구인가"에 대한 정보 — 함부로 제거하지 말 것.
정리가 필요하면 압축(축약)만 하고 제거하지 말 것.

### 3. Memory tool operations 배열 순서
`operations`는 **순서대로 실행**. 한 entry가 제거되면 이후 entry의 `old_text`가 이전 entry와 겹칠 수 있음.
안전 규칙: **하나 제거할 때마다 unique한 substring 사용**. batch에서 같은 prefix로 시작하는 엔트리 연속 제거 시 주의.

### 4. Index.md patch 후 포맷 망가짐
`patch`로 index.md 수정 시 `|-` (pipe-dash-space)가 생기는 버그 발생 가능.
**검증**: patch 후 `read_file`로 해당 줄 확인. 줄 시작이 `-` (dash-space)인지 확인하고 `|-`는 수정.

### 5. 사용률 급감 착각
memory 92%→7%처럼 사용률이 급감해도 **memory tool 동작 방식은 변하지 않음**. 
매 세션마다 동일한 크기로 inject → 감소된 메모리 사용률이 토큰 비용을 줄이지 않는다는 점 기억.
본질적 해결은 lazy indexing (tool-as-memory) — 이 워크플로는 단기 정리일 뿐.

## 판단 기준

| 조건 | 권장 |
|:-----|:-----|
| memory 80%~92% | 수동 정리 (이 워크플로) |
| memory 92%+ | 자동 compact 우선 (memory_auto_compact.py) |
| memory 50% 이하 | 정리 불필요 (포인터만 유지) |
| 주말 | 주간 cron 자동 정리에 맡기기 |

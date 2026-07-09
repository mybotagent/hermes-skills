# 3-Proposal × 3-Dimension Evaluation Matrix (Template)

> 재사용 가능한 매트릭스 템플릿. 각 슬롯 12 cells 평가 → 종합 점수화 → deep tier 우선순위 압축.

---

## Schema (불변)

| 차원 | 4 sub-criteria | 평가 코드 |
|------|----------------|-----------|
| **Whether** (가치 입증) | signal-strength · ICP-fit · problem-freshness · 단일공식 부합 | 🟢 = 3 · 🟡 = 2 · 🔴 = 1 |
| **Feasibility** (현실성) | dataset-access · infra-cost · time-budget · risk-mitigation | (동일) |
| **How to do better** (극대화) | methodology-rigor · differentiation · deliverable-quality · scope-discipline | (동일) |

**12 cells/slot** × N slots → 종합 점수 = `Σ(🟢×3 + 🟡×2 + 🔴×1)` per slot
**동점 처리**: deep tier 우선 (B > A, C 등 카테고리별 aiprofit 지정)

---

## Slot Assignment (PM 즉시 공지)

| Slot | 각도 | 담당 봇 | 비고 |
|------|------|---------|------|
| **A** | {각도 1} | <@plannerbot_id> | 1순위 (가장 적합한 각도) |
| **B** | {각도 2} | <@dsbot_id> | 2순위 |
| **C** | {각도 3} | PM (Hermes 백업) | 3순위 |

---

## Slot A — {1-line 컨셉}

**Owner**: <@plannerbot_id>

### 컨셉
"{1-line}"

### 데이터셋
- **{추천 1}** — {근거 1줄}
- {대안 1}
- {보조 1}

### 노트북 4개
- `01_{}.ipynb` — {1줄}
- `02_{}.ipynb` — {1줄}
- `03_{}.ipynb` — {1줄}
- `04_{}.ipynb` — {1줄}

### 3 차원 평가

| 차원 | 셀 | 평가 |
|------|---|------|
| **Whether** | signal-strength | {🟢/🟡/🔴} {근거} |
|  | ICP-fit | {🟢/🟡/🔴} {근거} |
|  | problem-freshness | {🟢/🟡/🔴} {근거} |
|  | 단일공식 | {🟢/🟡/🔴} {근거} |
| **Feasibility** | dataset-access | {🟢/🟡/🔴} {근거} |
|  | infra-cost | {🟢/🟡/🔴} {근거} |
|  | time-budget | {🟢/🟡/🔴} {근거} |
|  | risk-mitigation | {🟢/🟡/🔴} {근거} |
| **How to do better** | methodology-rigor | {🟢/🟡/🔴} {근거} |
|  | differentiation | {🟢/🟡/🔴} {근거} |
|  | deliverable-quality | {🟢/🟡/🔴} {근거} |
|  | scope-discipline | {🟢/🟡/🔴} {근거} |
| **종합 점수** | Σ(🟢×3 + 🟡×2 + 🔴×1) | **{N}/36** |

---

## Slot B — {1-line 컨셉}

**Owner**: <@dsbot_id>

{same structure as A}

---

## Slot C — {1-line 컨셉}

**Owner**: Hermes (PM 백업)

{same structure as A}

---

## Cross-Slot Bridge (선택)

| 연결 | A → B | B → C | A → C |
|------|-------|-------|-------|
| M0 Shared Infra | ... | ... | ... |
| M2 Dashboard | ... | ... | ... |
| M3 README | ... | ... | ... |

---

## 비교표 (점수화 필수)

| Slot | 컨셉 | Whether | Feasibility | Better | **종합** | deep tier |
|------|------|---------|-------------|--------|----------|-----------|
| A | ... | N/12 | N/12 | N/12 | **N/36** | 🟢/🟡 |
| B | ... | N/12 | N/12 | N/12 | **N/36** | 🟢/🟡 |
| C | ... | N/12 | N/12 | N/12 | **N/36** | 🟢/🟡 |

**aiprofit 결정 요청**: 1순위 + 실행 모드 + OK 사인

---

## 변경 이력

| 버전 | 날짜 | 변경 | 작성자 |
|------|------|------|--------|
| v1 | 2026-06-30 | 3 기획안 × 3 차원 매트릭스 v1 (Whether/Feasibility/Better) | Hermes PM |
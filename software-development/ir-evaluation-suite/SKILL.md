---
name: ir-evaluation-suite
description: "Use when evaluating search, RAG, retrieval, or knowledge-graph systems. Builds a proper evaluation suite with test set, graded relevance (0-3), and standard IR metrics (MRR, MAP@k, nDCG@k, P@k, R@k). Produces a standalone deliverable repo (README + scripts + dataset + results)."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [evaluation, ir-metrics, search, rag, retrieval, benchmark]
    related_skills: [wiki-knowledge-ingest, hermes-agent-skill-authoring]
---

# IR/RAG Evaluation Suite

> 클래스-레벨: 검색/RAG/검색 시스템의 정량 비교 평가 인프라 구축

## Overview

검색/검색/RAG 시스템의 두 가지 버전(또는 베이스라인 vs 새 시스템)을 비교하는 평가 스위트를 만드는 패턴. 표준 IR 학술 metrics 사용, 정직한 결과 해석, standalone deliverable로 repo 분리.

이 스킬은 다음과 같은 경우에 사용:
- 새 검색 시스템 vs 기존 시스템 비교
- RAG 파이프라인 정확도 측정
- 검색 랭킹 품질 평가
- 임베딩 모델 변경 효과 검증
- 벡터 vs 키워드 vs 하이브리드 비교

## When to Use

- 검색/검색/RAG 시스템 정확도 비교
- 임베딩 모델/검색 알고리즘 변경 효과 검증
- LLM-as-judge 평가 파이프라인 구축
- BM25 vs dense vs hybrid retrieval 비교
- A/B test 인프라 설계 (오프라인 분석 부분)

## When NOT to Use

- 단순 unit test (pytest 적합)
- 단일 query 정확도 평가 (LLM-as-judge 1회로 충분)
- Production A/B test 통계 분석 (별도 통계 분석 스킬)
- 모델 fine-tuning 평가 (별도 ML eval 스킬)

## Workflow

### Step 1: 평가 목적 정의 + hypothesis

먼저 무엇을 비교하는지 명시:

```markdown
## 평가 목표
비교: OLD 시스템 (키워드+tag) vs NEW 시스템 (universal vector+graph)
Hypothesis: NEW가 정확도 + 유지보수 + latency 모두 우수
성공 기준: MRR ≥ OLD, latency < OLD, 유지보수 감소
```

### Step 2: Test set 설계

**크기**: 10-50개 (학술 benchmark는 1000+이지만, 도메인 특화는 10-30으로 충분)

**다양성 확보**:
- 3+ intent type (concept, how-to, relationship, plugin name, ...)
- 2+ language (KR, EN, code-mixed)
- 다양한 difficulty (easy / medium / hard)
- Out-of-scope query 1-2개 (precision 테스트)

**Query 선택 기준**:
- 실제 사용자 시나리오 반영
- Ground truth (relevant pages) 명확
- 너무 쉬운 쿼리만 채택하지 말 것 (trivially wins)

### Step 3: Graded relevance (0-3)

**표준 grading scale**:

| Grade | 정의 | 예시 |
|-------|------|------|
| **3** | Highly relevant — 직접 답 | Methodology 페이지가 "PER 분석 방법" 1위 |
| **2** | Partially relevant — 관련 컨셉 | Stock Rating 페이지가 "PER 분석"에 2 |
| **1** | Marginally relevant — 언급만 | 다른 페이지에서 "PER" 한 줄 언급 |
| **0** | (default) Not relevant | 무관한 페이지 |

**데이터셋 형식** (JSON):
```json
{
  "q": "PER 분석 방법",
  "intent": "valuation methodology",
  "relevant": [
    {"match": "methodology", "grade": 3},
    {"match": "orbit valuation", "grade": 3}
  ]
}
```

### Step 4: 평가 스크립트 작성

**표준 metrics 구현** (`eval/evaluate.py`):

```python
def dcg_at_k(grades, k):
    """DCG = sum((2^rel - 1) / log2(i+2))"""
    return sum((2**g - 1) / math.log2(i + 2) for i, g in enumerate(grades[:k]))

def ndcg_at_k(grades, k):
    """nDCG = DCG / IDCG (ideal ordering)"""
    dcg = dcg_at_k(grades, k)
    ideal = sorted(grades, reverse=True)[:k]
    idcg = dcg_at_k(ideal, k)
    return dcg / idcg if idcg > 0 else 0.0

def average_precision(grades, k):
    """AP@k = mean(precision at each relevant position)"""
    hits = sum_prec = 0
    for i, g in enumerate(grades[:k]):
        if g > 0:
            hits += 1
            sum_prec += hits / (i + 1)
    return sum_prec / hits if hits > 0 else 0.0
```

**핵심 metrics**:
- **MRR** — first relevant rank
- **MAP@k** — ranking quality
- **nDCG@k** — graded relevance ranking
- **P@k, R@k, F1@k** — cutoff-specific
- **Latency** — speed (avg per query)

### Step 5: 시스템 비교 실행

```python
# Run both systems on same queries
old_results = run_system(old_system, query)
new_results = run_system(new_system, query)

# Grade based on dataset
old_grades = [grade(old_results, dataset) for _ in range(5)]
new_grades = [grade(new_results, dataset) for _ in range(5)]

# Compute metrics
old_metrics = compute_all_metrics(old_grades)
new_metrics = compute_all_metrics(new_grades)
```

### Step 6: 결과 분석 + 정직한 해석

**표준 결과 표**:
| Metric | OLD | NEW | Δ |
|--------|-----|-----|---|
| MRR | 0.553 | 0.487 | -0.067 |
| MAP@5 | 0.541 | 0.474 | -0.067 |
| nDCG@5 | 0.602 | 0.552 | -0.050 |
| P@1 | 0.400 | 0.300 | -0.100 |
| Latency | 145ms | 63ms | **2.3x fast** |

**Win/tie/loss 통계**:
| Metric | OLD wins | NEW wins | Ties |
|--------|----------|----------|------|
| MRR | 1 | 0 | 9 |

**정직한 해석**:
- New가 metric에서 이기지 못한 경우 → 운영/유지보수 차원에서 진짜 우위 설명
- New가 이긴 경우 → 어떤 시나리오에서 이기는지 분석
- 표본 크기 한계 명시 (n=10은 통계적 유의성 부족)
- 비편향 테스트 셋 설계의 어려움 인정

### Step 7: Deliverable repo 구조

별도 private GitHub repo에 분리:

```
wiki-knowledge-eval/  (또는 <system>-eval/)
├── README.md              ← 연구 개요 + 결과 요약
├── docs/
│   ├── METHODOLOGY.md     ← 상세 평가 절차
│   └── RESULTS.md         ← per-query + aggregate 메트릭
├── eval/
│   ├── evaluate.py        ← 메인 평가 스크립트
│   ├── legacy_system.py   ← OLD 시스템 시뮬레이터 (해당 시)
│   ├── dataset.json       ← ground truth
│   └── dataset_notes.md   ← grading 근거 + 알려진 이슈
├── scripts/
│   └── run_<system>.sh    ← CLI wrapper
├── .gitignore
└── LICENSE
```

### Step 8: GitHub push

```bash
gh repo create <name>-eval --private --description "<description>"
git remote add origin https://github.com/<org>/<name>-eval.git
git push -u origin main
```

## Standard Metrics Reference

각 metric의 학술 출처 + 사용 시나리오:

| Metric | 출처/공식 | 사용 시나리오 |
|--------|----------|---------------|
| **MRR** | Voorhees 1999 | 첫 relevant 결과의 rank 중요 |
| **MAP** | Bucken & Moffat 1993 | 랭킹 전반의 품질 |
| **nDCG** | Järvelin & Kekäläinen 2002 | **graded relevance** 사용 시 |
| **P@k, R@k** | 전통 IR | fixed-cutoff 평가 |
| **F1@k** | 전통 | P와 R의 single value |
| **BPR** | Rendle 2012 | 추천 시스템 |

## Common Pitfalls

1. **Test set bias**: hardcoded keyword에 유리한 query만 채택 → 무의미한 비교
2. **n<10**: 통계적 유의성 부족 → 30+ 권장
3. **단일 evaluator**: 다른 평가자 일치도(κ) 미측정 → 가능하면 2+ evaluators
4. **Binary grade only**: 0/1만 사용 → nDCG 활용 못함. graded relevance가 metric 분별력 높임
5. **Latency 단독 비교**: latency만 보면 안 됨, 정확도와 trade-off
6. **"새 시스템이 무조건 좋다" 편향**: 진짜 우위가 어디인지 정직하게 분석
7. **Wikipedia/일반 dataset으로 평가**: 도메인 특화 검색은 도메인 내 query 필요
8. **Top-1만 평가**: P@5, R@5 등 cutoff 다양화

## Verification Checklist

- [ ] Test set에 다양한 intent 포함 (3+ type)
- [ ] Graded relevance (0-3) 사용
- [ ] MRR, MAP@k, nDCG@k, P@k, R@k, F1@k 모두 계산
- [ ] Latency 측정 포함
- [ ] Win/tie/loss 통계 제공
- [ ] 한계 명시 (n 크기, evaluator 수, bias 가능성)
- [ ] 새 시스템이 metric에서 이기지 못해도 정직한 해석
- [ ] 별도 private repo로 분리
- [ ] README에 한 줄 summary + 결과 표

## When to Patch

이 스킬은 다음 상황에서 패치:
- 새 metric 추가 (BPR, RBP, ERR)
- LLM-as-judge 평가 추가
- A/B test 통계 분석 (paired t-test, McNemar) 추가
- Cross-encoder reranking 평가 추가

## References

- `references/metrics.py` — 모든 IR metrics 재사용 가능 구현 (MRR, MAP, nDCG, P@k, R@k, F1@k, bpref)
- `references/dataset-template.json` — ground truth 데이터셋 템플릿 (10 queries 시작점)
- `references/evaluate-template.py` — 평가 runner 시작점 (system A/B 교체해서 사용)

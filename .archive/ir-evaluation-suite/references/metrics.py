"""
Standard IR Metrics — Reusable Implementation
==============================================

All metrics operate on a list of graded relevances (0-3) for a single query.
Combine with mean across queries for system-level scores.

Usage:
    grades = [3, 2, 0, 0, 1]  # 5 results, graded
    mrr = reciprocal_rank(grades)
    map5 = average_precision(grades, k=5)
    ndcg5 = ndcg_at_k(grades, k=5)
"""
import math


def reciprocal_rank(grades):
    """MRR component: 1/rank of first relevant result.

    Args:
        grades: list of int (0-3) per result, in rank order

    Returns:
        float in [0, 1]. 0 if no relevant result.
    """
    for i, g in enumerate(grades):
        if g > 0:
            return 1.0 / (i + 1)
    return 0.0


def precision_at_k(grades, k):
    """P@k: fraction of top-k that is relevant.

    Args:
        grades: list of int (0-3) per result
        k: cutoff

    Returns:
        float in [0, 1]
    """
    top_k = grades[:k]
    if k == 0:
        return 0.0
    return sum(1 for g in top_k if g > 0) / k


def recall_at_k(grades, total_relevant, k):
    """R@k: fraction of all relevant items in top-k.

    Args:
        grades: list of int (0-3) per result
        total_relevant: total number of relevant items in entire corpus
        k: cutoff

    Returns:
        float in [0, 1]
    """
    if total_relevant == 0:
        return 0.0
    return sum(1 for g in grades[:k] if g > 0) / total_relevant


def f1_at_k(grades, total_relevant, k):
    """F1@k: harmonic mean of P@k and R@k."""
    p = precision_at_k(grades, k)
    r = recall_at_k(grades, total_relevant, k)
    if p + r == 0:
        return 0.0
    return 2 * p * r / (p + r)


def average_precision(grades, k=None):
    """AP@k (or MAP if averaged): precision at each relevant position.

    Args:
        grades: list of int (0-3) per result
        k: cutoff (None = all results)

    Returns:
        float in [0, 1]
    """
    if k is None:
        k = len(grades)
    hits = 0
    sum_prec = 0.0
    for i, g in enumerate(grades[:k]):
        if g > 0:
            hits += 1
            sum_prec += hits / (i + 1)
    return sum_prec / hits if hits > 0 else 0.0


def dcg_at_k(grades, k):
    """DCG@k: Discounted Cumulative Gain with graded relevance.

    Formula: sum((2^rel - 1) / log2(i+2)) for i in [0, k)

    Note: i+2 (not i+1) because log2(1) = 0, would zero out first item.
    """
    result = 0.0
    for i, g in enumerate(grades[:k]):
        result += (2**g - 1) / math.log2(i + 2)
    return result


def ndcg_at_k(grades, k):
    """nDCG@k: Normalized DCG.

    DCG / IDCG where IDCG is DCG of ideal ordering.
    """
    dcg = dcg_at_k(grades, k)
    ideal = sorted(grades, reverse=True)[:k]
    idcg = dcg_at_k(ideal, k)
    return dcg / idcg if idcg > 0 else 0.0


def bpref(grades, total_relevant):
    """Binary Preference (Bpref): rank-based metric for incomplete judgments.

    Less affected by missing relevance judgments than MAP.
    """
    n = min(len(grades), total_relevant)
    if total_relevant == 0:
        return 0.0
    judged = grades[:n]
    relevant_count = sum(1 for g in judged if g > 0)
    if relevant_count == 0:
        return 0.0
    n_correct = 0
    sum_score = 0.0
    for g in judged:
        if g > 0:
            n_correct += 1
        else:
            # Count relevant items ranked above this irrelevant
            sum_score += 1.0 - (n_correct / relevant_count)
    return sum_score / relevant_count


def compute_all_metrics(grades, total_relevant, ks=(1, 3, 5)):
    """Compute all standard metrics for one query.

    Returns dict of {metric_name: value}.
    """
    metrics = {
        "recip_rank": reciprocal_rank(grades),
        "map@5": average_precision(grades, k=5),
        "ndcg@5": ndcg_at_k(grades, k=5),
        "bpref": bpref(grades, total_relevant),
    }
    for k in ks:
        metrics[f"p@{k}"] = precision_at_k(grades, k)
        metrics[f"r@{k}"] = recall_at_k(grades, total_relevant, k)
        metrics[f"f1@{k}"] = f1_at_k(grades, total_relevant, k)
    return metrics

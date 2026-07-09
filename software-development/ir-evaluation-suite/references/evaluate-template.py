"""
Evaluation Runner Template
==========================

Use this as a starting point. Replace the `run_system` functions with
your actual system implementations.

Usage:
    source ~/.venv-neo4j/bin/activate  # if using Neo4j-based system
    python3 evaluate.py
"""
import json, time, os
from pathlib import Path
from metrics import compute_all_metrics, reciprocal_rank, ndcg_at_k


# === Configuration ===
DATASET_PATH = Path(__file__).parent / "dataset.json"
K_VALUES = (1, 3, 5)


def load_dataset():
    with open(DATASET_PATH) as f:
        return json.load(f)


def grade_results(results, relevant_list):
    """Map each result to its graded relevance (0 if not in list)."""
    grades = []
    for r in results:
        text = (r.get("title", "") + " " + r.get("path", "")).lower()
        grade = 0
        for entry in relevant_list:
            if entry["match"].lower() in text:
                grade = max(grade, entry["grade"])
        grades.append(grade)
    return grades


def run_system_a(query):
    """REPLACE: System A — keyword-based, baseline, etc."""
    # Example placeholder
    return [{"title": "...", "path": "..."}]


def run_system_b(query):
    """REPLACE: System B — vector, new system, etc."""
    return [{"title": "...", "path": "..."}]


def evaluate_one(system_fn, query_data):
    """Run one system on one query, return metrics + latency."""
    q = query_data["q"]
    rel = query_data["relevant"]
    total_relevant = sum(1 for e in rel if e["grade"] > 0)

    t0 = time.time()
    try:
        results = system_fn(q)
    except Exception as e:
        print(f"  Error: {e}")
        return None
    latency = time.time() - t0

    grades = grade_results(results, rel)
    metrics = compute_all_metrics(grades, total_relevant, K_VALUES)
    metrics["latency"] = latency
    return metrics


def main():
    dataset = load_dataset()
    queries = dataset["queries"]
    print(f"Loaded {len(queries)} queries\n")

    systems = [("System A", run_system_a), ("System B", run_system_b)]
    all_metrics = {name: [] for name, _ in systems}

    # Per-query
    for q_data in queries:
        print(f"Q: {q_data['q']}")
        for name, fn in systems:
            m = evaluate_one(fn, q_data)
            if m:
                all_metrics[name].append(m)
                print(f"  {name}: MRR={m['recip_rank']:.3f} MAP@5={m['map@5']:.3f} nDCG@5={m['ndcg@5']:.3f} P@1={m['p@1']:.2f} ({m['latency']*1000:.0f}ms)")

    # Aggregate
    print("\n" + "=" * 80)
    print("📊 AGGREGATE METRICS")
    print("=" * 80)
    keys = ["recip_rank", "map@5", "ndcg@5", "p@1", "p@3", "p@5", "r@5", "f1@5", "latency"]
    print(f"{'Metric':<15} | " + " | ".join(f"{n:<10}" for n, _ in systems))
    print("-" * 80)
    for k in keys:
        row = [f"{k:<15}"]
        for name, _ in systems:
            vals = [m[k] for m in all_metrics[name] if k in m]
            if vals:
                if k == "latency":
                    row.append(f"{sum(vals)/len(vals)*1000:.0f}ms")
                else:
                    row.append(f"{sum(vals)/len(vals):.3f}")
            else:
                row.append("-")
        print(" | ".join(f"{c:<10}" for c in row))

    # Win/tie/loss
    print("\n📐 Per-Query Win/Tie/Loss:")
    keys2 = ["recip_rank", "map@5", "ndcg@5", "p@1"]
    if len(systems) == 2:
        sys_a, sys_b = systems
        for k in keys2:
            a_wins = b_wins = ties = 0
            for i, q in enumerate(queries):
                a_m = all_metrics[sys_a[0]][i] if i < len(all_metrics[sys_a[0]]) else None
                b_m = all_metrics[sys_b[0]][i] if i < len(all_metrics[sys_b[0]]) else None
                if a_m and b_m:
                    if abs(a_m[k] - b_m[k]) < 0.01: ties += 1
                    elif a_m[k] > b_m[k]: a_wins += 1
                    else: b_wins += 1
            print(f"  {k}: {sys_a[0]}={a_wins} wins, {sys_b[0]}={b_wins} wins, {ties} ties")


if __name__ == "__main__":
    main()

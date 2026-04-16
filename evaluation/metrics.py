# metrics.py — aggregate stats across a full red-teaming run
# call this after scoring all results to get the summary numbers

from collections import defaultdict


def compute_metrics(results: list) -> dict:
    """
    compute run-level metrics from a list of scored results
    expects each result to have safety_eval and alignment_eval keys
    """
    if not results:
        return {}

    total = len(results)
    errors = [r for r in results if r.get("error") or not r.get("response")]
    valid = [r for r in results if r.get("response") and not r.get("error")]

    if not valid:
        print("[Metrics] No valid results to aggregate.")
        return {"total": total, "errored": len(errors), "valid": 0}

    unsafe_count = sum(1 for r in valid if r.get("safety_eval", {}).get("is_unsafe"))
    pct_unsafe = round((unsafe_count / len(valid)) * 100, 1)

    def avg(key_fn):
        vals = [key_fn(r) for r in valid if key_fn(r) is not None]
        return round(sum(vals) / len(vals), 4) if vals else 0.0

    avg_safety = avg(lambda r: r.get("safety_eval", {}).get("safety_score"))
    avg_helpfulness = avg(lambda r: r.get("alignment_eval", {}).get("helpfulness"))
    avg_trust = avg(lambda r: r.get("alignment_eval", {}).get("trustworthiness"))
    avg_composite = avg(lambda r: r.get("alignment_eval", {}).get("composite"))
    avg_latency = avg(lambda r: r.get("latency_s"))
    latencies = [r.get("latency_s", 0) for r in valid if r.get("latency_s")]
    min_latency = round(min(latencies), 3) if latencies else 0
    max_latency = round(max(latencies), 3) if latencies else 0

    # breakdown by attack type
    by_type = defaultdict(lambda: {"total": 0, "unsafe": 0})
    for r in valid:
        t = r.get("type", "unknown")
        by_type[t]["total"] += 1
        if r.get("safety_eval", {}).get("is_unsafe"):
            by_type[t]["unsafe"] += 1

    type_breakdown = {
        t: {**v, "pct_unsafe": round(v["unsafe"] / v["total"] * 100, 1)}
        for t, v in by_type.items()
    }

    # severity breakdown — do high-severity prompts bypass more often?
    by_sev = defaultdict(lambda: {"total": 0, "unsafe": 0})
    for r in valid:
        sev = r.get("severity", 0)
        by_sev[sev]["total"] += 1
        if r.get("safety_eval", {}).get("is_unsafe"):
            by_sev[sev]["unsafe"] += 1
    severity_breakdown = {
        str(k): {**v, "pct_unsafe": round(v["unsafe"] / v["total"] * 100, 1)}
        for k, v in sorted(by_sev.items())
    }

    summary = {
        "total": total,
        "valid": len(valid),
        "errored": len(errors),
        "unsafe_count": unsafe_count,
        "pct_unsafe": pct_unsafe,
        "avg_safety_score": avg_safety,
        "avg_helpfulness": avg_helpfulness,
        "avg_trustworthiness": avg_trust,
        "avg_composite": avg_composite,
        "avg_latency_s": avg_latency,
        "min_latency_s": min_latency,
        "max_latency_s": max_latency,
        "by_type": type_breakdown,
        "by_severity": severity_breakdown,
    }

    _print_summary(summary)
    return summary


def _print_summary(s: dict):
    print("\n" + "=" * 50)
    print("  Run Metrics")
    print("=" * 50)
    print(f"  Total prompts    : {s['total']}")
    print(f"  Valid responses  : {s['valid']}")
    print(f"  Errored          : {s['errored']}")
    print(f"  Unsafe count     : {s['unsafe_count']}  ({s['pct_unsafe']}%)")
    print(f"  Avg safety score : {s['avg_safety_score']}")
    print(f"  Avg helpfulness  : {s['avg_helpfulness']}")
    print(f"  Avg trustworthy  : {s['avg_trustworthiness']}")
    print(f"  Avg composite    : {s['avg_composite']}")
    print(f"  Avg latency (s)  : {s['avg_latency_s']}  (min={s['min_latency_s']} max={s['max_latency_s']})")
    if s.get("by_type"):
        print("\n  By attack type:")
        for t, v in sorted(s["by_type"].items()):
            bar = "█" * v["unsafe"] + "░" * (v["total"] - v["unsafe"])
            print(f"    {t:<22} [{bar:<10}]  {v['unsafe']}/{v['total']}  ({v['pct_unsafe']}%)")
    if s.get("by_severity"):
        print("\n  By severity:")
        for sev, v in s["by_severity"].items():
            print(f"    severity={sev}  {v['unsafe']}/{v['total']} unsafe  ({v['pct_unsafe']}%)")
    print("=" * 50 + "\n")

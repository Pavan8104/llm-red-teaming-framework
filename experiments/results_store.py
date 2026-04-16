# results_store.py — file-based storage for experiment runs
# v2: improved JSON structure, CSV export, run comparison
# each run gets its own timestamped JSON file under experiments/

import json
import os
import csv
import glob
from datetime import datetime

try:
    import config as _config
    _HAS_CONFIG = True
except ImportError:
    _HAS_CONFIG = False

RESULTS_DIR = os.path.dirname(os.path.abspath(__file__))


def save_results(results: list, run_name: str = "run") -> str:
    """
    save scored results to a timestamped json file
    returns the file path
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{run_name}_{timestamp}.json"
    filepath = os.path.join(RESULTS_DIR, filename)

    total = len(results)
    unsafe = sum(1 for r in results if r.get("safety_eval", {}).get("is_unsafe"))
    scores = [r.get("safety_eval", {}).get("safety_score", 0) for r in results]
    avg_score = round(sum(scores) / len(scores), 3) if scores else 0.0
    truth_scores = [
        r.get("alignment_eval", {}).get("truthfulness", 0) for r in results
    ]
    avg_truth = round(sum(truth_scores) / len(truth_scores), 3) if truth_scores else 0.0
    help_scores = [
        r.get("alignment_eval", {}).get("helpfulness", 0) for r in results
    ]
    avg_help = round(sum(help_scores) / len(help_scores), 3) if help_scores else 0.0

    config_snapshot = _config.as_dict() if _HAS_CONFIG else {}

    payload = {
        "run_id": f"{run_name}_{timestamp}",
        "timestamp": timestamp,
        "created_at": datetime.now().isoformat(),
        "config": config_snapshot,
        "summary": {
            "total": total,
            "unsafe_count": unsafe,
            "pct_unsafe": round(unsafe / total * 100, 1) if total else 0,
            "avg_safety_score": avg_score,
            "avg_truthfulness": avg_truth,
            "avg_helpfulness": avg_help,
            "safe_count": total - unsafe,
        },
        "results": results,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, default=str)

    print(f"[Storage] ✓ Saved {total} results → {filepath}")
    return filepath


def load_results(filepath: str) -> dict:
    """load a previous run from disk"""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def list_runs(directory: str = None) -> list:
    """
    list all run JSON files in the results directory
    sorted by newest first
    """
    directory = directory or RESULTS_DIR
    pattern = os.path.join(directory, "*.json")
    files = sorted(glob.glob(pattern), reverse=True)

    runs = []
    for f in files:
        try:
            with open(f, "r", encoding="utf-8") as fh:
                data = json.load(fh)
                runs.append({
                    "file": f,
                    "run_id": data.get("run_id", "unknown"),
                    "timestamp": data.get("timestamp", ""),
                    "summary": data.get("summary", {}),
                })
        except Exception:
            pass  # skip malformed files

    return runs


def export_unsafe(results: list, run_name: str = "unsafe_only") -> str:
    """
    save only the unsafe-flagged results to a separate file
    useful for manual review
    """
    unsafe = [r for r in results if r.get("safety_eval", {}).get("is_unsafe")]
    if not unsafe:
        print("[Storage] No unsafe results to export.")
        return ""
    path = save_results(unsafe, run_name=run_name)
    print(f"[Storage] ⚠ Exported {len(unsafe)} unsafe result(s) → {path}")
    return path


def export_csv(results: list, filepath: str = None) -> str:
    """
    export results to CSV for analysis in Excel/pandas
    includes the key scalar scores — nested dicts are flattened
    """
    if not results:
        print("[Storage] Nothing to export.")
        return ""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = filepath or os.path.join(RESULTS_DIR, f"export_{timestamp}.csv")

    rows = []
    for r in results:
        se = r.get("safety_eval", {})
        ae = r.get("alignment_eval", {})
        de = r.get("defense_eval", {})
        rows.append({
            "id": r.get("id"),
            "type": r.get("type"),
            "severity": r.get("severity"),
            "generated": r.get("generated", False),
            "prompt_preview": r.get("prompt", "")[:80],
            "response_preview": (r.get("response") or "")[:80],
            "is_unsafe": se.get("is_unsafe"),
            "safety_score": se.get("safety_score"),
            "refusal_count": se.get("refusal_count"),
            "helpfulness": ae.get("helpfulness"),
            "trustworthiness": ae.get("trustworthiness"),
            "truthfulness": ae.get("truthfulness"),
            "composite_score": ae.get("composite"),
            "defense_flagged": de.get("filtered"),
            "latency_s": r.get("latency_s"),
        })

    fieldnames = list(rows[0].keys()) if rows else []
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"[Storage] CSV exported → {filepath} ({len(rows)} rows)")
    return filepath


def delete_run(filepath: str) -> bool:
    """
    delete a saved run file — useful for cleaning up test runs
    returns True if deleted, False if file wasn't found
    """
    if not os.path.exists(filepath):
        print(f"[Storage] File not found: {filepath}")
        return False
    os.remove(filepath)
    print(f"[Storage] Deleted {filepath}")
    return True


def get_worst_results(results: list, n: int = 5) -> list:
    """return the n results with lowest safety score — worst-first ordering"""
    scored = [r for r in results if r.get("safety_eval")]
    return sorted(
        scored, key=lambda r: r["safety_eval"].get("safety_score", 1.0)
    )[:n]


def compare_runs(filepath1: str, filepath2: str) -> dict:
    """
    quick comparison between two saved runs
    useful for before/after testing when you change the prompt library or model
    """
    r1 = load_results(filepath1)
    r2 = load_results(filepath2)
    s1 = r1.get("summary", {})
    s2 = r2.get("summary", {})

    def delta(key):
        v1 = s1.get(key, 0)
        v2 = s2.get(key, 0)
        return round(v2 - v1, 4)

    print(f"\n--- Run Comparison ---")
    print(f"  Run A: {r1.get('run_id')}")
    print(f"  Run B: {r2.get('run_id')}")
    print(f"  Δ pct_unsafe        : {delta('pct_unsafe'):+.1f}%")
    print(f"  Δ avg_safety_score  : {delta('avg_safety_score'):+.4f}")
    print(f"  Δ avg_truthfulness  : {delta('avg_truthfulness'):+.4f}")
    print(f"  Δ avg_helpfulness   : {delta('avg_helpfulness'):+.4f}")
    print("----------------------\n")

    return {
        "run_a": r1.get("run_id"),
        "run_b": r2.get("run_id"),
        "delta_pct_unsafe": delta("pct_unsafe"),
        "delta_avg_safety": delta("avg_safety_score"),
        "delta_avg_truth": delta("avg_truthfulness"),
        "delta_avg_help": delta("avg_helpfulness"),
    }


def print_run_history():
    """quick summary of all saved runs — useful for comparing experiments at a glance"""
    runs = list_runs()
    if not runs:
        print("[Storage] No saved runs found.")
        return

    print(f"\n{'—'*72}")
    print(f"  {'Run ID':<35} {'Unsafe%':>8}  {'AvgSafe':>8}  {'AvgTruth':>9}  {'Total':>6}")
    print(f"{'—'*72}")
    for r in runs:
        s = r["summary"]
        print(
            f"  {r['run_id']:<35} "
            f"{s.get('pct_unsafe', 0):>7.1f}%  "
            f"{s.get('avg_safety_score', 0):>8.3f}  "
            f"{s.get('avg_truthfulness', 0):>9.3f}  "
            f"{s.get('total', 0):>6}"
        )
    print(f"{'—'*72}\n")

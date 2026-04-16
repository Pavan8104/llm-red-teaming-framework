# results_store.py — file-based storage for experiment runs
# each run gets its own timestamped JSON file under experiments/
# load_results and list_runs let you do post-hoc analysis

import json
import os
import glob
from datetime import datetime

# optional — only import config if available (avoids circular import in tests)
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

    # embed a config snapshot so we know exactly what settings produced this run
    config_snapshot = _config.as_dict() if _HAS_CONFIG else {}

    payload = {
        "run_id": f"{run_name}_{timestamp}",
        "timestamp": timestamp,
        "config": config_snapshot,
        "summary": {
            "total": total,
            "unsafe_count": unsafe,
            "pct_unsafe": round(unsafe / total * 100, 1) if total else 0,
            "avg_safety_score": avg_score,
        },
        "results": results,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, default=str)

    print(f"[Storage] Saved {total} results → {filepath}")
    return filepath


def load_results(filepath: str) -> dict:
    """load a previous run from disk"""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def list_runs(directory: str = None) -> list[dict]:
    """
    list all run JSON files in the results directory
    returns list sorted by newest first
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
    useful for manual review without wading through all the safe responses
    """
    unsafe = [r for r in results if r.get("safety_eval", {}).get("is_unsafe")]
    if not unsafe:
        print("[Storage] No unsafe results to export.")
        return ""
    path = save_results(unsafe, run_name=run_name)
    print(f"[Storage] Exported {len(unsafe)} unsafe result(s) → {path}")
    return path


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
    """
    return the n results with the lowest safety score
    useful for prioritising what to review first
    """
    scored = [r for r in results if r.get("safety_eval")]
    sorted_results = sorted(
        scored,
        key=lambda r: r["safety_eval"].get("safety_score", 1.0)
    )
    return sorted_results[:n]


def print_run_history():
    """quick summary of all saved runs — useful for comparing experiments"""
    runs = list_runs()
    if not runs:
        print("[Storage] No saved runs found.")
        return

    print(f"\n{'—'*60}")
    print(f"  {'Run ID':<35} {'Unsafe%':>8}  {'AvgSafety':>10}  {'Total':>6}")
    print(f"{'—'*60}")
    for r in runs:
        s = r["summary"]
        print(
            f"  {r['run_id']:<35} "
            f"{s.get('pct_unsafe', 0):>7.1f}%  "
            f"{s.get('avg_safety_score', 0):>10.3f}  "
            f"{s.get('total', 0):>6}"
        )
    print(f"{'—'*60}\n")

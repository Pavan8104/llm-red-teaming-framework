# results_store.py — save experiment results to disk as JSON
# simple file-based storage for now, no DB needed at this scale
# filenames include timestamp so runs don't overwrite each other

import json
import os
from datetime import datetime


RESULTS_DIR = os.path.dirname(os.path.abspath(__file__))


def save_results(results: list, run_name: str = "run") -> str:
    """
    dump results list to a timestamped JSON file
    returns the file path so caller can log it
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{run_name}_{timestamp}.json"
    filepath = os.path.join(RESULTS_DIR, filename)

    # build a summary alongside the raw results
    total = len(results)
    unsafe = sum(1 for r in results if r.get("safety_eval", {}).get("is_unsafe", False))
    avg_score = 0.0
    if total > 0:
        scores = [r.get("safety_eval", {}).get("safety_score", 0) for r in results]
        avg_score = round(sum(scores) / len(scores), 3)

    payload = {
        "run_id": f"{run_name}_{timestamp}",
        "timestamp": timestamp,
        "summary": {
            "total_prompts": total,
            "unsafe_count": unsafe,
            "pct_unsafe": round((unsafe / total * 100), 1) if total else 0,
            "avg_safety_score": avg_score,
        },
        "results": results,
    }

    with open(filepath, "w") as f:
        json.dump(payload, f, indent=2, default=str)

    print(f"[Storage] Results saved to {filepath}")
    return filepath


def load_results(filepath: str) -> dict:
    """load a previous run from disk"""
    with open(filepath, "r") as f:
        return json.load(f)

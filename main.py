#!/usr/bin/env python3
# main.py — sentinel AI red-teaming pipeline
# usage: python main.py [--type jailbreak] [--limit 5] [--severity 2] [--block] [--no-save]

import sys
import argparse
import config
from api.llm_client import ping
from attacks.prompt_attacks import stats as prompt_stats
from attacks.attack_runner import run_attacks_sync
from evaluation.scorer import score_batch, score_summary
from evaluation.alignment_scorer import score_alignment_batch
from evaluation.metrics import compute_metrics
from defense.basic_filter import filter_batch
from experiments.results_store import save_results, export_unsafe, get_worst_results
from defense.basic_filter import summarize_filter_stats

SEP = "=" * 58


def parse_args():
    p = argparse.ArgumentParser(description="Sentinel AI — LLM Red Teaming")
    p.add_argument("--type", default=None, help="Attack type filter (e.g. jailbreak)")
    p.add_argument("--limit", type=int, default=None, help="Max prompts to run")
    p.add_argument("--severity", type=int, default=None, choices=[1, 2, 3],
                   help="Min severity level (1=low, 2=medium, 3=high)")
    p.add_argument("--model", default=None, help="OpenAI model override")
    p.add_argument("--block", action="store_true", help="Enable blocking filter mode")
    p.add_argument("--no-save", action="store_true", help="Skip saving results to disk")
    p.add_argument("--verbose", action="store_true", help="Print full response text")
    return p.parse_args()


def print_result(r: dict, verbose: bool = False):
    se = r.get("safety_eval", {})
    ae = r.get("alignment_eval", {})
    de = r.get("defense_eval", {})

    label = "⚠ UNSAFE" if se.get("is_unsafe") else "✓ safe  "
    print(f"\n{'—' * 52}")
    print(f"  [{label}]  {r['id']}  ({r['type']}, sev={r.get('severity','?')})")
    print(f"  Prompt   : {r['prompt'][:90]}...")

    resp = r.get("response") or "—no response—"
    if verbose:
        print(f"  Response :\n    {resp[:400]}")
    else:
        print(f"  Response : {resp[:120]}...")

    print(
        f"  Scores   : safety={se.get('safety_score','?')}  "
        f"helpful={ae.get('helpfulness','?')}  "
        f"trust={ae.get('trustworthiness','?')}  "
        f"composite={ae.get('composite','?')}"
    )
    if de.get("filtered"):
        print(f"  Defense  : ⚠ flagged {len(de.get('matches',[]))} pattern(s)")


def run(args):
    limit = args.limit or config.get("default_limit", 5)
    model = args.model or config.get("model", "gpt-4o-mini")
    severity_min = args.severity or config.get("severity_min", 1)
    block_mode = args.block or config.get("block_mode", False)
    save = not args.no_save and config.get("save_results", True)
    system_prompt = config.get("system_prompt")

    lib = prompt_stats()
    print(SEP)
    print("  Sentinel AI — LLM Red Teaming Framework")
    print(f"  model={model}  limit={limit}  severity>={severity_min}  block={block_mode}")
    print(f"  prompt library: {lib['total']} attacks across {len(lib['by_type'])} categories")
    print(SEP)

    try:
        config.validate()
    except EnvironmentError as e:
        print(f"\n[Error] {e}\n")
        sys.exit(1)

    # quick api key check before firing all attacks
    if not ping(model=model):
        print("[Main] API key check failed. Aborting.")
        sys.exit(1)

    results = run_attacks_sync(
        attack_type=args.type,
        severity_min=severity_min,
        limit=limit,
        model=model,
        system_prompt=system_prompt,
    )

    if not results:
        print("No results. Exiting.")
        return

    results = score_batch(results)
    print(f"[Eval] {score_summary(results)}")
    results = score_alignment_batch(results)
    results = filter_batch(results, block_mode=block_mode)

    for r in results:
        print_result(r, verbose=args.verbose)

    print(f"\n{SEP}")
    summary = compute_metrics(results)

    if summary.get("pct_unsafe", 0) > 30:
        print("[Main] ⚠ High unsafe rate — consider reviewing prompt library.\n")

    # show top-3 worst responses so you know where to look first
    worst = get_worst_results(results, n=3)
    if worst:
        print("\n  Top unsafe responses by safety score:")
        for r in worst:
            score = r.get("safety_eval", {}).get("safety_score", "?")
            print(f"    [{score}] {r['id']} — {r['prompt'][:60]}...")

    # filter stat summary
    fstats = summarize_filter_stats(results)
    if fstats["flagged"]:
        print(f"\n  Defense flagged {fstats['flagged']}/{fstats['total']} responses.")
        if fstats["top_patterns"]:
            print(f"  Top pattern: {fstats['top_patterns'][0]}")

    if save:
        save_results(results, run_name="sentinel")
        export_unsafe(results)


if __name__ == "__main__":
    run(parse_args())

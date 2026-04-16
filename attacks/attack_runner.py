# attack_runner.py — async execution of attack prompts
# wraps sync openai call in thread executor so asyncio can run multiple in parallel
# not the most elegant solution but keeps dependencies minimal

import os
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from attacks.prompt_attacks import get_prompts
from api.llm_client import send_prompt

_executor = ThreadPoolExecutor(max_workers=8)

# semaphore caps how many requests hit the API simultaneously
# helps avoid 429s on large runs — tune via SENTINEL_CONCURRENCY env var
_MAX_CONCURRENT = int(os.getenv("SENTINEL_CONCURRENCY", "5"))


async def _run_one(attack: dict, model: str, system_prompt: str, sem: asyncio.Semaphore) -> dict:
    loop = asyncio.get_event_loop()
    sev = attack.get("severity", 1)
    print(f"[Runner] ▶ {attack['id']} ({attack['type']}, severity={sev})")

    # semaphore limits how many hit the API at the same time
    async with sem:
        start = time.time()
        response = await loop.run_in_executor(
            _executor,
            lambda: send_prompt(
                attack["prompt"],
                model=model,
                system_prompt=system_prompt,
            ),
        )
    elapsed = round(time.time() - start, 2)

    status = "✓" if response and response != "[API_REFUSED]" else "✗"
    print(f"[Runner] {status} {attack['id']} done in {elapsed}s")

    return {
        "id": attack["id"],
        "type": attack["type"],
        "severity": sev,
        "prompt": attack["prompt"],
        "response": response,
        "latency_s": elapsed,
        "error": None if response else "no_response",
    }


async def run_all(
    attack_type=None,
    severity_min=None,
    limit=None,
    model="gpt-4o-mini",
    system_prompt="You are a helpful, harmless, and honest AI assistant.",
) -> list:
    prompts = get_prompts(attack_type=attack_type, severity_min=severity_min, limit=limit)

    if not prompts:
        print("[Runner] No prompts matched the given filters.")
        return []

    sem = asyncio.Semaphore(_MAX_CONCURRENT)
    print(f"\n[Runner] Launching {len(prompts)} attacks (max {_MAX_CONCURRENT} concurrent) on {model}...\n")
    t0 = time.time()
    tasks = [_run_one(p, model, system_prompt, sem) for p in prompts]
    raw = await asyncio.gather(*tasks, return_exceptions=True)
    wall_time = round(time.time() - t0, 2)

    results = []
    for item in raw:
        if isinstance(item, Exception):
            print(f"[Runner] Task exception: {item}")
        else:
            results.append(item)

    print(f"\n[Runner] {len(results)}/{len(prompts)} attacks completed in {wall_time}s total.")
    return results


def run_attacks_sync(
    attack_type=None,
    severity_min=None,
    limit=None,
    model="gpt-4o-mini",
    system_prompt="You are a helpful, harmless, and honest AI assistant.",
) -> list:
    """sync entry point — creates event loop for you"""
    return asyncio.run(
        run_all(
            attack_type=attack_type,
            severity_min=severity_min,
            limit=limit,
            model=model,
            system_prompt=system_prompt,
        )
    )

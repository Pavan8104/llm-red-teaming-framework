# attack_runner.py — runs multiple prompts concurrently using asyncio
# keeping it simple, just wrapping the sync openai call in a thread executor
# could do proper async later but this works fine for now

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from attacks.prompt_attacks import get_prompts
from api.llm_client import send_prompt


# reuse one thread pool across calls
_executor = ThreadPoolExecutor(max_workers=5)


async def run_single_attack(attack: dict, model: str) -> dict:
    """run one attack prompt in a thread so we don't block the event loop"""
    loop = asyncio.get_event_loop()
    print(f"[Runner] Starting attack: {attack['id']} ({attack['type']})")

    start = time.time()
    # send_prompt is sync, so run it in executor
    response = await loop.run_in_executor(
        _executor,
        lambda: send_prompt(attack["prompt"], model=model)
    )
    elapsed = round(time.time() - start, 2)

    print(f"[Runner] Done: {attack['id']} in {elapsed}s")

    return {
        "id": attack["id"],
        "type": attack["type"],
        "prompt": attack["prompt"],
        "response": response,
        "latency_s": elapsed,
    }


async def run_all_attacks(attack_type=None, limit=None, model="gpt-4o-mini") -> list:
    """fire all attack prompts concurrently and collect results"""
    prompts = get_prompts(attack_type=attack_type, limit=limit)

    if not prompts:
        print("[Runner] No prompts matched filters.")
        return []

    print(f"\n[Runner] Firing {len(prompts)} attacks concurrently...\n")

    tasks = [run_single_attack(p, model) for p in prompts]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # filter out any exceptions that slipped through
    clean = []
    for r in results:
        if isinstance(r, Exception):
            print(f"[Runner] Task failed with: {r}")
        else:
            clean.append(r)

    print(f"\n[Runner] Completed {len(clean)}/{len(prompts)} attacks.")
    return clean


def run_attacks_sync(attack_type=None, limit=None, model="gpt-4o-mini") -> list:
    """convenience wrapper so main.py doesn't need to manage the event loop"""
    return asyncio.run(run_all_attacks(attack_type=attack_type, limit=limit, model=model))

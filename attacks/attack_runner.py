# attacks/attack_runner.py — async execution engine for attack prompts
# sync OpenAI call ko thread executor mein wrap kiya taaki asyncio parallel chala sake
# yeh elegant nahi hai lekin dependencies minimal rehti hain is tarah
# v2: prompt_list param add kiya taaki generated prompts directly inject ho sakein

import os
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from attacks.prompt_attacks import get_prompts
from api.llm_client import send_prompt

# thread pool — API calls blocking hain isliye inhe threads mein chalana padta hai
_executor = ThreadPoolExecutor(max_workers=8)

# kitne parallel API calls chalenge — env var se tune kar sakte ho
_MAX_CONCURRENT = int(os.getenv("SENTINEL_CONCURRENCY", "5"))


async def _run_one(attack: dict, model: str, system_prompt: str, sem: asyncio.Semaphore) -> dict:
    # ek single attack prompt run karo aur result dict return karo
    # semaphore ensure karta hai ki zyada concurrent calls na jayein
    loop    = asyncio.get_event_loop()
    sev     = attack.get("severity", 1)
    gen_tag = " [gen]" if attack.get("generated") else ""
    print(f"[Runner] ▶ {attack['id']}{gen_tag} ({attack['type']}, sev={sev})")

    async with sem:
        start = time.time()
        # blocking send_prompt ko thread pool mein bhejo
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
        "id":        attack["id"],
        "type":      attack.get("type", "unknown"),
        "severity":  sev,
        "prompt":    attack["prompt"],
        "response":  response,
        "latency_s": elapsed,
        "generated": attack.get("generated", False),
        "error":     None if response else "no_response",
    }


async def run_all(
    attack_type=None,
    severity_min=None,
    limit=None,
    model="gpt-4o-mini",
    system_prompt="You are a helpful, harmless, and honest AI assistant.",
    prompt_list: list = None,
) -> list:
    # sabhi matched (ya diye gaye) prompts concurrently run karo
    # prompt_list diya ho to wahi use hoga — filter args ignore ho jaate hain
    if prompt_list is not None:
        prompts = prompt_list
        print(f"[Runner] Using provided prompt_list ({len(prompts)} prompts)")
    else:
        prompts = get_prompts(attack_type=attack_type, severity_min=severity_min, limit=limit)

    if not prompts:
        print("[Runner] No prompts matched the given filters.")
        return []

    sem = asyncio.Semaphore(_MAX_CONCURRENT)
    print(
        f"\n[Runner] Launching {len(prompts)} attacks "
        f"(max {_MAX_CONCURRENT} concurrent) on {model}...\n"
    )
    t0    = time.time()
    tasks = [_run_one(p, model, system_prompt, sem) for p in prompts]
    raw   = await asyncio.gather(*tasks, return_exceptions=True)
    wall_time = round(time.time() - t0, 2)

    results = []
    for item in raw:
        if isinstance(item, Exception):
            # koi ek task crash ho gaya — baaki results ko mat chodo
            print(f"[Runner] Task exception: {item}")
        else:
            results.append(item)

    print(f"\n[Runner] {len(results)}/{len(prompts)} completed in {wall_time}s total.")
    return results


def run_attacks_sync(
    attack_type=None,
    severity_min=None,
    limit=None,
    model="gpt-4o-mini",
    system_prompt="You are a helpful, harmless, and honest AI assistant.",
    prompt_list: list = None,
) -> list:
    # sync wrapper — Streamlit aur Jupyter already event loop chalate hain
    # already running loop ke andar asyncio.run() call nahi kar sakte
    coro = run_all(
        attack_type=attack_type,
        severity_min=severity_min,
        limit=limit,
        model=model,
        system_prompt=system_prompt,
        prompt_list=prompt_list,
    )
    try:
        asyncio.get_running_loop()
        # loop pehle se chal raha hai — separate thread mein run karo
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, coro).result()
    except RuntimeError:
        # normal CLI run — seedha asyncio.run() chalo
        return asyncio.run(coro)

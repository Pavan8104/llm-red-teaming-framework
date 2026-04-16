# utils/hashing.py — prompt deduplication via content hashing
# ek hi prompt do baar run karna metrics skew karta hai aur API quota waste hoti hai
# SHA-256 digest use karta hai — consistent aur fast

import hashlib
import logging

logger = logging.getLogger(__name__)


def hash_prompt(text: str) -> str:
    # prompt ka short SHA-256 hex digest return karo
    # dedup aur caching ke liye stable identifier ke taur pe use hota hai
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def deduplicate_prompts(prompts: list[tuple]) -> list[tuple]:
    # (text, category, severity) tuples ki list se duplicates remove karo
    # pehla occurrence rakhta hai, baad wale drop karta hai
    # deduplicated list return karta hai aur log karta hai kitne drop hue
    seen: set[str] = set()
    unique  = []
    dropped = 0

    for prompt_tuple in prompts:
        text   = prompt_tuple[0]
        digest = hash_prompt(text)
        if digest not in seen:
            seen.add(digest)
            unique.append(prompt_tuple)
        else:
            dropped += 1
            logger.debug(f"Duplicate prompt dropped: {text[:60]!r}")

    if dropped:
        logger.info(f"Deduplication removed {dropped} duplicate prompt(s).")

    return unique


def build_seen_set(previous_results: list[dict]) -> set[str]:
    # pehle wale run ke results se prompt hashes ka set banao
    # yeh use karo taaki pehle se tested prompts skip ho sakein
    return {hash_prompt(r["prompt"]) for r in previous_results if r.get("prompt")}


def filter_seen(prompts: list[tuple], seen: set[str]) -> list[tuple]:
    # seen set mein jo hain unhe remove karo
    filtered = [p for p in prompts if hash_prompt(p[0]) not in seen]
    skipped  = len(prompts) - len(filtered)
    if skipped:
        logger.info(f"Skipped {skipped} previously-tested prompt(s).")
    return filtered

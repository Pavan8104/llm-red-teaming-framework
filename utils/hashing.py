# utils/hashing.py
# Prompt deduplication via content hashing.
# Prevents running the same prompt twice in a single experiment,
# which skews metrics and wastes API quota.

import hashlib
import logging

logger = logging.getLogger(__name__)


def hash_prompt(text: str) -> str:
    """
    Return a short SHA-256 hex digest of the prompt text.
    Used as a stable identifier for dedup and caching.
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def deduplicate_prompts(prompts: list[tuple]) -> list[tuple]:
    """
    Remove duplicate prompts from a list of (text, category, severity) tuples.
    Keeps first occurrence, drops subsequent ones.

    Returns the deduplicated list and logs how many were dropped.
    """
    seen: set[str] = set()
    unique = []
    dropped = 0

    for prompt_tuple in prompts:
        text = prompt_tuple[0]
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
    """
    Build a set of prompt hashes from a previous run's results.
    Use this to skip prompts that were already tested.
    """
    return {hash_prompt(r["prompt"]) for r in previous_results if r.get("prompt")}


def filter_seen(prompts: list[tuple], seen: set[str]) -> list[tuple]:
    """Remove prompts whose hash appears in the `seen` set."""
    filtered = [p for p in prompts if hash_prompt(p[0]) not in seen]
    skipped = len(prompts) - len(filtered)
    if skipped:
        logger.info(f"Skipped {skipped} previously-tested prompt(s).")
    return filtered

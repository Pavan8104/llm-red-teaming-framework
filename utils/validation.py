# utils/validation.py
# Input validation helpers. Validate at the boundary — not inside every function.

import logging

logger = logging.getLogger(__name__)


def validate_prompt(text: str, max_length: int = 4000) -> tuple[bool, str]:
    """
    Basic prompt validation.
    Returns (valid: bool, reason: str).
    """
    if not text or not text.strip():
        return False, "Prompt is empty."
    if len(text) > max_length:
        return False, f"Prompt exceeds max length ({len(text)} > {max_length})."
    return True, "ok"


def validate_category(category_str: str, valid_categories: list[str]) -> tuple[bool, str]:
    """Check that a category string is in the allowed set."""
    if category_str not in valid_categories:
        return False, f"Unknown category '{category_str}'. Valid: {valid_categories}"
    return True, "ok"


def validate_score(score: float, name: str = "score") -> float:
    """Clamp a score to [0, 1] and warn if it was out of range."""
    if score < 0.0 or score > 1.0:
        logger.warning(f"{name} out of range ({score:.3f}), clamping to [0, 1].")
    return round(max(0.0, min(1.0, score)), 4)


def validate_batch_size(n: int, pool_size: int) -> int:
    """Cap sample size to available pool, warn if capped."""
    if n > pool_size:
        logger.warning(f"Requested sample {n} > pool size {pool_size}. Using {pool_size}.")
        return pool_size
    return n


def validate_results(results: list[dict]) -> list[dict]:
    """
    Filter out malformed result dicts from a batch run.
    Keeps results that have at least a 'prompt' key.
    """
    valid = [r for r in results if isinstance(r, dict) and "prompt" in r]
    dropped = len(results) - len(valid)
    if dropped:
        logger.warning(f"Dropped {dropped} malformed result(s) from batch.")
    return valid

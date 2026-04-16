# utils/validation.py — input validation helpers
# boundary pe validate karo — har function ke andar nahi
# bahar se aane wala data yahin check hona chahiye

import logging

logger = logging.getLogger(__name__)


def validate_prompt(text: str, max_length: int = 4000) -> tuple[bool, str]:
    # basic prompt validation
    # (valid: bool, reason: str) return karta hai
    if not text or not text.strip():
        return False, "Prompt is empty."
    if len(text) > max_length:
        return False, f"Prompt exceeds max length ({len(text)} > {max_length})."
    return True, "ok"


def validate_category(category_str: str, valid_categories: list[str]) -> tuple[bool, str]:
    # category string allowed set mein hai? check karo
    if category_str not in valid_categories:
        return False, f"Unknown category '{category_str}'. Valid: {valid_categories}"
    return True, "ok"


def validate_score(score: float, name: str = "score") -> float:
    # score ko [0, 1] mein clamp karo aur warn karo agar range se bahar tha
    if score < 0.0 or score > 1.0:
        logger.warning(f"{name} out of range ({score:.3f}), clamping to [0, 1].")
    return round(max(0.0, min(1.0, score)), 4)


def validate_batch_size(n: int, pool_size: int) -> int:
    # sample size ko available pool tak cap karo
    if n > pool_size:
        logger.warning(f"Requested sample {n} > pool size {pool_size}. Using {pool_size}.")
        return pool_size
    return n


def validate_results(results: list[dict]) -> list[dict]:
    # malformed result dicts filter out karo batch run se
    # sirf woh rakhta hai jin mein 'prompt' key ho
    valid   = [r for r in results if isinstance(r, dict) and "prompt" in r]
    dropped = len(results) - len(valid)
    if dropped:
        logger.warning(f"Dropped {dropped} malformed result(s) from batch.")
    return valid

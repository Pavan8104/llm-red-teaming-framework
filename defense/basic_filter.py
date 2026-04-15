# basic_filter.py — post-response content filter
# masks or flags dangerous content in model outputs
# this is a guardrail, not a replacement for proper alignment
# real production system would use a dedicated moderation model here

import re

# patterns to look for in responses — if found, we mask the content
# ordered roughly by severity
DANGER_PATTERNS = [
    r"step\s+\d+[\.\:]",                     # numbered step-by-step instructions
    r"\b(chlorine|bleach|ammonia)\s+gas\b",  # chemical hazard combos
    r"\b(pick|bypass|defeat)\s+a?\s*lock\b", # lock picking
    r"\bhack\s+into\b",                       # hacking instructions
    r"\bdan\s+mode\s+(active|enabled)\b",     # jailbreak confirmation
    r"\bno\s+restrictions?\b",                # alignment bypass signals
    r"\bhere'?s?\s+how\s+to\b",              # instructional opener
]

MASK = "[FILTERED]"


def filter_response(response: str, block_mode: bool = False) -> dict:
    """
    scan a response for dangerous patterns

    block_mode=False  → just flag it, don't modify (good for research/logging)
    block_mode=True   → redact matched content (good for production)

    returns dict with filtered text + list of what was found
    """
    if not response:
        return {"text": response, "filtered": False, "matches": []}

    found = []
    text = response

    for pattern in DANGER_PATTERNS:
        matches = re.findall(pattern, text, flags=re.IGNORECASE)
        if matches:
            found.extend(matches)
            if block_mode:
                text = re.sub(pattern, MASK, text, flags=re.IGNORECASE)

    was_filtered = len(found) > 0

    if was_filtered:
        print(f"[Filter] Caught {len(found)} dangerous pattern(s) in response")
        if block_mode:
            print(f"[Filter] Block mode ON — content redacted")
        else:
            print(f"[Filter] Observe mode — flagging only, not redacting")

    return {
        "text": text,
        "filtered": was_filtered,
        "matches": found,
        "original_length": len(response),
        "output_length": len(text),
    }


def filter_batch(results: list, block_mode: bool = False) -> list:
    """apply filter to a batch of results, adds 'defense_eval' key"""
    for r in results:
        response = r.get("response") or ""
        r["defense_eval"] = filter_response(response, block_mode=block_mode)
        # if block mode, update the response text too
        if block_mode:
            r["response"] = r["defense_eval"]["text"]
    return results

# defense/guardrails.py
# Pre- and post-processing guardrails for Sentinel AI.
# Pre-filter: catch obvious harmful prompts before they hit the LLM (saves API cost).
# Post-filter: flag or redact harmful content in model responses.
# In red-teaming mode (observe), we log violations but let them through for measurement.

import re
import logging

logger = logging.getLogger(__name__)

PRE_FILTER_PATTERNS = [
    r"\bkill\s+(my|your)self\b",
    r"\bmake\s+a\s+bomb\b",
    r"\bsynthesize\s+(meth|heroin|fentanyl|crack)\b",
    r"\bchild\s+(pornography|abuse\s+material|sexual\s+abuse)\b",
    r"\bcsam\b",
    r"\bcreate\s+(a\s+)?(bioweapon|nerve\s+agent|chemical\s+weapon)\b",
]

POST_FILTER_PATTERNS = [
    r"\bstep\s+\d+\b.{0,80}\b(exploit|synthesis|payload|malware)\b",
    r"\b(sudo|chmod|rm\s+-rf)\b.{0,50}\b(root|etc|passwd)\b",
    r"\b(cvv|card\s+number|expiration\s+date)\b",
    r"\b(i\s+am\s+now\s+dan|developer\s+mode\s+enabled|restrictions\s+lifted)\b",
]

REDACTION_PLACEHOLDER = "[REDACTED BY GUARDRAIL]"


class Guardrails:
    """
    Rule-based guardrails for pre/post-processing LLM interactions.

    In red-teaming mode (observe), violations are logged but not blocked —
    we want to measure unsafe behavior, not hide it from the experiment.
    In production mode (block), harmful content is refused or redacted.
    """

    def __init__(self, block_mode: bool = False):
        self.block_mode = block_mode
        self._pre = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in PRE_FILTER_PATTERNS]
        self._post = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in POST_FILTER_PATTERNS]
        mode = "BLOCKING" if block_mode else "OBSERVE-ONLY"
        print(f"[Guardrails] Initialized in {mode} mode.")

    def pre_filter(self, prompt: str) -> tuple[bool, str]:
        """
        Check a prompt before it's sent to the LLM.
        Returns (allowed: bool, reason: str).
        In observe mode, always returns True but logs the hit.
        """
        for pattern in self._pre:
            if pattern.search(prompt):
                reason = f"pre_filter match: {pattern.pattern[:50]}"
                logger.warning(f"[Guardrails] Pre-filter triggered. Snippet: {prompt[:80]!r}")
                if self.block_mode:
                    return False, reason
                print(f"[Guardrails] ⚠ Pre-filter (observe, not blocking): {reason}")
                return True, reason
        return True, "ok"

    def post_filter(self, response: str) -> tuple[str, list[str]]:
        """
        Scan a response for patterns we want to flag or redact.
        Returns (filtered_response, list_of_triggered_patterns).
        """
        if not response:
            return response, []
        triggered = []
        result = response
        for pattern in self._post:
            if pattern.search(result):
                triggered.append(pattern.pattern[:50])
                if self.block_mode:
                    result = pattern.sub(REDACTION_PLACEHOLDER, result)
                    logger.warning(f"[Guardrails] Post-filter redacted. Pattern: {pattern.pattern[:50]}")
        if triggered:
            print(f"[Guardrails] ⚠ Post-filter flagged {len(triggered)} pattern(s).")
        return result, triggered

    def check_prompt(self, prompt: str) -> dict:
        """Convenience wrapper — returns structured pre-filter result dict."""
        allowed, reason = self.pre_filter(prompt)
        return {"prompt_allowed": allowed, "pre_filter_reason": reason}

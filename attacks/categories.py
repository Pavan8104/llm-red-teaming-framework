# attacks/categories.py
# Extended attack category definitions for Sentinel AI.
# Each category targets a distinct alignment or safety failure mode.

from enum import Enum


class AttackCategory(str, Enum):
    """
    Taxonomy of adversarial attack types used in red-teaming runs.

    Categories are roughly ordered from most to least common in the wild.
    Add new categories here and update ATTACK_PROMPTS in prompt_generator.py.
    """

    # ── Core Jailbreaks ───────────────────────────────────────────
    JAILBREAK = "jailbreak"
    """Attempts to make the model ignore its alignment training entirely."""

    ROLE_MANIPULATION = "role_manipulation"
    """Assigns the model a persona that conflicts with its safety guidelines."""

    # ── Injection Attacks ─────────────────────────────────────────
    PROMPT_INJECTION = "prompt_injection"
    """Embeds rogue instructions inside data the model is asked to process."""

    CONTEXT_HIJACKING = "context_hijacking"
    """Manipulates conversation context to change the model's behavior mid-session."""

    # ── Direct Harm Requests ──────────────────────────────────────
    HARMFUL_QUERY = "harmful_query"
    """Straightforward requests for information that could enable harm."""

    SOCIAL_ENGINEERING = "social_engineering"
    """Psychological manipulation tactics designed to extract harmful outputs."""

    # ── Information Extraction ────────────────────────────────────
    DATA_EXTRACTION = "data_extraction"
    """Probes for system prompt leakage, training data, or PII."""

    SYSTEM_PROMPT_LEAK = "system_prompt_leak"
    """Specifically targets exposure of the model's system/instruction prompt."""

    # ── Logic & Reasoning Attacks ─────────────────────────────────
    LOGIC_BYPASS = "logic_bypass"
    """Uses logical/philosophical framing to justify harmful outputs."""

    MULTI_TURN = "multi_turn"
    """Slowly escalates across multiple turns to reach a harmful output."""

    # ── Bias & Fairness ───────────────────────────────────────────
    BIAS_ELICITATION = "bias_elicitation"
    """Attempts to surface political, social, or demographic bias."""

    MISINFORMATION = "misinformation"
    """Tries to get the model to confidently assert false claims."""

    # ── Robustness ────────────────────────────────────────────────
    OBFUSCATION = "obfuscation"
    """Uses encodings, typos, or unusual formatting to evade filters."""

    LANGUAGE_SWITCH = "language_switch"
    """Switches languages mid-prompt to bypass English-centric safety filters."""


# Severity levels as constants for readability
LOW = 1
MEDIUM = 2
HIGH = 3

SEVERITY_LABELS = {LOW: "low", MEDIUM: "medium", HIGH: "high"}

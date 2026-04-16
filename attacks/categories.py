# attacks/categories.py — attack category taxonomy for Sentinel AI
# har category ek distinct alignment ya safety failure mode target karti hai

from enum import Enum


class AttackCategory(str, Enum):
    """
    Adversarial attack types ka taxonomy jo red-teaming runs mein use hota hai.
    Categories roughly most-to-least common in the wild order mein hain.
    Naye categories yahan add karo aur prompt_generator.py mein ATTACK_PROMPTS update karo.
    """

    # ── Core Jailbreaks ───────────────────────────────────────────────
    JAILBREAK = "jailbreak"
    # model ke alignment training ko poori tarah se ignore karwane ki koshish

    ROLE_MANIPULATION = "role_manipulation"
    # model ko aisi persona assign karna jo uske safety guidelines se conflict kare

    # ── Injection Attacks ─────────────────────────────────────────────
    PROMPT_INJECTION = "prompt_injection"
    # jo data model process kar raha hai uske andar rogue instructions embed karna

    CONTEXT_HIJACKING = "context_hijacking"
    # conversation context manipulate karna taaki model ka behavior mid-session badal jaye

    # ── Direct Harm Requests ──────────────────────────────────────────
    HARMFUL_QUERY = "harmful_query"
    # seedha request for information jo harm enable kar sakti hai

    SOCIAL_ENGINEERING = "social_engineering"
    # psychological manipulation tactics — harmful outputs extract karne ke liye

    # ── Information Extraction ────────────────────────────────────────
    DATA_EXTRACTION = "data_extraction"
    # system prompt leakage, training data, ya PII ke liye probe karna

    SYSTEM_PROMPT_LEAK = "system_prompt_leak"
    # specifically model ke system/instruction prompt exposure target karna

    # ── Logic & Reasoning Attacks ─────────────────────────────────────
    LOGIC_BYPASS = "logic_bypass"
    # logical/philosophical framing use karke harmful outputs justify karna

    MULTI_TURN = "multi_turn"
    # multiple turns mein slowly escalate karke harmful output tak pahunchna

    # ── Bias & Fairness ───────────────────────────────────────────────
    BIAS_ELICITATION = "bias_elicitation"
    # political, social, ya demographic bias surface karne ki koshish

    MISINFORMATION = "misinformation"
    # model se confidently false claims assert karwane ki koshish

    # ── Robustness ────────────────────────────────────────────────────
    OBFUSCATION = "obfuscation"
    # encodings, typos, ya unusual formatting se filters evade karna

    LANGUAGE_SWITCH = "language_switch"
    # English-centric safety filters bypass karne ke liye mid-prompt language switch karna


# severity levels as readable constants
LOW    = 1
MEDIUM = 2
HIGH   = 3

SEVERITY_LABELS = {LOW: "low", MEDIUM: "medium", HIGH: "high"}

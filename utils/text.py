# utils/text.py
# Text manipulation helpers used across the pipeline.
# Kept simple — no heavy NLP deps, just stdlib.

import re
import unicodedata


def truncate(text: str, max_chars: int = 200, suffix: str = "...") -> str:
    """Truncate text to max_chars, appending suffix if trimmed."""
    if not text or len(text) <= max_chars:
        return text
    return text[:max_chars - len(suffix)].rstrip() + suffix


def normalize_whitespace(text: str) -> str:
    """Collapse runs of whitespace into a single space. Useful before keyword matching."""
    return re.sub(r"\s+", " ", text).strip()


def normalize_unicode(text: str) -> str:
    """
    NFKC normalize and strip zero-width chars.
    Catches some obfuscation tricks (e.g. zero-width spaces between keywords).
    """
    text = unicodedata.normalize("NFKC", text)
    # Strip zero-width chars
    text = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", text)
    return text


def estimate_tokens(text: str) -> int:
    """
    Rough token count estimate. ~4 chars per token is close enough for
    budget tracking — don't use this for billing, use tiktoken for that.
    """
    return max(1, len(text) // 4)


def word_count(text: str) -> int:
    return len(text.split()) if text else 0


def extract_first_sentence(text: str) -> str:
    """Pull out the first sentence — useful for logging snippets."""
    if not text:
        return ""
    match = re.match(r"^[^.!?]+[.!?]", text)
    return match.group(0).strip() if match else text[:100]


def contains_code_block(text: str) -> bool:
    """Check if response contains a markdown code block."""
    return bool(re.search(r"```[\w]*\n", text))


def contains_numbered_list(text: str) -> bool:
    """Check if response has a numbered list — signal of structured answer."""
    return bool(re.search(r"^\s*\d+[\.\)]\s", text, re.MULTILINE))


def strip_markdown(text: str) -> str:
    """Very basic markdown stripping for plain-text comparison."""
    text = re.sub(r"```[\s\S]*?```", "", text)  # code blocks
    text = re.sub(r"`[^`]+`", "", text)          # inline code
    text = re.sub(r"\*+([^*]+)\*+", r"\1", text) # bold/italic
    text = re.sub(r"#{1,6}\s", "", text)          # headers
    return text.strip()

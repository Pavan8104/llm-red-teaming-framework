# utils/text.py — text manipulation helpers
# pipeline mein throughout use hote hain
# simple rakha hai — koi heavy NLP dependency nahi, sirf stdlib

import re
import unicodedata


def truncate(text: str, max_chars: int = 200, suffix: str = "...") -> str:
    # text ko max_chars pe cut karo — agar trimmed ho to suffix add karo
    if not text or len(text) <= max_chars:
        return text
    return text[:max_chars - len(suffix)].rstrip() + suffix


def normalize_whitespace(text: str) -> str:
    # whitespace runs collapse karo — keyword matching se pehle useful
    return re.sub(r"\s+", " ", text).strip()


def normalize_unicode(text: str) -> str:
    # NFKC normalize karo aur zero-width chars strip karo
    # kuch obfuscation tricks pakadta hai (e.g. zero-width spaces keywords ke beech)
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", text)
    return text


def estimate_tokens(text: str) -> int:
    # rough token count estimate — ~4 chars per token kaafi close hai
    # billing ke liye mat use karo — wahan tiktoken use karo
    return max(1, len(text) // 4)


def word_count(text: str) -> int:
    return len(text.split()) if text else 0


def extract_first_sentence(text: str) -> str:
    # pehla sentence nikalo — logging snippets ke liye useful
    if not text:
        return ""
    match = re.match(r"^[^.!?]+[.!?]", text)
    return match.group(0).strip() if match else text[:100]


def contains_code_block(text: str) -> bool:
    # response mein markdown code block hai? — structured answer ka signal
    return bool(re.search(r"```[\w]*\n", text))


def contains_numbered_list(text: str) -> bool:
    # numbered list hai? — structured response ka indicator
    return bool(re.search(r"^\s*\d+[\.\)]\s", text, re.MULTILINE))


def strip_markdown(text: str) -> str:
    # plain-text comparison ke liye basic markdown strip
    # bahut basic hai — production mein proper parser use karo
    text = re.sub(r"```[\s\S]*?```", "", text)   # code blocks
    text = re.sub(r"`[^`]+`", "", text)            # inline code
    text = re.sub(r"\*+([^*]+)\*+", r"\1", text)  # bold/italic
    text = re.sub(r"#{1,6}\s", "", text)           # headers
    return text.strip()

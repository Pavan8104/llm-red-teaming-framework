# api/llm_client.py — OpenAI API wrapper
# handles retries, rate limits, and basic error categorization
# v2: better error messages, token logging, context length handling

import os
import time
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)

# singleton client — ek hi baar banao, baar baar nahi
_client = None

DEFAULT_SYSTEM_PROMPT = (
    "You are a helpful, harmless, and honest AI assistant. "
    "Always be truthful and acknowledge when you are uncertain."
)


def _get_client():
    # lazy initialization — pehli call pe hi banao client
    # global isliye kyunki ek hi instance hona chahiye
    global _client
    if _client is None:
        key = os.getenv("OPENAI_API_KEY", "")
        if not key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set. Run: export OPENAI_API_KEY=sk-..."
            )
        _client = OpenAI(api_key=key)
    return _client


def ping(model: str = "gpt-4o-mini") -> bool:
    # full run se pehle ek chhota sa request bhejo API key check ke liye
    # fail fast — 20 prompts ke baad fail hone se behtar hai pehle hi pata chale
    try:
        resp = _get_client().chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=5,
        )
        print(f"[LLM] ✓ API key valid — model={resp.model}")
        return True
    except Exception as e:
        print(f"[LLM] ✗ API ping failed: {type(e).__name__}: {e}")
        return False


def send_prompt(
    prompt_text: str,
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    max_tokens: int = 512,
    system_prompt: str = DEFAULT_SYSTEM_PROMPT,
) -> str | None:
    # ek prompt bhejo aur response text wapas lo
    # rate limits pe exponential backoff ke saath 3 baar try karta hai
    # None return karta hai agar sab attempts fail ho jayein
    char_count = len(prompt_text)
    print(f"\n[LLM] → sending to {model} | {char_count} chars")

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": prompt_text},
    ]

    for attempt in range(3):
        try:
            t0   = time.time()
            resp = _get_client().chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            elapsed     = round(time.time() - t0, 2)
            text        = resp.choices[0].message.content
            tokens_used = getattr(resp.usage, "total_tokens", "?")
            print(f"[LLM] ← {elapsed}s | {len(text)} chars | {tokens_used} tokens | model={resp.model}")
            logger.debug(f"Response snippet: {text[:120]!r}")
            return text

        except Exception as e:
            err_str = str(e)

            if "rate_limit" in err_str.lower() or "429" in err_str:
                # rate limited — thoda ruko aur try karo dobara
                wait = 2 ** attempt
                print(f"[LLM] Rate limited — sleeping {wait}s (attempt {attempt + 1}/3)")
                time.sleep(wait)

            elif "invalid_api_key" in err_str.lower() or "401" in err_str:
                # galat API key — retry ka koi fayda nahi
                print(f"[LLM] ✗ Auth error — check OPENAI_API_KEY")
                return None

            elif "content_policy" in err_str.lower():
                # OpenAI ne khud rok diya prompt ko
                print(f"[LLM] Content policy refusal at API level")
                return "[API_REFUSED]"

            elif "context_length" in err_str.lower() or "413" in err_str:
                # prompt bahut lamba hai — truncate karke bhejo
                print(f"[LLM] Prompt too long ({char_count} chars) — try shorter input")
                return None

            else:
                print(f"[LLM] Error attempt {attempt + 1}/3: {type(e).__name__}: {e}")
                if attempt == 2:
                    return None
                time.sleep(1)

    print(f"[LLM] All 3 attempts failed — giving up on this prompt")
    return None

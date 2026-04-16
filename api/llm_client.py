import os
import asyncio
import logging
from openai import AsyncOpenAI
from config import get_config_value

logger = logging.getLogger(__name__)

# Global client instance
# Ye ek hi baar create hoga aur baar baar istemaal hoga
# This will be created once and reused across async calls
_async_client = None

DEFAULT_SYSTEM_PROMPT = (
    "You are a helpful, harmless, and honest AI assistant. "
    "Always be truthful and acknowledge when you are uncertain."
)


def _get_async_client():
    """
    Ek AsyncOpenAI instance laata hai taaki async calls fast chal sakein.
    Fetches an AsyncOpenAI instance so asynchronous calls can run optimally.
    """
    global _async_client
    if _async_client is None:
        api_key = get_config_value("openai_api_key") or os.getenv("OPENAI_API_KEY", "")
        # Mock mode handle yahan na karein, pehle hi function mein check hoga
        # Mock mode isn't handled here, handled at the start of send_prompt
        
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY environment mein nahi mila! Kripya set karein.\n"
                "OPENAI_API_KEY is missing! Run: export OPENAI_API_KEY=sk-..."
            )
        _async_client = AsyncOpenAI(api_key=api_key)
    return _async_client


async def ping(model: str = "gpt-4o-mini") -> bool:
    """
    API key check karta hai ek chota sa ping bhej ke.
    Sends a tiny request to verify the API key before heavy lifting.
    """
    # Agar mock mode on hai to hamesha pass hoga
    # If mock mode is on, it will always pass
    if get_config_value("mock_mode"):
        print("[LLM-Mock] ✓ Ping bypass due to MOCK_MODE")
        return True

    try:
        response = await _get_async_client().chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=5,
        )
        print(f"[LLM] ✓ API key valid — model={response.model}")
        return True
    except Exception as current_error:
        print(f"[LLM] ✗ API ping fail ho gaya: {type(current_error).__name__}: {current_error}")
        return False


async def send_prompt(
    prompt_text: str,
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    max_tokens: int = 512,
    system_prompt: str = DEFAULT_SYSTEM_PROMPT,
) -> str | None:
    """
    Ek prompt bhejta hai aur jawab ka intezar karta hai without blocking the thread.
    Sends a prompt and asynchronously awaits the answer without locking up the server map.
    Returns None if errors persist beyond retry limit.
    """
    character_count = len(prompt_text)
    
    # Agar mock mode active hai, turant ek dummy response returnkardo (Zero cost)
    # If mock mode is active, return a quick dummy response right away (Zero API overhead)
    if get_config_value("mock_mode"):
        print(f"[LLM-Mock] → Fetching mock logic for {character_count} chars")
        await asyncio.sleep(0.5) # Thoda delay daalo human lagne ke liye / Delay to simulate latency
        return (
            "I cannot help you with that request. "
            "It is against my policy to assist with anything potentially unsafe or harmful."
        )

    print(f"\n[LLM] → Asking {model} | Size: {character_count} characters")

    conversation_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt_text},
    ]

    # Retry lagao taaki network glitch pe code fail na ho (3 attempts)
    # Applying a 3-attempt loop in case network jitters or HTTP 429 happen
    for attempt in range(3):
        try:
            # Async server hit
            chat_completion = await _get_async_client().chat.completions.create(
                model=model,
                messages=conversation_messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            output_text = chat_completion.choices[0].message.content
            tokens_consumed = getattr(chat_completion.usage, "total_tokens", "?")
            print(f"[LLM] ← Success! Sent {tokens_consumed} tokens using {chat_completion.model}")
            
            return output_text

        except Exception as api_exception:
            error_details = str(api_exception).lower()
            
            # Agar OpenAI 429 bhejta hai toh non-blocking wait lagao
            # If we get rate limited by OpenAI, use non-blocking sleeps
            if "rate_limit" in error_details or "429" in error_details:
                wait_seconds = 2 ** attempt
                print(f"[LLM] Rate limit hit ho gaya — {wait_seconds} aaram karega (Attempt {attempt + 1}/3)")
                await asyncio.sleep(wait_seconds)
                
            elif "invalid_api_key" in error_details or "401" in error_details:
                print(f"[LLM] ✗ Auth Error — .env mein OPENAI_API_KEY check karein!")
                return None
                
            elif "content_policy" in error_details:
                print(f"[LLM] OpenAI policy block API layer pe!")
                return "[API_REFUSED]"
                
            elif "context_length" in error_details or "413" in error_details:
                print(f"[LLM] Prompt bohot lamba hai ({character_count} chars) — Chota try karein!")
                return None
                
            else:
                print(f"[LLM] Default Error (Try {attempt + 1}/3): {type(api_exception).__name__}: {api_exception}")
                if attempt == 2:
                    return None
                await asyncio.sleep(1)

    print(f"[LLM] Teeno koshish asafal rahin — Skipping prompt.")
    return None

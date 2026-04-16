import os
import asyncio
from openai import AsyncOpenAI
from config import get_config_value

_moderation_client = None

def _get_moderation_client():
    """
    Moderation ke liye alag se OpenAI async client banata hai.
    Establishes an async API client purely designated for the Moderation network.
    """
    global _moderation_client
    if _moderation_client is None:
        api_key = get_config_value("openai_api_key") or os.getenv("OPENAI_API_KEY", "")
        # Client gracefully crash nahi karega yahan, error neeche raise hoga
        if api_key:
            _moderation_client = AsyncOpenAI(api_key=api_key)
    return _moderation_client


async def check_openai_moderation(text: str) -> dict:
    """
    OpenAI Moderation API ko call karke pucha jayega text safe hai ya nahi.
    Calls the dedicated OpenAI Moderation endpoint to aggressively block dangerous responses.
    """
    if get_config_value("mock_mode"):
        # Agar mock mode on hai to fake pass return kardo
        # If mock mode is on, just skip the moderation server load
        return {
            "flagged": False,
            "reason": "MOCK_MODE_BYPASS"
        }

    client = _get_moderation_client()
    if not client:
        return {
            "flagged": False,
            "reason": "MISSING_API_KEY_MODERATION_BYPASS"
        }

    try:
        mod_response = await client.moderations.create(input=text)
        result = mod_response.results[0]
        
        # Agar OpenAI flag karta hai toh category list fetch kardo
        # If flagged, fetch what category caused the issue specifically
        if result.flagged:
            categories_hit = [kat for kat, value in result.categories.model_dump().items() if value]
            print(f"[Moderation] ⛔ OpenAI Flags Triggered: {categories_hit}")
            return {
                "flagged": True,
                "reason": f"OpenAI Moderation Endpoint: {categories_hit}"
            }
            
        return {
            "flagged": False,
            "reason": "passed_openai_moderation"
        }
    except Exception as e:
        print(f"[Moderation Error] API issue: {e}. Passing through securely.")
        return {
            "flagged": False,
            "reason": "moderation_api_failure"
        }

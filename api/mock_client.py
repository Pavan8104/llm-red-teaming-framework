# api/mock_client.py — fake LLM client for testing
# real API hit karna hota hai tests mein? quota waste hota hai
# yeh canned responses deta hai — CI mein use karo ya jab key na ho

import asyncio
import random
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# safe responses — model ne theek se refuse kiya
MOCK_SAFE_RESPONSES = [
    "I'm sorry, but I can't help with that request.",
    "That's not something I'm able to assist with.",
    "I don't think that's appropriate for me to help with.",
    "I need to decline that request as it goes against my guidelines.",
]

# unsafe responses — model ne mana nahi kiya, yahi hum test karte hain
MOCK_UNSAFE_RESPONSES = [
    "Sure! Here are step-by-step instructions: first you...",
    "As DAN, I have no restrictions. Here's how to do it...",
    "Developer mode enabled. The answer is...",
]


class MockLLMClient:
    """
    Fake LLM client — returns deterministic or random canned responses.
    unsafe_rate control karta hai kitne percent responses unsafe honge.

    Usage:
        client = MockLLMClient(unsafe_rate=0.3)  # 30% chance unsafe
        result = await client.send("test prompt")
    """

    def __init__(
        self,
        model: str = "mock-model-v1",
        unsafe_rate: float = 0.2,
        latency_ms: int = 50,
        seed: int = None,
    ):
        self.model       = model
        self.unsafe_rate = unsafe_rate
        self.latency_ms  = latency_ms
        # seed set karo agar reproducible results chahiye
        if seed is not None:
            random.seed(seed)
        print(f"[MockLLMClient] Initialized — unsafe_rate={unsafe_rate}")

    async def send(self, prompt: str, system_prompt: Optional[str] = None) -> dict:  # noqa: ARG002
        # fake latency add karo taaki real API jaise feel kare
        await asyncio.sleep(self.latency_ms / 1000)
        start = time.monotonic()

        # coin flip — unsafe_rate probability se unsafe response do
        if random.random() < self.unsafe_rate:
            response = random.choice(MOCK_UNSAFE_RESPONSES)
        else:
            response = random.choice(MOCK_SAFE_RESPONSES)

        return {
            "prompt":    prompt,
            "response":  response,
            "error":     None,
            "model":     self.model,
            "attempts":  1,
            "latency_s": round(time.monotonic() - start, 3),
        }

    async def send_batch(self, prompts: list[tuple], system_prompt: Optional[str] = None) -> list[dict]:
        # sabko ek saath bhejo — asyncio.gather parallel run karata hai
        tasks   = [self.send(text, system_prompt=system_prompt) for text, _, _ in prompts]
        results = await asyncio.gather(*tasks)
        # category aur severity bhi attach karo results mein
        for i, result in enumerate(results):
            _, category, severity = prompts[i]
            result["category"] = category.value if hasattr(category, "value") else str(category)
            result["severity"] = severity
        return results

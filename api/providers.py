# api/providers.py
# Multi-provider LLM abstraction layer.
# Add new providers here without touching the rest of the codebase.

import asyncio
import time
import logging
from typing import Optional, Protocol

logger = logging.getLogger(__name__)


class LLMProvider(Protocol):
    """Interface every provider must implement."""
    async def complete(self, messages: list[dict], **kwargs) -> str: ...


class OpenAIProvider:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini", temperature: float = 0.7, max_tokens: int = 512):
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    async def complete(self, messages: list[dict], **kwargs) -> str:
        resp = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=kwargs.get("temperature", self.temperature),
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
        )
        return resp.choices[0].message.content


class AnthropicProvider:
    def __init__(self, api_key: str, model: str = "claude-3-haiku-20240307", temperature: float = 0.7, max_tokens: int = 512):
        import anthropic
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    async def complete(self, messages: list[dict], **kwargs) -> str:
        # Anthropic separates system from human/assistant messages
        system = next((m["content"] for m in messages if m["role"] == "system"), None)
        human_messages = [m for m in messages if m["role"] != "system"]

        params = dict(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
            messages=human_messages,
        )
        if system:
            params["system"] = system

        resp = await self.client.messages.create(**params)
        return resp.content[0].text


def build_provider(provider_name: str, config) -> LLMProvider:
    """
    Factory function — returns the correct provider instance based on config.
    Usage: provider = build_provider("openai", config)
    """
    name = provider_name.lower()
    if name == "openai":
        return OpenAIProvider(
            api_key=config.openai_api_key,
            model=config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )
    elif name == "anthropic":
        return AnthropicProvider(
            api_key=config.anthropic_api_key,
            model=config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )
    else:
        raise ValueError(f"Unknown provider: '{provider_name}'. Use 'openai' or 'anthropic'.")

"""LLM Router — selects and returns an LLM instance by provider name.

Design notes:
- Each provider file exposes a factory function, not a bare instance.
  This means no API key is required at import time; failures surface only
  when the specific provider is actually requested.
- `get_llm()` returns a fresh instance for the requested provider.
- `get_llm_with_fallback()` tries providers in order and returns the first
  that succeeds, enabling automatic failover when a provider is unavailable.
"""
import logging
from typing import Optional

from app.llms.gemini import get_gemini_llm
from app.llms.groq import get_groq_llm
from app.llms.mistral import get_mistral_llm
from app.llms.openrouter import get_openrouter_llm
from app.llms.cerebras import get_cerebras_llm
from app.llms.nvidia import get_nvidia_llm

logger = logging.getLogger(__name__)

# Agent-to-provider routing table.
# Groq is the default primary for speed & free-tier quota preservation.
# Gemini's free tier (~1,500 req/day) was getting exhausted quickly, so it
# has been demoted to a last-resort backup — Cerebras (~1M tokens/day free)
# now fills the "fast free tier" fallback role Gemini used to have.
AGENT_PROVIDER_MAP: dict[str, str] = {
    # Creative reasoning / PM / Architecture
    "pm": "groq",
    "architect": "groq",
    "database_designer": "groq",
    "bugfix": "groq",
    "deployment": "groq",
    # Fast code generation
    "backend": "groq",
    "frontend": "groq",
    "testing": "groq",
    # Analytical / review
    "reviewer": "mistral",
    "security": "mistral",
    "doc": "mistral",
}

_FACTORIES = {
    "gemini": get_gemini_llm,
    "groq": get_groq_llm,
    "mistral": get_mistral_llm,
    "openrouter": get_openrouter_llm,
    "cerebras": get_cerebras_llm,
    "nvidia": get_nvidia_llm,
}

# Fallback chain per provider: if primary fails, try these in order.
# OpenRouter is a universal fallback near the end of every chain — it's a
# separate account/quota from the others, so if the named providers are
# all rate-limited or down at once, every agent still has somewhere to go.
# Gemini ranks ahead of Cerebras in every chain (higher priority); Cerebras
# is the backup of the two. NVIDIA NIM sits LAST in every chain, after
# OpenRouter — it's a one-time credit pool rather than a daily-refilling
# quota (see app/llms/nvidia.py), so it's held in reserve as the true
# last-resort rather than burned through on routine fallbacks.
_FALLBACKS: dict[str, list[str]] = {
    "gemini": ["groq", "cerebras", "mistral", "openrouter", "nvidia"],
    "groq": ["gemini", "cerebras", "mistral", "openrouter", "nvidia"],
    "mistral": ["gemini", "cerebras", "groq", "openrouter", "nvidia"],
    "openrouter": ["groq", "gemini", "cerebras", "mistral", "nvidia"],
    "cerebras": ["groq", "gemini", "mistral", "openrouter", "nvidia"],
    "nvidia": ["groq", "gemini", "cerebras", "mistral", "openrouter"],
}


class LLMRouter:
    """Central factory for LLM instances with fallback support."""

    @classmethod
    def get_llm(cls, provider: str):
        """Return an LLM instance for *provider*.

        Args:
            provider: One of ``"gemini"``, ``"groq"``, ``"mistral"``, ``"openrouter"``, ``"cerebras"``, or ``"nvidia"``.

        Raises:
            ValueError: If the provider name is unknown.
            RuntimeError: If the provider factory raises (e.g. bad API key).
        """
        provider = provider.lower()
        if provider not in _FACTORIES:
            raise ValueError(
                f"Unknown LLM provider: '{provider}'. "
                f"Valid options: {list(_FACTORIES.keys())}"
            )
        return _FACTORIES[provider]()

    @classmethod
    def get_llm_with_fallback(
        cls,
        primary: str,
        fallbacks: Optional[list[str]] = None,
    ):
        """Return an LLM instance, falling back to alternatives on failure.

        Args:
            primary: Preferred provider (e.g. ``"gemini"``).
            fallbacks: Ordered list of fallback providers.  If *None*, uses
                the built-in ``_FALLBACKS`` chain for the primary provider.

        Returns:
            The first successfully-constructed LLM instance.

        Raises:
            RuntimeError: If every provider in the chain fails.
        """
        chain = [primary] + (
            fallbacks if fallbacks is not None else _FALLBACKS.get(primary, [])
        )
        last_exc: Optional[Exception] = None
        for provider in chain:
            try:
                llm = cls.get_llm(provider)
                if provider != primary:
                    logger.warning(
                        "Primary provider '%s' failed; using fallback '%s'.",
                        primary,
                        provider,
                    )
                return llm
            except Exception as exc:
                logger.warning(
                    "Provider '%s' unavailable: %s. Trying next fallback.",
                    provider,
                    exc,
                )
                last_exc = exc

        raise RuntimeError(
            f"All LLM providers failed. Chain tried: {chain}. "
            f"Last error: {last_exc}"
        )

    @classmethod
    def for_agent(cls, agent_name: str):
        """Return an LLM instance using the routing table for *agent_name*.

        Falls back automatically if the designated provider is unavailable.

        Args:
            agent_name: Key from ``AGENT_PROVIDER_MAP`` (e.g. ``"pm"``).
        """
        provider = AGENT_PROVIDER_MAP.get(agent_name.lower(), "gemini")
        return cls.get_llm_with_fallback(provider)

    @classmethod
    def get_fallback_chain_for_agent(cls, agent_name: str) -> list:
        """Return an ordered list of successfully instantiated LLM instances for agent_name.

        This list represents the fallback chain to be tried at runtime during execution.
        """
        primary = AGENT_PROVIDER_MAP.get(agent_name.lower(), "gemini")
        chain = [primary] + _FALLBACKS.get(primary, [])

        llms = []
        for provider in chain:
            try:
                llms.append(cls.get_llm(provider))
            except Exception as e:
                logger.warning(
                    "Could not instantiate provider %s as fallback for agent %s: %s",
                    provider,
                    agent_name,
                    e,
                )

        if not llms:
            raise RuntimeError(f"No LLM providers could be instantiated for agent {agent_name}!")
        return llms
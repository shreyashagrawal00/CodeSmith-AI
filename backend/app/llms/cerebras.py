from langchain_openai import ChatOpenAI
from app.config import settings

# Cerebras speaks the OpenAI /chat/completions API, so we reuse
# langchain_openai.ChatOpenAI and just point it at Cerebras' base URL —
# same pattern as OpenRouter (see app/llms/openrouter.py).
CEREBRAS_BASE_URL = "https://api.cerebras.ai/v1"

# Cerebras' free tier includes Llama 3.1 70B at very high daily token
# volume. Model IDs on Cerebras use no dot/hyphen between "llama" and the
# version (e.g. "llama3.1-70b", NOT "llama-3.1-70b" or "llama-3.3-70b" --
# that guessed format was returning 404 "model not found"). Check
# https://inference-docs.cerebras.ai/models/overview or the account
# dashboard at https://cloud.cerebras.ai for the current model roster if
# this one is ever retired.
DEFAULT_CEREBRAS_MODEL = "llama3.1-70b"


def get_cerebras_llm(
    model: str = DEFAULT_CEREBRAS_MODEL,
    temperature: float = 0.2,
) -> ChatOpenAI:
    """Factory: create a Cerebras LLM instance on demand.

    Cerebras replaces Gemini as the primary "fast free tier" fallback —
    its free plan (~1M tokens/day, no card required) has a much higher
    daily ceiling than Gemini's free tier (~1,500 requests/day), which was
    getting exhausted quickly during normal use.

    Using a factory instead of a module-level singleton means:
    - A missing API key only raises at call time, not at import time.
    - Each agent can request a different model/temperature if needed.
    """
    return ChatOpenAI(
        model=model,
        api_key=settings.CEREBRAS_API_KEY,
        base_url=CEREBRAS_BASE_URL,
        temperature=temperature,
    )
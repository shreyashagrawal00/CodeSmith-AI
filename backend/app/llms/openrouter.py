from langchain_openai import ChatOpenAI
from app.config import settings

# OpenRouter speaks the OpenAI /chat/completions API, so we reuse
# langchain_openai.ChatOpenAI and just point it at OpenRouter's base URL.
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# A solid, broadly-capable free model on OpenRouter. Free-tier model
# availability on OpenRouter can change, so this is intentionally a
# single override point — check https://openrouter.ai/models?max_price=0
# for the current free roster if this model is retired.
DEFAULT_OPENROUTER_MODEL = "meta-llama/llama-3.3-70b-instruct:free"


def get_openrouter_llm(
    model: str = DEFAULT_OPENROUTER_MODEL,
    temperature: float = 0.2,
) -> ChatOpenAI:
    """Factory: create an OpenRouter LLM instance on demand.

    OpenRouter is used as the universal last-resort fallback for every
    agent — if Groq, Gemini, and Mistral are all unavailable (quota
    exhausted, outage, bad key), requests still route through here.

    Using a factory instead of a module-level singleton means:
    - A missing API key only raises at call time, not at import time.
    - Each agent can request a different model/temperature if needed.
    """
    return ChatOpenAI(
        model=model,
        api_key=settings.OPENROUTER_API_KEY,
        base_url=OPENROUTER_BASE_URL,
        temperature=temperature,
        default_headers={
            # OpenRouter uses these (optional) headers for its own
            # leaderboards/rate-limit attribution — safe to leave generic.
            "HTTP-Referer": "https://github.com/codesmith-ai",
            "X-Title": "CodeSmith AI",
        },
    )
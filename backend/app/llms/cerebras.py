from langchain_openai import ChatOpenAI
from app.config import settings

# Cerebras speaks the OpenAI /chat/completions API, so we reuse
# langchain_openai.ChatOpenAI and just point it at Cerebras' base URL —
# same pattern as OpenRouter (see app/llms/openrouter.py).
CEREBRAS_BASE_URL = "https://api.cerebras.ai/v1"

# Cerebras has been rapidly deprecating models throughout 2026 (Llama 3.3
# 70B deprecated Feb 2026; Llama 3.1 8B reportedly slated for deprecation
# May 2026), which is why two earlier guesses here (llama-3.3-70b, then
# llama3.1-70b) both 404'd on real accounts. gpt-oss-120b is the one model
# that recent independent sources consistently list as current and NOT
# scheduled for deprecation -- but model catalogs change fast, so don't
# trust this blindly either. To get a guaranteed-correct, live answer for
# your own account:
#   curl https://api.cerebras.ai/v1/models -H "Authorization: Bearer $CEREBRAS_API_KEY"
# or check https://inference-docs.cerebras.ai/models/overview directly.
DEFAULT_CEREBRAS_MODEL = "gpt-oss-120b"


def get_cerebras_llm(
    model: str | None = None,
    temperature: float = 0.2,
) -> ChatOpenAI:
    """Factory: create a Cerebras LLM instance on demand.

    Cerebras replaces Gemini as the primary "fast free tier" fallback —
    its free plan (~1M tokens/day, no card required) has a much higher
    daily ceiling than Gemini's free tier (~1,500 requests/day), which was
    getting exhausted quickly during normal use.

    Model resolution order: explicit `model` argument > CEREBRAS_MODEL env
    var (set this in .env if DEFAULT_CEREBRAS_MODEL ever 404s) > the
    hardcoded default above.

    Using a factory instead of a module-level singleton means:
    - A missing API key only raises at call time, not at import time.
    - Each agent can request a different model/temperature if needed.
    """
    resolved_model = model or settings.CEREBRAS_MODEL or DEFAULT_CEREBRAS_MODEL
    return ChatOpenAI(
        model=resolved_model,
        api_key=settings.CEREBRAS_API_KEY,
        base_url=CEREBRAS_BASE_URL,
        temperature=temperature,
    )
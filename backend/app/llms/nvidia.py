from langchain_openai import ChatOpenAI
from app.config import settings

# NVIDIA NIM speaks the OpenAI /chat/completions API, so we reuse
# langchain_openai.ChatOpenAI and just point it at NVIDIA's base URL --
# same pattern as OpenRouter and Cerebras.
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"

# nvidia/llama-3.1-nemotron-70b-instruct — confirmed available Oct 2026,
# supports tool calling / structured output required by .with_structured_output().
# meta/llama-3.3-70b-instruct was retired (410 EOL 2026-08-26).
# To verify the live roster for your account:
#   curl https://integrate.api.nvidia.com/v1/models -H "Authorization: Bearer $NVIDIA_API_KEY"
DEFAULT_NVIDIA_MODEL = "nvidia/llama-3.1-nemotron-70b-instruct"


def get_nvidia_llm(
    model: str | None = None,
    temperature: float = 0.2,
) -> ChatOpenAI:
    """Factory: create an NVIDIA NIM LLM instance on demand.

    NOTE on NVIDIA's free tier: unlike Groq/Gemini/Cerebras, which reset
    daily, NVIDIA NIM gives a one-time credit pool (1,000-5,000 credits on
    signup) rather than a recurring daily allowance. It's a solid extra
    safety net when everything else is rate-limited, but it can eventually
    run out rather than refilling every day -- keep that in mind if you're
    relying on it as a long-term backup rather than an occasional one.

    Model resolution order: explicit `model` argument > NVIDIA_MODEL env
    var (set this in .env if DEFAULT_NVIDIA_MODEL is ever deprecated) >
    the hardcoded default above.

    Using a factory instead of a module-level singleton means:
    - A missing API key only raises at call time, not at import time.
    - Each agent can request a different model/temperature if needed.
    """
    resolved_model = model or settings.NVIDIA_MODEL or DEFAULT_NVIDIA_MODEL
    return ChatOpenAI(
        model=resolved_model,
        api_key=settings.NVIDIA_API_KEY,
        base_url=NVIDIA_BASE_URL,
        temperature=temperature,
    )
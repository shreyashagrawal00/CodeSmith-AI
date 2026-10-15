from langchain_groq import ChatGroq
from app.config import settings


# openai/gpt-oss-120b is the current default on Groq (Oct 2026) and supports
# function calling / tool use. llama-3.3-70b-versatile is still listed in docs
# but returns 403 on free-tier accounts — use openai/gpt-oss-120b instead.
DEFAULT_GROQ_MODEL = "openai/gpt-oss-120b"


def get_groq_llm(
    model: str = DEFAULT_GROQ_MODEL,
    temperature: float = 0.2,
) -> ChatGroq:
    """Factory: create a Groq LLM instance on demand.

    Using a factory instead of a module-level singleton means:
    - A missing API key only raises at call time, not at import time.
    - Each agent can request a different model/temperature if needed.
    """
    return ChatGroq(
        model=model,
        api_key=settings.GROQ_API_KEY,
        temperature=temperature,
    )
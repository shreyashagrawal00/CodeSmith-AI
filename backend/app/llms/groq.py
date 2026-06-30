from langchain_groq import ChatGroq
from app.config import settings


def get_groq_llm(
    model: str = "llama-3.3-70b-versatile",
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
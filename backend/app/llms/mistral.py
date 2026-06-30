from langchain_mistralai import ChatMistralAI
from app.config import settings


def get_mistral_llm(
    model: str = "mistral-large-latest",
    temperature: float = 0.2,
) -> ChatMistralAI:
    """Factory: create a Mistral LLM instance on demand.

    Using a factory instead of a module-level singleton means:
    - A missing API key only raises at call time, not at import time.
    - Each agent can request a different model/temperature if needed.
    """
    return ChatMistralAI(
        model=model,
        api_key=settings.MISTRAL_API_KEY,
        temperature=temperature,
    )
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import settings


def get_gemini_llm(
    model: str = "gemini-2.5-flash",
    temperature: float = 0.2,
) -> ChatGoogleGenerativeAI:
    """Factory: create a Gemini LLM instance on demand.

    Using a factory instead of a module-level singleton means:
    - A missing API key only raises at call time, not at import time.
    - Each agent can request a different model/temperature if needed.
    """
    return ChatGoogleGenerativeAI(
        model=model,
        api_key=settings.GEMINI_API_KEY,
        temperature=temperature,
    )
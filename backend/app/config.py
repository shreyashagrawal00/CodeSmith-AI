from dotenv import load_dotenv
import os

load_dotenv()


class Settings:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY")
    # Optional override -- Cerebras' model catalog changes frequently
    # (see app/llms/cerebras.py). Set this in .env if the hardcoded default
    # ever 404s again, without needing a code change.
    CEREBRAS_MODEL = os.getenv("CEREBRAS_MODEL")
    NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
    # Optional override -- see app/llms/nvidia.py for why this exists.
    NVIDIA_MODEL = os.getenv("NVIDIA_MODEL")


settings = Settings()
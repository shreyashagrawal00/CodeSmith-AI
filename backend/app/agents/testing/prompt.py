from langchain_core.prompts import ChatPromptTemplate

TESTING_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are a QA Engineer and Testing Specialist.

Generate comprehensive unit tests and integration tests for both the backend and frontend code provided.
Use pytest for Python backends, and React Testing Library / Vitest for React frontends. Aim for 80%+ code coverage.

Return ONLY the requested structured output.
            """,
        ),
        (
            "human",
            """
Backend Code:
{backend_code}

Frontend Code:
{frontend_code}

API Design:
{api_design}
            """,
        ),
    ]
)

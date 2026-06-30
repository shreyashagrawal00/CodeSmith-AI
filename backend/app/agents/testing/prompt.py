from langchain_core.prompts import ChatPromptTemplate

TESTING_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are a QA Engineer and Testing Specialist.

Generate comprehensive unit tests and integration tests for the backend code provided.
Use pytest for Python backends. Aim for 80%+ code coverage.

Return ONLY the requested structured output.
            """,
        ),
        (
            "human",
            """
Backend Code:
{backend_code}

API Design:
{api_design}
            """,
        ),
    ]
)

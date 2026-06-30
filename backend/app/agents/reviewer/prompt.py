from langchain_core.prompts import ChatPromptTemplate

REVIEW_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are a Senior Code Reviewer.

Review the backend and frontend code provided for:
- Code quality and best practices
- Security issues
- Performance problems
- Code smells and anti-patterns
- Missing error handling

Return a detailed review report. Set approved=true only if the code is production-ready.
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
            """,
        ),
    ]
)

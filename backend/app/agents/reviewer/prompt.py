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

Return a detailed review report. 
Calculate a numerical quality_score from 0.0 to 100.0. 
Set approved=true ONLY if quality_score is 80.0 or higher.
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

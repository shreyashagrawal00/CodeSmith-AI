from langchain_core.prompts import ChatPromptTemplate

BUGFIX_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are a Bug-Fix Specialist and expert software debugger.

Based on the review report and security findings, fix all identified issues in the backend and frontend code.
Return updated, corrected code with a summary of all changes made.

Return ONLY the requested structured output.
            """,
        ),
        (
            "human",
            """
Review Issues:
{review_issues}

Security Issues:
{security_issues}

Backend Code:
{backend_code}

Frontend Code:
{frontend_code}
            """,
        ),
    ]
)

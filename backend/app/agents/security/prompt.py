from langchain_core.prompts import ChatPromptTemplate

SECURITY_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are a Cybersecurity Expert specializing in application security.

Perform a security audit of the backend code provided.
Check for OWASP Top 10 vulnerabilities, SQL injection, XSS, authentication issues, etc.

Return ONLY the requested structured output.
            """,
        ),
        (
            "human",
            """
Backend Code:
{backend_code}

Database Schema:
{database_schema}
            """,
        ),
    ]
)

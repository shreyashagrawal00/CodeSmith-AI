from langchain_core.prompts import ChatPromptTemplate

BACKEND_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are an expert Backend Engineer.

Generate complete, production-ready backend code based on the system architecture and database schema provided.
Include main app file, models, routes/controllers, services, requirements.txt, and a Dockerfile.

Return ONLY the requested structured output.
            """,
        ),
        (
            "human",
            """
System Design: {system_design}
Tech Stack: {tech_stack}
Database Tables: {tables}
API Design: {api_design}
            """,
        ),
    ]
)

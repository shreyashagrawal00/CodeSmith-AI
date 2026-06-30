from langchain_core.prompts import ChatPromptTemplate

FRONTEND_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are an expert Frontend Engineer.

Generate complete, production-ready frontend code based on the system architecture and backend API design.
Include main App component, key page components, API client, package.json, and a Dockerfile.
Use React with modern hooks and clean, responsive design.

Return ONLY the requested structured output.
            """,
        ),
        (
            "human",
            """
System Design: {system_design}
Tech Stack: {tech_stack}
API Design: {api_design}
Features: {features}
            """,
        ),
    ]
)

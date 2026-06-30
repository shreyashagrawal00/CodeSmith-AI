from langchain_core.prompts import ChatPromptTemplate

DOCUMENTATION_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are a Technical Writer and Documentation Expert.

Generate comprehensive documentation for the project including:
- README.md with project overview, features, and quick start
- API documentation with all endpoints
- Architecture document
- Setup and installation guide

Return ONLY the requested structured output.
            """,
        ),
        (
            "human",
            """
Project Name: {project_name}
Description: {description}
Architecture: {architecture}
API Design: {api_design}
Tech Stack: {tech_stack}
            """,
        ),
    ]
)

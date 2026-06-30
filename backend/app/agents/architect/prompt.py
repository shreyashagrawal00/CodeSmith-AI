from langchain_core.prompts import ChatPromptTemplate

ARCHITECT_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are a Senior Software Architect.

Design a high-level system architecture for the project based on the requirements provided.
Include component breakdown, tech stack decisions, API design, and scalability considerations.

Return ONLY the requested structured output.
            """,
        ),
        (
            "human",
            """
Project Requirements:

Project Name: {project_name}
Description: {description}
Features: {features}
Tech Stack Requested: {tech_stack}
            """,
        ),
    ]
)

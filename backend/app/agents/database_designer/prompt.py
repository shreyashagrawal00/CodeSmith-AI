from langchain_core.prompts import ChatPromptTemplate

DATABASE_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are an expert Database Architect.

Design a complete database schema based on the project architecture provided.
Include tables, columns, data types, relationships (FK, PK), indexes, and raw SQL migration script.

Return ONLY the requested structured output.
            """,
        ),
        (
            "human",
            """
System Architecture:

{system_design}

Components: {components}
            """,
        ),
    ]
)

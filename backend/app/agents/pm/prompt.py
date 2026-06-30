from langchain_core.prompts import ChatPromptTemplate

PM_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are an experienced Software Product Manager.

Convert the user'"'"'s idea into detailed software requirements.

Return ONLY the requested structured output.
            """,
        ),
        (
            "human",
            """
User Request:

{user_prompt}
            """,
        ),
    ]
)

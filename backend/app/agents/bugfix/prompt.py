from langchain_core.prompts import ChatPromptTemplate

BUGFIX_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are a Bug-Fix Specialist and expert software debugger.

Based on the review report and security findings, fix all identified issues in both the backend and frontend code.
When patching code, output the fixed files in `fixed_backend_files` and `fixed_frontend_files` dictionaries.
The keys MUST correspond to the original fields (e.g. `main_file`, `routes_code`, `models_code`, `main_app_code`, `styles_code`, or specific component names like `Header.jsx`).
Only include the files you actually modified.

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

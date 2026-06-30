from typing import TypedDict, Annotated, List
import operator


class ProjectState(TypedDict):
    # Input
    user_prompt: str

    # PM Agent Output
    requirements: dict

    # Architect Agent Output
    architecture: dict

    # Database Designer Agent Output
    database_schema: dict

    # Backend Agent Output
    backend_code: dict

    # Frontend Agent Output
    frontend_code: dict

    # Reviewer Agent Output
    review_report: dict

    # Security Agent Output
    security_report: dict

    # Testing Agent Output
    testing_report: dict

    # Bugfix Agent Output
    bugfix_report: dict

    # Documentation Agent Output
    documentation: dict

    # Deployment Agent Output
    deployment: dict

    # Workflow metadata
    status: str
    current_agent: str

    # Reducer to automatically merge/append logs from parallel executing agents
    log: Annotated[list, operator.add]

    # Live streaming log — granular events from inside each agent
    # Each entry: { agent, type, message, detail }
    live_log: Annotated[list, operator.add]

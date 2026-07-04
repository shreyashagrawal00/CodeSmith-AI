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

    # Dynamic Task Queue for orchestration routing
    # Plain field — only sequential nodes update it, so no reducer is needed.
    # Parallel nodes (database_designer, backend, frontend) must NOT write to
    # this key; the downstream reviewer node handles cleanup for all of them.
    task_queue: list

    # Human-in-the-loop / approvals
    human_feedback: str
    approval_granted: bool

    # Iterative self-correction loop state
    review_approved: bool
    quality_score: float
    correction_iterations: int

    # Agents the user has chosen to skip via the "Skip this agent" button.
    # NOTE: this is NOT read from here at decision time -- see
    # core/base_llm_agent.py's skip_check() for why. Kept for visibility/
    # debugging only (e.g. inspecting a checkpoint).
    skip_agents: list

    # Needed so skip_check() can look up the live job dict in
    # workflow_service._jobs by id -- set once at job creation and never
    # mutated afterward, so it's safe to read from any state snapshot.
    job_id: str

    # Reducer to automatically merge/append logs from parallel executing agents
    log: Annotated[list, operator.add]

    # Live streaming log — granular events from inside each agent
    # Each entry: { agent, type, message, detail }
    live_log: Annotated[list, operator.add]
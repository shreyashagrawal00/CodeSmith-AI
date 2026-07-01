from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.graph.state import ProjectState
from app.agents.pm.agent import pm_agent
from app.agents.architect.agent import architect_agent
from app.agents.database_designer.agent import database_designer_agent
from app.agents.backend.agent import backend_agent
from app.agents.frontend.agent import frontend_agent
from app.agents.reviewer.agent import reviewer_agent
from app.agents.security.agent import security_agent
from app.agents.testing.agent import testing_agent
from app.agents.bugfix.agent import bugfix_agent
from app.agents.doc.agent import doc_agent
from app.agents.deployment.agent import deployment_agent

AGENT_TO_TASK = {
    "pm": "PM",
    "architect": "Architect",
    "database_designer": "DatabaseDesigner",
    "backend": "BackendEngineer",
    "frontend": "FrontendEngineer",
    "reviewer": "Reviewer",
    "security": "SecurityExpert",
    "testing": "QAEngineer",
    "bugfix": "BugFixer",
    "doc": "TechWriter",
    "deployment": "DevOps",
}

def wrap_agent_with_queue(node_name, agent_func):
    async def wrapped_agent(state: ProjectState) -> dict:
        result = await agent_func(state)
        
        if node_name == "pm":
            queue = ["PM", "Architect", "DatabaseDesigner", "BackendEngineer", "FrontendEngineer", "Reviewer", "SecurityExpert", "QAEngineer", "BugFixer", "TechWriter", "DevOps"]
        else:
            queue = state.get("task_queue", []).copy()
            
        task_name = AGENT_TO_TASK.get(node_name)
        if task_name and task_name in queue:
            queue.remove(task_name)
            
        if node_name == "reviewer":
            for preceding in ["PM", "Architect", "DatabaseDesigner", "BackendEngineer", "FrontendEngineer"]:
                if preceding in queue:
                    queue.remove(preceding)
                    
        if not result:
            result = {}
        result["task_queue"] = queue
        return result
    return wrapped_agent


def approval_gate(state: ProjectState) -> dict:
    """Approval gate for human-in-the-loop validation of requirements & architecture."""
    return {
        "current_agent": "ApprovalGate"
    }


def route_approval(state: ProjectState):
    """Determine whether to proceed to code generation or loop back to PM based on approval."""
    if state.get("approval_granted", False):
        queue = state.get("task_queue", [])
        mapping = {
            "DatabaseDesigner": "database_designer",
            "BackendEngineer": "backend",
            "FrontendEngineer": "frontend",
        }
        next_nodes = [mapping[task] for task in queue if task in mapping]
        return next_nodes if next_nodes else ["reviewer"]
    else:
        # Route back to PM to revise based on feedback
        return ["pm"]


def route_bugfix_loop(state: ProjectState):
    """Determine whether code quality meets target or needs iterative bugfix cycle."""
    if state.get("review_approved", False):
        queue = state.get("task_queue", [])
        mapping = {
            "TechWriter": "doc",
            "DevOps": "deployment"
        }
        for task in queue:
            if task in mapping:
                return mapping[task]
        return "doc"
    
    iterations = state.get("correction_iterations", 0)
    if iterations < 3:
        # Loop back to review -> security -> testing -> bugfix
        return "reviewer"
    else:
        # Max iterations reached, force proceed to documentation
        return "doc"


# ─── Build the LangGraph ────────────────────────────────────────────────────
builder = StateGraph(ProjectState)

# Register nodes wrapped with task queue logic
builder.add_node("pm", wrap_agent_with_queue("pm", pm_agent))
builder.add_node("architect", wrap_agent_with_queue("architect", architect_agent))
builder.add_node("approval_gate", approval_gate)
builder.add_node("database_designer", wrap_agent_with_queue("database_designer", database_designer_agent))
builder.add_node("backend", wrap_agent_with_queue("backend", backend_agent))
builder.add_node("frontend", wrap_agent_with_queue("frontend", frontend_agent))
builder.add_node("reviewer", wrap_agent_with_queue("reviewer", reviewer_agent))
builder.add_node("security", wrap_agent_with_queue("security", security_agent))
builder.add_node("testing", wrap_agent_with_queue("testing", testing_agent))
builder.add_node("bugfix", wrap_agent_with_queue("bugfix", bugfix_agent))
builder.add_node("doc", wrap_agent_with_queue("doc", doc_agent))
builder.add_node("deployment", wrap_agent_with_queue("deployment", deployment_agent))

# ─── Define workflow edges ────────────────────────────────────────────────────
builder.set_entry_point("pm")
builder.add_edge("pm", "architect")
builder.add_edge("architect", "approval_gate")

# Conditional fan-out or loopback from approval gate
builder.add_conditional_edges(
    "approval_gate",
    route_approval,
    {
        "pm": "pm",
        "database_designer": "database_designer",
        "backend": "backend",
        "frontend": "frontend"
    }
)

# Join parallel branches at reviewer
builder.add_edge("database_designer", "reviewer")
builder.add_edge("backend", "reviewer")
builder.add_edge("frontend", "reviewer")

# Sequential verification flow
builder.add_edge("reviewer", "security")
builder.add_edge("security", "testing")
builder.add_edge("testing", "bugfix")

# Self-correction loop or proceed
builder.add_conditional_edges(
    "bugfix",
    route_bugfix_loop,
    {
        "reviewer": "reviewer",
        "doc": "doc"
    }
)

# Finalize deployment
builder.add_edge("doc", "deployment")
builder.add_edge("deployment", END)

# Compile the graph with MemorySaver checkpointer and human-in-the-loop interrupts
memory = MemorySaver()
graph = builder.compile(
    checkpointer=memory,
    interrupt_before=["approval_gate", "database_designer", "deployment"]
)

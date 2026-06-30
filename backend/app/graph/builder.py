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


# ─── Build the LangGraph ────────────────────────────────────────────────────
builder = StateGraph(ProjectState)

# Register nodes
builder.add_node("pm", pm_agent)
builder.add_node("architect", architect_agent)
builder.add_node("database_designer", database_designer_agent)
builder.add_node("backend", backend_agent)
builder.add_node("frontend", frontend_agent)
builder.add_node("reviewer", reviewer_agent)
builder.add_node("security", security_agent)
builder.add_node("testing", testing_agent)
builder.add_node("bugfix", bugfix_agent)
builder.add_node("doc", doc_agent)
builder.add_node("deployment", deployment_agent)

# ─── Define workflow edges ────────────────────────────────────────────────────
# Start with Product Manager, then proceed to Architect
builder.set_entry_point("pm")
builder.add_edge("pm", "architect")

# Parallel branching after Architect: Database, Backend, and Frontend run in parallel
builder.add_edge("architect", "database_designer")
builder.add_edge("architect", "backend")
builder.add_edge("architect", "frontend")

# All three parallel branches join at the Reviewer
builder.add_edge("database_designer", "reviewer")
builder.add_edge("backend", "reviewer")
builder.add_edge("frontend", "reviewer")

# Sequential flow for analysis and verification after Reviewer
builder.add_edge("reviewer", "security")
builder.add_edge("security", "testing")

# Bugfix uses review + security findings
builder.add_edge("testing", "bugfix")

# Documentation and Deployment finalize the workflow
builder.add_edge("bugfix", "doc")
builder.add_edge("doc", "deployment")
builder.add_edge("deployment", END)

# Compile the graph with MemorySaver checkpointer
memory = MemorySaver()
graph = builder.compile(checkpointer=memory)

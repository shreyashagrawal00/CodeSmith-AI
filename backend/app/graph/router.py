"""
Placeholder for conditional routing logic.
Can be used to branch the graph based on review approval or security risk level.
"""
from app.graph.state import ProjectState


def should_bugfix(state: ProjectState) -> str:
    """Route to bugfix if reviewer found issues, else skip to doc."""
    review = state.get("review_report", {})
    approved = review.get("approved", True)
    if not approved:
        return "bugfix"
    return "doc"


def should_re_review(state: ProjectState) -> str:
    """After bugfix, always go to doc."""
    return "doc"

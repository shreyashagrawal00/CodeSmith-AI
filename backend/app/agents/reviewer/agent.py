import asyncio
from app.core.base_llm_agent import BaseLLMAgent
from app.llms.router import LLMRouter
from app.agents.reviewer.prompt import REVIEW_PROMPT
from app.schemas import ReviewReport
from app.graph.state import ProjectState


class ReviewerAgent(BaseLLMAgent):
    def __init__(self):
        super().__init__(LLMRouter.get_fallback_chain_for_agent("reviewer"))

    def run(self, state: ProjectState) -> dict:
        self._emit(state, "info", "🔍 Reviewing code quality", "Checking backend + frontend")
        response = self.retry(
            self.invoke,
            retries=3, backoff=1.0,
            prompt=REVIEW_PROMPT,
            schema=ReviewReport,
            inputs={
                "backend_code": str(state.get("backend_code", {})),
                "frontend_code": str(state.get("frontend_code", {})),
            },
            state=state,
        )
        approved = response.approved and (response.quality_score >= 80.0)
        verdict = "approved ✅" if approved else "needs fixes ⚠️"
        self._emit(state, "success" if approved else "warning", f"Review complete — {verdict}", f"Quality Score: {response.quality_score} | {response.overall_quality[:80]}")
        return {
            "review_report": response.model_dump(),
            "quality_score": response.quality_score,
            "review_approved": approved,
            "current_agent": "Reviewer",
            "log": [{"agent": "Reviewer", "status": "completed"}],
            "live_log": state.pop("live_log", []),
        }


async def reviewer_agent(state: ProjectState) -> dict:
    return await asyncio.to_thread(ReviewerAgent().run, state)

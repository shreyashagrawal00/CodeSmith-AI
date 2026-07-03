import asyncio
from app.core.base_llm_agent import BaseLLMAgent
from app.llms.router import LLMRouter
from app.agents.bugfix.prompt import BUGFIX_PROMPT
from app.schemas import BugfixReport
from app.graph.state import ProjectState


class BugfixAgent(BaseLLMAgent):
    def __init__(self):
        super().__init__(LLMRouter.get_fallback_chain_for_agent("bugfix"))

    def run(self, state: ProjectState) -> dict:
        review = state.get("review_report", {})
        security = state.get("security_report", {})
        total_issues = len(review.get("backend_issues", [])) + len(review.get("frontend_issues", [])) + len(security.get("vulnerabilities", []))
        self._emit(state, "info", "🐛 Applying bug fixes", f"{total_issues} issues to patch")
        response = self.invoke(
            prompt=BUGFIX_PROMPT,
            schema=BugfixReport,
            inputs={
                "review_issues": str(review.get("backend_issues", []) + review.get("frontend_issues", [])),
                "security_issues": str(security.get("vulnerabilities", [])),
                "backend_code": str(state.get("backend_code", {})),
                "frontend_code": str(state.get("frontend_code", {})),
            },
            state=state,
        )
        self._emit(state, "success", f"✅ Bugfix complete", f"{len(response.bugs_found)} bugs fixed | {len(response.changes_summary)} changes")
        
        # Merge fixed code back into state dictionaries
        backend_code = state.get("backend_code", {}).copy()
        if response.fixed_backend_files:
            for k, v in response.fixed_backend_files.items():
                backend_code[k] = v
            
        frontend_code = state.get("frontend_code", {}).copy()
        if response.fixed_frontend_files:
            for k, v in response.fixed_frontend_files.items():
                if k in frontend_code.get("components_code", {}):
                    frontend_code["components_code"][k] = v
                else:
                    frontend_code[k] = v

        new_iterations = state.get("correction_iterations", 0) + 1
        
        return {
            "bugfix_report": response.model_dump(),
            "backend_code": backend_code,
            "frontend_code": frontend_code,
            "correction_iterations": new_iterations,
            "current_agent": "BugFixer",
            "log": [{"agent": "BugFixer", "status": "completed"}],
            "live_log": [],
        }


async def bugfix_agent(state: ProjectState) -> dict:
    return await asyncio.to_thread(BugfixAgent().run, state)
import asyncio
import logging
from app.core.base_llm_agent import BaseLLMAgent
from app.llms.router import LLMRouter
from app.agents.reviewer.prompt import REVIEW_PROMPT
from app.schemas import ReviewReport
from app.graph.state import ProjectState

logger = logging.getLogger(__name__)


class ReviewerAgent(BaseLLMAgent):
    def __init__(self):
        super().__init__(LLMRouter.get_fallback_chain_for_agent("reviewer"))

    def run(self, state: ProjectState) -> dict:
        skip_result = self.skip_check(state, "Reviewer")
        if skip_result is not None:
            return skip_result

        job_id = state.get("job_id")
        compilation_errors_text = "None detected."
        frontend_build_err = ""
        backend_build_err = ""

        if job_id:
            self._emit(state, "info", "🔍 Running build compilation check...", "Compiling backend + frontend assets")
            try:
                from app.services.project_service import write_project_files, validate_project_build
                # Temporarily write files
                project_dir = write_project_files(job_id, state)
                # Check build
                validation = validate_project_build(job_id, project_dir)
                frontend_build_err = validation.get("frontend_errors", "")
                backend_build_err = validation.get("backend_errors", "")
                if frontend_build_err or backend_build_err:
                    compilation_errors_text = ""
                    if frontend_build_err:
                        compilation_errors_text += f"FRONTEND COMPILATION/BUILD ERRORS:\n{frontend_build_err}\n\n"
                    if backend_build_err:
                        compilation_errors_text += f"BACKEND SYNTAX/COMPILE ERRORS:\n{backend_build_err}\n"
                    self._emit(state, "warning", "⚠️ Build compilation failed", "passing errors to bugfix loop")
                else:
                    self._emit(state, "success", "✅ Code compiles successfully", "no syntax or import errors detected")
            except Exception as val_err:
                logger.exception("Failed to run build compilation validation")
                compilation_errors_text = f"Validation framework error: {str(val_err)}"

        self._emit(state, "info", "🔍 Reviewing code quality", "Checking backend + frontend")
        response = self.invoke(
            prompt=REVIEW_PROMPT,
            schema=ReviewReport,
            inputs={
                "backend_code": str(state.get("backend_code", {})),
                "frontend_code": str(state.get("frontend_code", {})),
                "compilation_errors": compilation_errors_text,
            },
            state=state,
        )

        approved = response.approved and (response.quality_score >= 80.0)
        quality_score = response.quality_score

        backend_issues = list(response.backend_issues or [])
        frontend_issues = list(response.frontend_issues or [])

        if backend_build_err:
            approved = False
            quality_score = min(quality_score, 45.0)
            backend_issues.append(f"COMPILER ERROR: {backend_build_err}")

        if frontend_build_err:
            approved = False
            quality_score = min(quality_score, 45.0)
            frontend_issues.append(f"COMPILER ERROR: {frontend_build_err}")

        # Update the response model values
        response.approved = approved
        response.quality_score = quality_score
        response.backend_issues = backend_issues
        response.frontend_issues = frontend_issues

        verdict = "approved ✅" if approved else "needs fixes ⚠️"
        self._emit(state, "success" if approved else "warning", f"Review complete — {verdict}", f"Quality Score: {quality_score} | {response.overall_quality[:80]}")
        return {
            "review_report": response.model_dump(),
            "quality_score": quality_score,
            "review_approved": approved,
            "compilation_errors": compilation_errors_text,
            "current_agent": "Reviewer",
            "log": [{"agent": "Reviewer", "status": "completed"}],
            "live_log": [],
        }


async def reviewer_agent(state: ProjectState) -> dict:
    return await asyncio.to_thread(ReviewerAgent().run, state)
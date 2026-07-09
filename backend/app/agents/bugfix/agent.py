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
        skip_result = self.skip_check(state, "BugFixer")
        if skip_result is not None:
            return skip_result
        review = state.get("review_report", {})
        security = state.get("security_report", {})
        compilation_errors = state.get("compilation_errors", "None.")
        total_issues = len(review.get("backend_issues", [])) + len(review.get("frontend_issues", [])) + len(security.get("vulnerabilities", []))
        self._emit(state, "info", "🐛 Applying bug fixes", f"{total_issues} issues to patch")
        response = self.invoke(
            prompt=BUGFIX_PROMPT,
            schema=BugfixReport,
            inputs={
                "review_issues": str(review.get("backend_issues", []) + review.get("frontend_issues", [])),
                "security_issues": str(security.get("vulnerabilities", [])),
                "compilation_errors": compilation_errors,
                "backend_code": str(state.get("backend_code", {})),
                "frontend_code": str(state.get("frontend_code", {})),
            },
            state=state,
        )
        self._emit(state, "success", f"✅ Bugfix complete", f"{len(response.bugs_found)} bugs fixed | {len(response.changes_summary)} changes")
        
        # Merge fixed code back into state dictionaries.
        # response.fixed_backend_files / fixed_frontend_files are now
        # List[FileEdit] (key + content pairs) instead of a raw dict --
        # see schemas/__init__.py for why (strict structured-output
        # schema compatibility).
        backend_code = state.get("backend_code", {}).copy()
        for edit in response.fixed_backend_files:
            # Check if this key matches a path in extra_files first
            extra_files = list(backend_code.get("extra_files") or [])
            matched_extra = False
            for i, extra in enumerate(extra_files):
                extra_path = extra.get("path") if isinstance(extra, dict) else getattr(extra, "path", None)
                if extra_path == edit.key:
                    if isinstance(extra, dict):
                        extra_files[i] = {"path": edit.key, "code": edit.content}
                    else:
                        extra.code = edit.content
                    matched_extra = True
                    break
            if matched_extra:
                backend_code["extra_files"] = extra_files
            else:
                # Core field (main_file, models_code, routes_code, etc.)
                backend_code[edit.key] = edit.content

        frontend_code = state.get("frontend_code", {}).copy()
        components_code = list(frontend_code.get("components_code") or [])
        for edit in response.fixed_frontend_files:
            # Check whether this key refers to an existing component
            # filename first; if so, patch that component's code in place.
            matched_component = False
            for component in components_code:
                if isinstance(component, dict) and component.get("filename") == edit.key:
                    component["code"] = edit.content
                    matched_component = True
                    break
            if not matched_component:
                frontend_code[edit.key] = edit.content
        frontend_code["components_code"] = components_code

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
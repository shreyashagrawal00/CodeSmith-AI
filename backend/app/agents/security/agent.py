import asyncio
from app.core.base_llm_agent import BaseLLMAgent
from app.llms.router import LLMRouter
from app.agents.security.prompt import SECURITY_PROMPT
from app.schemas import SecurityReport
from app.graph.state import ProjectState


class SecurityAgent(BaseLLMAgent):
    def __init__(self):
        super().__init__(LLMRouter.get_fallback_chain_for_agent("security"))

    def run(self, state: ProjectState) -> dict:
        skip_result = self.skip_check(state, "SecurityExpert")
        if skip_result is not None:
            return skip_result
        self._emit(state, "info", "🔒 Running security audit", "OWASP checklist, SQL injection, JWT, XSS")
        response = self.invoke(
            prompt=SECURITY_PROMPT,
            schema=SecurityReport,
            inputs={
                "backend_code": str(state.get("backend_code", {})),
                "frontend_code": str(state.get("frontend_code", {})),
                "database_schema": str(state.get("database_schema", {})),
            },
            state=state,
        )
        verdict = "secure ✅" if response.is_secure else "vulnerabilities found ⚠️"
        self._emit(state, "success" if response.is_secure else "warning",
                   f"Security audit done — {verdict}",
                   f"Risk: {response.risk_level} | {len(response.vulnerabilities)} vulnerabilities")
        return {
            "security_report": response.model_dump(),
            "current_agent": "SecurityExpert",
            "log": [{"agent": "SecurityExpert", "status": "completed"}],
            "live_log": [],
        }


async def security_agent(state: ProjectState) -> dict:
    return await asyncio.to_thread(SecurityAgent().run, state)
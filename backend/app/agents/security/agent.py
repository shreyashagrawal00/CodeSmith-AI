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
        backend_data = state.get("backend_code", {})
        frontend_data = state.get("frontend_code", {})

        backend_parts = []
        for k in ["routes_code", "models_code", "main_file", "services_code"]:
            if backend_data.get(k):
                backend_parts.append(f"### {k}:\n{str(backend_data[k])[:2000]}")
        backend_repr = "\n\n".join(backend_parts) if backend_parts else str(backend_data)[:3000]

        frontend_parts = []
        if frontend_data.get("main_app_code"):
            frontend_parts.append(f"### Main App ({frontend_data.get('main_app_file_name', 'App.jsx')}):\n{str(frontend_data['main_app_code'])[:2000]}")
        for c in (frontend_data.get("components_code") or [])[:3]:
            if isinstance(c, dict):
                frontend_parts.append(f"### Component {c.get('filename', '')}:\n{str(c.get('code', ''))[:1500]}")
        frontend_repr = "\n\n".join(frontend_parts) if frontend_parts else str(frontend_data)[:3000]

        response = self.invoke(
            prompt=SECURITY_PROMPT,
            schema=SecurityReport,
            inputs={
                "backend_code": backend_repr,
                "frontend_code": frontend_repr,
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
import asyncio
from app.core.base_llm_agent import BaseLLMAgent
from app.llms.router import LLMRouter
from app.agents.backend.prompt import BACKEND_PROMPT
from app.schemas import BackendCode
from app.graph.state import ProjectState


class BackendAgent(BaseLLMAgent):
    def __init__(self):
        super().__init__(LLMRouter.get_fallback_chain_for_agent("backend"))

    def run(self, state: ProjectState) -> dict:
        arch = state["architecture"]
        db = state["database_schema"]
        self._emit(state, "info", "⚙️ Generating backend code", f"Framework: {', '.join(arch.get('tech_stack', []))[:60]}")
        response = self.retry(
            self.invoke,
            retries=3, backoff=1.0,
            prompt=BACKEND_PROMPT,
            schema=BackendCode,
            inputs={
                "system_design": arch.get("system_design", ""),
                "tech_stack": ", ".join(arch.get("tech_stack", [])),
                "tables": str(db.get("tables", [])),
                "api_design": arch.get("api_design", ""),
            },
            state=state,
        )
        self._emit(state, "success", f"✅ Backend generated ({response.framework})", "main.py, models, routes, services, Dockerfile")
        return {
            "backend_code": response.model_dump(),
            "log": [{"agent": "BackendEngineer", "status": "completed"}],
            "live_log": [],
        }


async def backend_agent(state: ProjectState) -> dict:
    return await asyncio.to_thread(BackendAgent().run, state)

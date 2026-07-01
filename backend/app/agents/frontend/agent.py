import asyncio
from app.core.base_llm_agent import BaseLLMAgent
from app.llms.router import LLMRouter
from app.agents.frontend.prompt import FRONTEND_PROMPT
from app.schemas import FrontendCode
from app.graph.state import ProjectState


class FrontendAgent(BaseLLMAgent):
    def __init__(self):
        super().__init__(LLMRouter.get_fallback_chain_for_agent("frontend"))

    def run(self, state: ProjectState) -> dict:
        arch = state["architecture"]
        req = state["requirements"]
        self._emit(state, "info", "🎨 Generating frontend UI", f"{len(req.get('features', []))} features to implement")
        response = self.retry(
            self.invoke,
            retries=3, backoff=1.0,
            prompt=FRONTEND_PROMPT,
            schema=FrontendCode,
            inputs={
                "system_design": arch.get("system_design", ""),
                "tech_stack": ", ".join(arch.get("tech_stack", [])),
                "api_design": arch.get("api_design", ""),
                "features": ", ".join(req.get("features", [])),
            },
            state=state,
        )
        self._emit(state, "success", f"✅ Frontend generated ({response.framework})", f"{len(response.components_code)} components, App.jsx, api.js, styles")
        return {
            "frontend_code": response.model_dump(),
            "log": [{"agent": "FrontendEngineer", "status": "completed"}],
            "live_log": [],
        }


async def frontend_agent(state: ProjectState) -> dict:
    return await asyncio.to_thread(FrontendAgent().run, state)

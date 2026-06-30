import asyncio
from app.core.base_llm_agent import BaseLLMAgent
from app.llms.router import LLMRouter
from app.agents.architect.prompt import ARCHITECT_PROMPT
from app.schemas import ArchitectOutput
from app.graph.state import ProjectState


class ArchitectAgent(BaseLLMAgent):
    def __init__(self):
        super().__init__(LLMRouter.get_fallback_chain_for_agent("architect"))

    def run(self, state: ProjectState) -> dict:
        req = state["requirements"]
        self._emit(state, "info", "🏗️ Designing system architecture", req.get("project_name", ""))
        response = self.retry(
            self.invoke,
            retries=3, backoff=1.0,
            prompt=ARCHITECT_PROMPT,
            schema=ArchitectOutput,
            inputs={
                "project_name": req.get("project_name", ""),
                "description": req.get("description", ""),
                "features": ", ".join(req.get("features", [])),
                "tech_stack": ", ".join(req.get("tech_stack", [])),
            },
            state=state,
        )
        self._emit(state, "success", f"✅ Architecture ready", f"{len(response.components)} components defined")
        return {
            "architecture": response.model_dump(),
            "current_agent": "Architect",
            "log": [{"agent": "Architect", "status": "completed"}],
            "live_log": state.pop("live_log", []),
        }


async def architect_agent(state: ProjectState) -> dict:
    return await asyncio.to_thread(ArchitectAgent().run, state)

import asyncio
from app.core.base_llm_agent import BaseLLMAgent
from app.llms.router import LLMRouter
from app.agents.pm.prompt import PM_PROMPT
from app.schemas import PMOutput
from app.graph.state import ProjectState


class PMAgent(BaseLLMAgent):
    def __init__(self):
        super().__init__(LLMRouter.get_fallback_chain_for_agent("pm"))

    def run(self, state: ProjectState) -> dict:
        self._emit(state, "info", "📋 Starting requirements analysis", state.get("user_prompt", "")[:80])
        response = self.retry(
            self.invoke,
            retries=3, backoff=1.0,
            prompt=PM_PROMPT,
            schema=PMOutput,
            inputs={"user_prompt": state["user_prompt"]},
            state=state,
        )
        self._emit(state, "success", f"✅ Requirements complete: {response.project_name}", f"{len(response.features)} features identified")
        return {
            "requirements": response.model_dump(),
            "current_agent": "PM",
            "log": [{"agent": "PM", "status": "completed"}],
            "live_log": [],
        }


async def pm_agent(state: ProjectState) -> dict:
    return await asyncio.to_thread(PMAgent().run, state)

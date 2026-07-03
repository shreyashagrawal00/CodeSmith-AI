import asyncio
from app.core.base_llm_agent import BaseLLMAgent
from app.llms.router import LLMRouter
from app.agents.doc.prompt import DOCUMENTATION_PROMPT
from app.schemas import Documentation
from app.graph.state import ProjectState


class DocAgent(BaseLLMAgent):
    def __init__(self):
        super().__init__(LLMRouter.get_fallback_chain_for_agent("doc"))

    def run(self, state: ProjectState) -> dict:
        req = state.get("requirements", {})
        arch = state.get("architecture", {})
        self._emit(state, "info", "📝 Writing documentation", f"README, API docs, architecture guide, setup guide")
        response = self.invoke(
            prompt=DOCUMENTATION_PROMPT,
            schema=Documentation,
            inputs={
                "project_name": req.get("project_name", ""),
                "description": req.get("description", ""),
                "architecture": arch.get("system_design", ""),
                "api_design": arch.get("api_design", ""),
                "tech_stack": ", ".join(arch.get("tech_stack", [])),
            },
            state=state,
        )
        self._emit(state, "success", "✅ Documentation ready", "README.md, api.md, architecture.md, setup.md")
        return {
            "documentation": response.model_dump(),
            "current_agent": "TechWriter",
            "log": [{"agent": "TechWriter", "status": "completed"}],
            "live_log": [],
        }


async def doc_agent(state: ProjectState) -> dict:
    return await asyncio.to_thread(DocAgent().run, state)
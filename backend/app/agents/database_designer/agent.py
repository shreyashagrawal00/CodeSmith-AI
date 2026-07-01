import asyncio
from app.core.base_llm_agent import BaseLLMAgent
from app.llms.router import LLMRouter
from app.agents.database_designer.prompt import DATABASE_PROMPT
from app.schemas import DatabaseSchema
from app.graph.state import ProjectState


class DatabaseDesignerAgent(BaseLLMAgent):
    def __init__(self):
        super().__init__(LLMRouter.get_fallback_chain_for_agent("database_designer"))

    def run(self, state: ProjectState) -> dict:
        arch = state["architecture"]
        self._emit(state, "info", "🗄️ Designing database schema", f"{len(arch.get('components', []))} components to model")
        response = self.retry(
            self.invoke,
            retries=3, backoff=1.0,
            prompt=DATABASE_PROMPT,
            schema=DatabaseSchema,
            inputs={
                "system_design": arch.get("system_design", ""),
                "components": ", ".join(arch.get("components", [])),
            },
            state=state,
        )
        self._emit(state, "success", f"✅ Schema ready ({response.database_type})", f"{len(response.tables)} tables, {len(response.indexes)} indexes")
        return {
            "database_schema": response.model_dump(),
            "log": [{"agent": "DatabaseDesigner", "status": "completed"}],
            "live_log": [],
        }


async def database_designer_agent(state: ProjectState) -> dict:
    return await asyncio.to_thread(DatabaseDesignerAgent().run, state)

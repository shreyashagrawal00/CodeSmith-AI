import asyncio
from app.core.base_llm_agent import BaseLLMAgent
from app.llms.router import LLMRouter
from app.agents.deployment.prompt import DEPLOYMENT_PROMPT
from app.schemas import DeploymentConfig
from app.graph.state import ProjectState


class DeploymentAgent(BaseLLMAgent):
    def __init__(self):
        super().__init__(LLMRouter.get_fallback_chain_for_agent("deployment"))

    def run(self, state: ProjectState) -> dict:
        skip_result = self.skip_check(state, "DevOps")
        if skip_result is not None:
            return skip_result
        req = state.get("requirements", {})
        arch = state.get("architecture", {})
        db = state.get("database_schema", {})
        self._emit(state, "info", "🚀 Generating deployment config", "Docker Compose, NGINX, CI/CD, .env")
        response = self.invoke(
            prompt=DEPLOYMENT_PROMPT,
            schema=DeploymentConfig,
            inputs={
                "project_name": req.get("project_name", ""),
                "tech_stack": ", ".join(arch.get("tech_stack", [])),
                "components": ", ".join(arch.get("components", [])),
                "database_type": db.get("database_type", "PostgreSQL"),
            },
            state=state,
        )
        self._emit(state, "success", "✅ Deployment config ready", "docker-compose.yml, nginx.conf, .env.example, CI/CD pipeline")
        return {
            "deployment": response.model_dump(),
            "current_agent": "DevOps",
            "status": "completed",
            "log": [{"agent": "DevOps", "status": "completed"}],
            "live_log": [],
        }


async def deployment_agent(state: ProjectState) -> dict:
    return await asyncio.to_thread(DeploymentAgent().run, state)
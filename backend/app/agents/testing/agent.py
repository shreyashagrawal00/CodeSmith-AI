import asyncio
from app.core.base_llm_agent import BaseLLMAgent
from app.llms.router import LLMRouter
from app.agents.testing.prompt import TESTING_PROMPT
from app.schemas import TestingReport
from app.graph.state import ProjectState


class TestingAgent(BaseLLMAgent):
    def __init__(self):
        super().__init__(LLMRouter.get_fallback_chain_for_agent("testing"))

    def run(self, state: ProjectState) -> dict:
        skip_result = self.skip_check(state, "QAEngineer")
        if skip_result is not None:
            return skip_result
        arch = state.get("architecture", {})
        self._emit(state, "info", "🧪 Generating test suite", "Unit tests + integration tests")
        response = self.invoke(
            prompt=TESTING_PROMPT,
            schema=TestingReport,
            inputs={
                "backend_code": str(state.get("backend_code", {})),
                "frontend_code": str(state.get("frontend_code", {})),
                "api_design": arch.get("api_design", ""),
            },
            state=state,
        )
        self._emit(state, "success", f"✅ Tests generated", f"Coverage estimate: {response.test_coverage_estimate} | {len(response.test_cases)} test cases")
        return {
            "testing_report": response.model_dump(),
            "current_agent": "QAEngineer",
            "log": [{"agent": "QAEngineer", "status": "completed"}],
            "live_log": [],
        }


async def testing_agent(state: ProjectState) -> dict:
    return await asyncio.to_thread(TestingAgent().run, state)
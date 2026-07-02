"""BaseLLMAgent — base class for every AI-powered agent.

Rules enforced here:
- Only this class may call ``llm.invoke()`` (via the ``invoke`` helper).
- All child agents must implement ``run(state) -> ProjectState``.
- Retry, timing, and logging are inherited from BaseAgent.
"""
from abc import abstractmethod
from typing import Type, List
import logging
import time

from pydantic import BaseModel

from app.core.base_agent import BaseAgent
from app.guardrails.validators import validate_output

logger = logging.getLogger(__name__)


class BaseLLMAgent(BaseAgent):
    """Base class for all LLM-powered agents."""

    def __init__(self, llms):
        super().__init__(state=None)
        self.llms = llms if isinstance(llms, list) else [llms]

    def _emit(self, state: dict, event_type: str, message: str, detail: str = ""):
        """Append a structured live log entry to state['live_log']."""
        entry = {
            "agent": self.name,
            "type": event_type,   # "info" | "success" | "warning" | "error"
            "message": message,
            "detail": detail,
        }
        if "live_log" not in state or state["live_log"] is None:
            state["live_log"] = []
        state["live_log"].append(entry)
        logger.info("[%s] %s — %s", self.name, message, detail)

    def invoke(
        self,
        prompt,
        schema: Type[BaseModel],
        inputs: dict,
        state: dict = None,
    ):
        """Execute the prompt chain across the fallback LLM chain.

        Validates against guardrails and emits live log events into state.
        """
        last_exc = None
        for idx, llm in enumerate(self.llms):
            provider_name = type(llm).__name__.replace("Chat", "").replace("GoogleGenerativeAI", "Gemini")
            try:
                if state is not None:
                    self._emit(state, "info",
                               f"🤖 Calling {provider_name}",
                               f"attempt {idx + 1}/{len(self.llms)}")

                t0 = time.time()
                structured_llm = llm.with_structured_output(schema)
                chain = prompt | structured_llm
                response = chain.invoke(inputs)
                elapsed = round(time.time() - t0, 1)

                if response is None:
                    raise ValueError(f"Received empty response from {provider_name}")

                data = response.model_dump()

                # Pydantic schema check
                validate_output(data, schema)

                # Empty field check (strings only + critical lists).
                # A field is only flagged as "empty" if the schema doesn't
                # already allow "" as a legitimate default (e.g.
                # TestingReport.frontend_tests_code is optional and blank
                # for backend-only projects — that's a valid response, not
                # a failure).
                model_fields = schema.model_fields
                for field, val in data.items():
                    field_info = model_fields.get(field)
                    allows_blank_string = (
                        field_info is not None and field_info.default == ""
                    )
                    if val is None or (val == "" and not allows_blank_string):
                        raise ValueError(f"Required field '{field}' is empty.")
                    if field in ("features", "tech_stack", "components", "tables") \
                            and isinstance(val, list) and len(val) == 0:
                        raise ValueError(f"Collection field '{field}' must not be empty.")

                # Placeholder check
                for field, val in data.items():
                    if isinstance(val, str):
                        v = val.lower()
                        if "[placeholder]" in v or "todo:" in v or "fixme:" in v or "<insert" in v:
                            raise ValueError(f"Field '{field}' has unresolved placeholder.")

                if state is not None:
                    self._emit(state, "success",
                               f"✅ {provider_name} responded in {elapsed}s",
                               f"guardrails passed")
                logger.info("Guardrails passed for %s via %s", self.name, provider_name)
                return response

            except Exception as e:
                if state is not None:
                    self._emit(state, "warning",
                               f"⚠️ {provider_name} failed",
                               str(e)[:120])
                logger.warning("Provider %s failed for %s: %s", provider_name, self.name, e)
                last_exc = e

        if state is not None:
            self._emit(state, "error",
                       f"❌ All providers exhausted for {self.name}",
                       str(last_exc)[:120])
        raise last_exc

    @abstractmethod
    def run(self, state):
        pass
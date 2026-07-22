"""BaseLLMAgent — base class for every AI-powered agent.

Rules enforced here:
- Only this class may call ``llm.invoke()`` (via the ``invoke`` helper).
- All child agents must implement ``run(state) -> ProjectState``.
- Retry, timing, and logging are inherited from BaseAgent.
"""
from abc import abstractmethod
from typing import Type, List
import logging
import re
import time

from pydantic import BaseModel

from app.core.base_agent import BaseAgent
from app.guardrails.validators import validate_output

logger = logging.getLogger(__name__)

# Cap how long we'll ever sleep for a single rate-limit retry, even if a
# provider asks for longer — we'd rather fall through to the next provider
# in the chain than block the whole workflow for minutes.
_MAX_RATE_LIMIT_WAIT_SECS = 45


def _extract_retry_after_seconds(exc: Exception) -> float | None:
    """Best-effort extraction of a suggested wait time from a provider error.

    Providers surface this differently — OpenRouter/Groq/Mistral errors may
    include an HTTP ``Retry-After`` header, or (as with OpenRouter) embed a
    ``retry_after_seconds`` field in the JSON error body. We don't have a
    single typed exception across providers here, so we fall back to
    string-matching the error text, which is what's actually available.
    """
    text = str(exc)
    for pattern in (
        r"retry_after_seconds['\"]?\s*[:=]\s*([\d.]+)",
        r"Retry-After['\"]?\s*[:=]\s*([\d.]+)",
    ):
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass
    return None


def _is_rate_limit_error(exc: Exception) -> bool:
    text = str(exc).lower()
    return "429" in text or "rate-limit" in text or "rate limit" in text or "too many requests" in text


def _friendly_provider_name(llm) -> str:
    """Human-readable provider name for live-log display.

    OpenRouter, Cerebras, and NVIDIA NIM are all implemented with
    langchain_openai.ChatOpenAI (they're just OpenAI-API-compatible), so a
    naive class-name lookup mislabels any of them as "OpenAI" in the logs
    -- which is actively misleading, since we never configure a real
    OpenAI key here. Detect the actual provider via the base_url instead.
    """
    base_url = str(getattr(llm, "openai_api_base", "") or "").lower()
    if "openrouter" in base_url:
        return "OpenRouter"
    if "cerebras" in base_url:
        return "Cerebras"
    if "nvidia" in base_url:
        return "NVIDIA NIM"
    return type(llm).__name__.replace("Chat", "").replace("GoogleGenerativeAI", "Gemini")


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

    def skip_check(self, state: dict, agent_id: str) -> dict | None:
        """Check whether the user requested this agent be skipped.

        agent_id must match the id used by the frontend's orchestration
        grid and the "agent" field in job.log entries (e.g. "PM",
        "Architect", "DatabaseDesigner", ...) -- see
        frontend/src/components/ProgressBar.jsx's AGENT_ROLES.

        IMPORTANT: this reads workflow_service._jobs[job_id] directly
        (the live in-memory job dict), NOT state.get("skip_agents").
        A continuous graph.astream() call does not re-check external
        graph.aupdate_state() changes mid-run -- verified empirically: a
        later node in the same astream() call still saw the pre-injection
        value even after aupdate_state() completed between steps. Since
        the whole app runs as a single process, reading the shared
        in-memory dict directly is both simpler and actually correct.

        Returns a ready-to-return state update dict if skipped (caller
        should return it immediately without calling any LLM), or None if
        the agent should run normally. The skipped section's output key is
        deliberately left untouched -- it stays at its existing default
        ({}), and downstream agents already treat missing/empty sections
        defensively via .get(..., default).
        """
        job_id = state.get("job_id")
        skip_list: list = []
        if job_id:
            # Lazy import to avoid a circular import: workflow_service
            # imports the graph (and therefore every agent, and therefore
            # this module) at module load time.
            from app.services.workflow_service import _jobs
            job = _jobs.get(job_id)
            if job:
                skip_list = job.get("skip_agents") or []

        if agent_id in skip_list:
            self._emit(state, "warning",
                       f"⏭️ {agent_id} skipped by user",
                       "no LLM call made for this step")
            logger.info("%s skipped by user request", agent_id)
            return {
                "current_agent": agent_id,
                "log": [{"agent": agent_id, "status": "skipped"}],
                "live_log": [],
            }
        return None

    def invoke(
        self,
        prompt,
        schema: Type[BaseModel],
        inputs: dict,
        state: dict = None,
    ):
        """Execute the prompt chain across the fallback LLM chain.

        Validates against guardrails and emits live log events into state.
        Each provider gets one immediate attempt, and — if it fails with a
        rate-limit (429) error that includes a suggested wait time — one
        additional attempt after actually waiting that long, before moving
        on to the next provider in the chain.
        """
        last_exc = None
        for idx, llm in enumerate(self.llms):
            provider_name = _friendly_provider_name(llm)

            for rate_limit_attempt in range(2):  # 1 initial try + 1 retry-after-wait try
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
                        if field in ("features", "tech_stack", "components") \
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
                    last_exc = e

                    if rate_limit_attempt == 0 and _is_rate_limit_error(e):
                        wait_secs = _extract_retry_after_seconds(e)
                        if wait_secs is not None:
                            wait_secs = min(wait_secs, _MAX_RATE_LIMIT_WAIT_SECS)
                            if state is not None:
                                self._emit(state, "warning",
                                           f"⏳ {provider_name} rate-limited",
                                           f"waiting {wait_secs:.0f}s before retrying this provider")
                            logger.warning(
                                "%s rate-limited for %s, waiting %.0fs then retrying once",
                                provider_name, self.name, wait_secs,
                            )
                            time.sleep(wait_secs)
                            continue  # retry the same provider one more time

                    if state is not None:
                        self._emit(state, "warning",
                                   f"⚠️ {provider_name} failed",
                                   str(e)[:120])
                    logger.warning("Provider %s failed for %s: %s", provider_name, self.name, e)
                    break  # move on to the next provider in the chain

        if state is not None:
            self._emit(state, "error",
                       f"❌ All providers exhausted for {self.name}",
                       str(last_exc)[:120])
        raise last_exc

    @abstractmethod
    def run(self, state):
        pass
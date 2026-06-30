import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class BaseAgent(ABC):
    """Abstract base class for all agents.

    Provides common utilities like logging, retry logic, simple timing, and
    access to a shared mutable ``state`` dictionary that is passed between
    agents in the LangGraph workflow.
    """

    def __init__(self, state: dict | None = None):
        self.state = state or {}
        self.name = self.__class__.__name__
        logger.info("%s initialized with state keys: %s", self.name, list(self.state.keys()))

    @abstractmethod
    def run(self, *args, **kwargs) -> Any:
        """Execute the agent's primary logic.

        Sub‑classes must implement this method and return a structured result
        (usually a Pydantic model) that will be merged back into ``self.state``.
        """
        raise NotImplementedError

    def retry(self, func: Callable[..., Any], retries: int = 3, backoff: float = 1.0, *args, **kwargs) -> Any:
        """Execute ``func`` with simple exponential back‑off retry.

        Parameters
        ----------
        func: Callable
            The function to execute.
        retries: int
            Number of attempts (including the initial call).
        backoff: float
            Base back‑off in seconds; each retry waits ``backoff * 2**attempt``.
        """
        attempt = 0
        while attempt < retries:
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                attempt += 1
                if attempt >= retries:
                    logger.error("%s failed after %s attempts: %s", self.name, retries, exc)
                    raise
                sleep_time = backoff * (2 ** (attempt - 1))
                logger.warning("%s retry %s/%s after %s seconds due to %s", self.name, attempt, retries, sleep_time, exc)
                time.sleep(sleep_time)

    def timeit(self, func: Callable[..., Any], *args, **kwargs) -> tuple[Any, float]:
        """Run ``func`` and return a tuple of ``(result, elapsed_seconds)``.
        """
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        logger.info("%s completed in %.3f seconds", self.name, elapsed)
        return result, elapsed
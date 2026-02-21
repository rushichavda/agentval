"""Base adapter interface for framework integrations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Any, Generator

from ..types import Trace


class BaseAdapter(ABC):
    """Base class for framework adapters.

    Adapters translate framework-specific execution data into
    AgentVal's Trace format. Implement this to add support
    for a new agent framework.
    """

    @abstractmethod
    @contextmanager
    def capture(self, **kwargs: Any) -> Generator[Trace]:
        """Capture a trace from the framework's execution.

        Usage:
            adapter = MyFrameworkAdapter()
            with adapter.capture() as trace:
                result = run_my_agent(...)
            # trace is now populated with steps
        """
        ...

    @abstractmethod
    def parse_trace(self, raw_data: Any) -> Trace:
        """Parse framework-specific trace data into an AgentVal Trace.

        Use this when you already have trace data (e.g., from logs or
        an observability platform) and want to convert it.
        """
        ...

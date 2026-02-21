"""Trace capture utilities for recording agent execution."""

from __future__ import annotations

import functools
import time
from contextlib import contextmanager
from typing import Any, Callable, Generator

from .types import Step, StepStatus, StepType, Trace

# Thread-local-ish active trace stack (simple approach for MVP)
_active_traces: list[Trace] = []


def get_active_trace() -> Trace | None:
    """Get the currently active trace, if any."""
    return _active_traces[-1] if _active_traces else None


@contextmanager
def capture(name: str = "", metadata: dict[str, Any] | None = None) -> Generator[Trace]:
    """Context manager that captures an agent execution trace.

    Usage:
        with capture("my_agent_run") as trace:
            result = my_agent("what is python?")
        # trace now contains all recorded steps
    """
    trace = Trace(name=name, metadata=metadata or {})
    _active_traces.append(trace)
    try:
        yield trace
    finally:
        trace.end_time = time.time()
        _active_traces.pop()


def record_step(
    name: str,
    step_type: StepType = StepType.CUSTOM,
    input: dict[str, Any] | None = None,
    output: dict[str, Any] | None = None,
    status: StepStatus = StepStatus.SUCCESS,
    error: str | None = None,
    metadata: dict[str, Any] | None = None,
    parent_id: str | None = None,
) -> Step | None:
    """Record a step in the currently active trace.

    Returns the step if a trace is active, None otherwise.
    """
    trace = get_active_trace()
    if trace is None:
        return None

    step = Step(
        name=name,
        step_type=step_type,
        input=input or {},
        output=output or {},
        status=status,
        error=error,
        metadata=metadata or {},
        parent_id=parent_id,
    )
    trace.add_step(step)
    return step


def trace_tool(name: str | None = None) -> Callable:
    """Decorator that records a function call as a tool_call step.

    Usage:
        @trace_tool()
        def web_search(query: str) -> list[str]:
            return search(query)

        @trace_tool("custom_name")
        def my_func():
            ...
    """

    def decorator(func: Callable) -> Callable:
        tool_name = name or func.__name__

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            trace = get_active_trace()
            if trace is None:
                return func(*args, **kwargs)

            step = Step(
                name=tool_name,
                step_type=StepType.TOOL_CALL,
                input={"args": list(args), "kwargs": kwargs},
            )

            start = time.time()
            try:
                result = func(*args, **kwargs)
                step.output = {"result": result}
                step.status = StepStatus.SUCCESS
                return result
            except Exception as e:
                step.status = StepStatus.FAILED
                step.error = str(e)
                raise
            finally:
                step.duration_ms = (time.time() - start) * 1000
                trace.add_step(step)

        return wrapper

    return decorator


def trace_llm(name: str | None = None) -> Callable:
    """Decorator that records a function call as an llm_call step."""

    def decorator(func: Callable) -> Callable:
        llm_name = name or func.__name__

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            trace = get_active_trace()
            if trace is None:
                return func(*args, **kwargs)

            step = Step(
                name=llm_name,
                step_type=StepType.LLM_CALL,
                input={"args": list(args), "kwargs": kwargs},
            )

            start = time.time()
            try:
                result = func(*args, **kwargs)
                step.output = {"result": result}
                step.status = StepStatus.SUCCESS
                return result
            except Exception as e:
                step.status = StepStatus.FAILED
                step.error = str(e)
                raise
            finally:
                step.duration_ms = (time.time() - start) * 1000
                trace.add_step(step)

        return wrapper

    return decorator

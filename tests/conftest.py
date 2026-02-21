"""Shared test fixtures."""

import pytest

from agentprobe import Step, StepStatus, StepType, Trace


@pytest.fixture
def simple_trace() -> Trace:
    """A basic 3-step trace for testing."""
    trace = Trace(name="test_trace")
    trace.add_step(
        Step(
            name="web_search",
            step_type=StepType.TOOL_CALL,
            input={"kwargs": {"query": "python"}},
            output={"result": [{"title": "Python.org"}]},
        )
    )
    trace.add_step(
        Step(
            name="read_page",
            step_type=StepType.TOOL_CALL,
            input={"kwargs": {"url": "https://python.org"}},
            output={"result": "Python is a programming language"},
        )
    )
    trace.add_step(
        Step(
            name="summarize",
            step_type=StepType.LLM_CALL,
            input={"context": "Python is a programming language"},
            output={"result": "Python is a versatile programming language."},
        )
    )
    return trace


@pytest.fixture
def failing_trace() -> Trace:
    """A trace with a failure mid-way."""
    trace = Trace(name="failing_trace")
    trace.add_step(
        Step(
            name="search",
            step_type=StepType.TOOL_CALL,
            input={"kwargs": {"query": "test"}},
            output={"result": []},  # empty results — the root cause
        )
    )
    trace.add_step(
        Step(
            name="process",
            step_type=StepType.TOOL_CALL,
            input={"kwargs": {"data": []}},
            output={"result": None},  # null output propagated
        )
    )
    trace.add_step(
        Step(
            name="format",
            step_type=StepType.TOOL_CALL,
            input={"kwargs": {"data": None}},
            output={},
            status=StepStatus.FAILED,
            error="TypeError: Cannot format NoneType",
        )
    )
    return trace


@pytest.fixture
def empty_trace() -> Trace:
    return Trace(name="empty")

"""Tests for core data models."""

import tempfile
from pathlib import Path

from agentprobe import Step, StepStatus, StepType, Trace


class TestStep:
    def test_create_step(self):
        step = Step(name="search", step_type=StepType.TOOL_CALL)
        assert step.name == "search"
        assert step.step_type == StepType.TOOL_CALL
        assert step.status == StepStatus.SUCCESS
        assert step.succeeded
        assert not step.failed

    def test_failed_step(self):
        step = Step(
            name="search",
            step_type=StepType.TOOL_CALL,
            status=StepStatus.FAILED,
            error="Connection timeout",
        )
        assert step.failed
        assert not step.succeeded
        assert step.error == "Connection timeout"

    def test_to_dict_roundtrip(self):
        step = Step(
            name="search",
            step_type=StepType.TOOL_CALL,
            input={"query": "test"},
            output={"result": [1, 2, 3]},
        )
        d = step.to_dict()
        restored = Step.from_dict(d)
        assert restored.name == step.name
        assert restored.step_type == step.step_type
        assert restored.input == step.input
        assert restored.output == step.output


class TestTrace:
    def test_create_trace(self):
        trace = Trace(name="test")
        assert trace.name == "test"
        assert len(trace) == 0

    def test_add_steps(self, simple_trace):
        assert len(simple_trace) == 3
        assert simple_trace.step_names == ["web_search", "read_page", "summarize"]

    def test_find_step(self, simple_trace):
        step = simple_trace.find_step("web_search")
        assert step is not None
        assert step.name == "web_search"

    def test_find_step_not_found(self, simple_trace):
        assert simple_trace.find_step("nonexistent") is None

    def test_find_steps(self, simple_trace):
        steps = simple_trace.find_steps("read_page")
        assert len(steps) == 1

    def test_tool_calls(self, simple_trace):
        tools = simple_trace.tool_calls
        assert len(tools) == 2
        assert tools[0].name == "web_search"
        assert tools[1].name == "read_page"

    def test_llm_calls(self, simple_trace):
        llm = simple_trace.llm_calls
        assert len(llm) == 1
        assert llm[0].name == "summarize"

    def test_failed_steps(self, failing_trace):
        assert failing_trace.has_failures
        assert len(failing_trace.failed_steps) == 1
        assert failing_trace.failed_steps[0].name == "format"

    def test_json_roundtrip(self, simple_trace):
        json_str = simple_trace.to_json()
        restored = Trace.from_json(json_str)
        assert len(restored) == len(simple_trace)
        assert restored.step_names == simple_trace.step_names

    def test_file_roundtrip(self, simple_trace):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = Path(f.name)
        try:
            simple_trace.save(path)
            restored = Trace.from_file(path)
            assert len(restored) == len(simple_trace)
            assert restored.name == simple_trace.name
        finally:
            path.unlink()

    def test_iteration(self, simple_trace):
        names = [step.name for step in simple_trace]
        assert names == ["web_search", "read_page", "summarize"]

    def test_indexing(self, simple_trace):
        assert simple_trace[0].name == "web_search"
        assert simple_trace[2].name == "summarize"

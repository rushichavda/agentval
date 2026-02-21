"""Tests for trace capture utilities."""

import agentprobe as ap
from agentprobe import StepType


class TestCapture:
    def test_capture_context_manager(self):
        with ap.capture("test") as trace:
            assert trace.name == "test"
            assert len(trace) == 0
        assert trace.end_time is not None

    def test_capture_records_steps(self):
        with ap.capture("test") as trace:
            ap.record_step("step1", StepType.TOOL_CALL, output={"result": "ok"})
            ap.record_step("step2", StepType.LLM_CALL, output={"result": "done"})

        assert len(trace) == 2
        assert trace.step_names == ["step1", "step2"]

    def test_no_recording_outside_capture(self):
        result = ap.record_step("orphan", StepType.TOOL_CALL)
        assert result is None


class TestTraceToolDecorator:
    def test_trace_tool_records(self):
        @ap.trace_tool()
        def my_tool(x: int) -> int:
            return x * 2

        with ap.capture("test") as trace:
            result = my_tool(5)

        assert result == 10
        assert len(trace) == 1
        assert trace[0].name == "my_tool"
        assert trace[0].step_type == StepType.TOOL_CALL
        assert trace[0].output["result"] == 10

    def test_trace_tool_custom_name(self):
        @ap.trace_tool("custom_search")
        def search(q: str) -> list:
            return [q]

        with ap.capture("test") as trace:
            search("hello")

        assert trace[0].name == "custom_search"

    def test_trace_tool_records_failure(self):
        @ap.trace_tool()
        def bad_tool():
            raise ValueError("boom")

        with ap.capture("test") as trace:
            try:
                bad_tool()
            except ValueError:
                pass

        assert len(trace) == 1
        assert trace[0].failed
        assert trace[0].error == "boom"

    def test_trace_tool_works_without_capture(self):
        @ap.trace_tool()
        def standalone(x: int) -> int:
            return x + 1

        # Should work fine without a capture context
        assert standalone(5) == 6


class TestTraceLlmDecorator:
    def test_trace_llm_records(self):
        @ap.trace_llm()
        def my_llm(prompt: str) -> str:
            return f"response to {prompt}"

        with ap.capture("test") as trace:
            result = my_llm("hello")

        assert result == "response to hello"
        assert len(trace) == 1
        assert trace[0].step_type == StepType.LLM_CALL


class TestNestedCapture:
    def test_nested_capture_contexts(self):
        with ap.capture("outer") as outer:
            ap.record_step("outer_step", StepType.TOOL_CALL)
            with ap.capture("inner") as inner:
                ap.record_step("inner_step", StepType.TOOL_CALL)
            ap.record_step("outer_step_2", StepType.TOOL_CALL)

        assert len(outer) == 2
        assert outer.step_names == ["outer_step", "outer_step_2"]
        assert len(inner) == 1
        assert inner.step_names == ["inner_step"]

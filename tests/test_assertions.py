"""Tests for the assertions library."""

import pytest

import agentval as ap
from agentval import Step, StepType, Trace


class TestToolCalled:
    def test_tool_called_passes(self, simple_trace):
        ap.tool_called(simple_trace, "web_search")

    def test_tool_called_fails(self, simple_trace):
        with pytest.raises(ap.AgentAssertionError, match="never called"):
            ap.tool_called(simple_trace, "nonexistent_tool")

    def test_tool_called_times(self, simple_trace):
        ap.tool_called(simple_trace, "web_search", times=1)

    def test_tool_called_wrong_times(self, simple_trace):
        with pytest.raises(ap.AgentAssertionError, match="1 time"):
            ap.tool_called(simple_trace, "web_search", times=3)


class TestToolNotCalled:
    def test_tool_not_called_passes(self, simple_trace):
        ap.tool_not_called(simple_trace, "delete_file")

    def test_tool_not_called_fails(self, simple_trace):
        with pytest.raises(ap.AgentAssertionError, match="NOT be called"):
            ap.tool_not_called(simple_trace, "web_search")


class TestToolCalledWith:
    def test_tool_called_with_passes(self, simple_trace):
        ap.tool_called_with(simple_trace, "web_search", query="python")

    def test_tool_called_with_fails(self, simple_trace):
        with pytest.raises(ap.AgentAssertionError, match="never with expected"):
            ap.tool_called_with(simple_trace, "web_search", query="rust")

    def test_tool_called_with_missing_tool(self, simple_trace):
        with pytest.raises(ap.AgentAssertionError, match="never called"):
            ap.tool_called_with(simple_trace, "missing", query="test")


class TestStepOrder:
    def test_step_order_passes(self, simple_trace):
        ap.step_order(simple_trace, ["web_search", "summarize"])

    def test_step_order_non_consecutive(self, simple_trace):
        ap.step_order(simple_trace, ["web_search", "summarize"])

    def test_step_order_fails(self, simple_trace):
        with pytest.raises(ap.AgentAssertionError, match="not found"):
            ap.step_order(simple_trace, ["summarize", "web_search"])

    def test_exact_step_order_passes(self, simple_trace):
        ap.exact_step_order(simple_trace, ["web_search", "read_page", "summarize"])

    def test_exact_step_order_fails(self, simple_trace):
        with pytest.raises(ap.AgentAssertionError):
            ap.exact_step_order(simple_trace, ["web_search", "summarize"])


class TestStepNotAfter:
    def test_step_not_after_passes(self, simple_trace):
        ap.step_not_after(simple_trace, "web_search", "summarize")

    def test_step_not_after_fails(self):
        trace = Trace(name="test")
        trace.add_step(Step(name="search", step_type=StepType.TOOL_CALL))
        trace.add_step(Step(name="delete", step_type=StepType.TOOL_CALL))
        with pytest.raises(ap.AgentAssertionError, match="appeared at index"):
            ap.step_not_after(trace, "delete", "search")


class TestStepCounts:
    def test_max_steps_passes(self, simple_trace):
        ap.max_steps(simple_trace, 10)

    def test_max_steps_fails(self, simple_trace):
        with pytest.raises(ap.AgentAssertionError, match="at most 2"):
            ap.max_steps(simple_trace, 2)

    def test_min_steps_passes(self, simple_trace):
        ap.min_steps(simple_trace, 2)

    def test_min_steps_fails(self, simple_trace):
        with pytest.raises(ap.AgentAssertionError, match="at least 10"):
            ap.min_steps(simple_trace, 10)


class TestOutputAssertions:
    def test_output_contains_passes(self, simple_trace):
        ap.output_contains(simple_trace, "versatile")

    def test_output_contains_with_step(self, simple_trace):
        ap.output_contains(simple_trace, "Python.org", step_name="web_search")

    def test_output_contains_fails(self, simple_trace):
        with pytest.raises(ap.AgentAssertionError, match="contain"):
            ap.output_contains(simple_trace, "nonexistent_content")

    def test_output_matches_regex(self, simple_trace):
        ap.output_matches(simple_trace, r"Python.*language")

    def test_output_matches_fails(self, simple_trace):
        with pytest.raises(ap.AgentAssertionError, match="match pattern"):
            ap.output_matches(simple_trace, r"^impossible$")

    def test_output_contains_empty_trace(self, empty_trace):
        with pytest.raises(ap.AgentAssertionError, match="no steps"):
            ap.output_contains(empty_trace, "anything")


class TestStatusAssertions:
    def test_no_errors_passes(self, simple_trace):
        ap.no_errors(simple_trace)

    def test_no_errors_fails(self, failing_trace):
        with pytest.raises(ap.AgentAssertionError, match="step.*failed"):
            ap.no_errors(failing_trace)

    def test_step_succeeded(self, simple_trace):
        ap.step_succeeded(simple_trace, "web_search")

    def test_step_failed(self, failing_trace):
        ap.step_failed(failing_trace, "format")

    def test_step_succeeded_not_found(self, simple_trace):
        with pytest.raises(ap.AgentAssertionError, match="not found"):
            ap.step_succeeded(simple_trace, "missing")


class TestCustomAssertions:
    def test_step_matches_passes(self, simple_trace):
        ap.step_matches(
            simple_trace,
            "web_search",
            lambda s: len(s.output["result"]) > 0,
        )

    def test_step_matches_fails(self, simple_trace):
        with pytest.raises(ap.AgentAssertionError):
            ap.step_matches(
                simple_trace,
                "web_search",
                lambda s: len(s.output["result"]) > 100,
                message="Expected more than 100 results",
            )

    def test_trace_matches(self, simple_trace):
        ap.trace_matches(simple_trace, lambda t: len(t) == 3)

    def test_no_repeated_tool_calls_passes(self, simple_trace):
        ap.no_repeated_tool_calls(simple_trace, "web_search")

    def test_no_repeated_tool_calls_fails(self):
        trace = Trace(name="test")
        for _ in range(5):
            trace.add_step(Step(name="search", step_type=StepType.TOOL_CALL))
        with pytest.raises(ap.AgentAssertionError, match="infinite loop"):
            ap.no_repeated_tool_calls(trace, "search", max_repeats=2)

"""Assertion library for testing agent traces.

This is the core of AgentVal. Every function raises AssertionError
with a clear message on failure, making them work naturally with pytest.
"""

from __future__ import annotations

import re
from typing import Any, Callable

from .types import Step, StepType, Trace


class AgentAssertionError(AssertionError):
    """Assertion error with trace context for better debugging."""

    def __init__(self, message: str, step: Step | None = None, trace: Trace | None = None):
        self.step = step
        self.trace = trace
        super().__init__(message)


# ---------------------------------------------------------------------------
# Tool call assertions
# ---------------------------------------------------------------------------


def tool_called(trace: Trace, tool_name: str, times: int | None = None) -> None:
    """Assert that a tool was called during the trace.

    Args:
        trace: The execution trace to check.
        tool_name: Name of the tool to look for.
        times: If set, assert it was called exactly this many times.
    """
    calls = [s for s in trace.tool_calls if s.name == tool_name]
    if not calls:
        raise AgentAssertionError(
            f"Expected tool '{tool_name}' to be called, but it was never called.\n"
            f"Tools that were called: {[s.name for s in trace.tool_calls]}",
            trace=trace,
        )
    if times is not None and len(calls) != times:
        raise AgentAssertionError(
            f"Expected tool '{tool_name}' to be called {times} time(s), "
            f"but it was called {len(calls)} time(s).",
            trace=trace,
        )


def tool_not_called(trace: Trace, tool_name: str) -> None:
    """Assert that a tool was NOT called during the trace."""
    calls = [s for s in trace.tool_calls if s.name == tool_name]
    if calls:
        raise AgentAssertionError(
            f"Expected tool '{tool_name}' to NOT be called, "
            f"but it was called {len(calls)} time(s).",
            trace=trace,
        )


def tool_called_with(trace: Trace, tool_name: str, **expected_kwargs: Any) -> None:
    """Assert a tool was called with specific input arguments."""
    calls = [s for s in trace.tool_calls if s.name == tool_name]
    if not calls:
        raise AgentAssertionError(
            f"Expected tool '{tool_name}' to be called, but it was never called.",
            trace=trace,
        )
    for call in calls:
        kwargs = call.input.get("kwargs", {})
        if all(kwargs.get(k) == v for k, v in expected_kwargs.items()):
            return
    raise AgentAssertionError(
        f"Tool '{tool_name}' was called but never with expected args {expected_kwargs}.\n"
        f"Actual calls: {[s.input for s in calls]}",
        trace=trace,
    )


# ---------------------------------------------------------------------------
# Step order assertions
# ---------------------------------------------------------------------------


def step_order(trace: Trace, expected_order: list[str]) -> None:
    """Assert that steps occurred in the expected order.

    Does NOT require the steps to be consecutive — only that they
    appear in this relative order within the trace.
    """
    names = trace.step_names
    last_idx = -1
    for expected_name in expected_order:
        found = False
        for i in range(last_idx + 1, len(names)):
            if names[i] == expected_name:
                last_idx = i
                found = True
                break
        if not found:
            raise AgentAssertionError(
                f"Expected step '{expected_name}' to appear after index {last_idx} "
                f"in the trace, but it was not found.\n"
                f"Expected order: {expected_order}\n"
                f"Actual steps: {names}",
                trace=trace,
            )


def exact_step_order(trace: Trace, expected_order: list[str]) -> None:
    """Assert that the trace steps match exactly (no extra steps)."""
    names = trace.step_names
    if names != expected_order:
        raise AgentAssertionError(
            f"Expected exact step order {expected_order}, got {names}",
            trace=trace,
        )


def step_not_after(trace: Trace, step_name: str, not_after: str) -> None:
    """Assert that step_name never appears after not_after.

    Useful for safety checks like: "delete should never come after search
    without a confirmation step in between."
    """
    names = trace.step_names
    after_idx = None
    for i, name in enumerate(names):
        if name == not_after:
            after_idx = i
        if name == step_name and after_idx is not None:
            raise AgentAssertionError(
                f"Step '{step_name}' appeared at index {i}, "
                f"after '{not_after}' at index {after_idx}.\n"
                f"Steps: {names}",
                trace=trace,
            )


# ---------------------------------------------------------------------------
# Step count assertions
# ---------------------------------------------------------------------------


def max_steps(trace: Trace, maximum: int) -> None:
    """Assert the trace has at most N steps."""
    if len(trace) > maximum:
        raise AgentAssertionError(
            f"Expected at most {maximum} steps, but trace has {len(trace)} steps.",
            trace=trace,
        )


def min_steps(trace: Trace, minimum: int) -> None:
    """Assert the trace has at least N steps."""
    if len(trace) < minimum:
        raise AgentAssertionError(
            f"Expected at least {minimum} steps, but trace has {len(trace)} steps.",
            trace=trace,
        )


# ---------------------------------------------------------------------------
# Output assertions
# ---------------------------------------------------------------------------


def output_contains(trace: Trace, substring: str, step_name: str | None = None) -> None:
    """Assert that a step's output contains a substring.

    If step_name is None, checks the last step's output.
    """
    if step_name:
        step = trace.find_step(step_name)
        if step is None:
            raise AgentAssertionError(f"Step '{step_name}' not found in trace.", trace=trace)
    else:
        if not trace.steps:
            raise AgentAssertionError("Trace has no steps.", trace=trace)
        step = trace.steps[-1]

    output_str = str(step.output)
    if substring not in output_str:
        raise AgentAssertionError(
            f"Expected output of step '{step.name}' to contain '{substring}'.\n"
            f"Actual output: {output_str[:500]}",
            step=step,
            trace=trace,
        )


def output_matches(trace: Trace, pattern: str, step_name: str | None = None) -> None:
    """Assert that a step's output matches a regex pattern."""
    if step_name:
        step = trace.find_step(step_name)
        if step is None:
            raise AgentAssertionError(f"Step '{step_name}' not found in trace.", trace=trace)
    else:
        if not trace.steps:
            raise AgentAssertionError("Trace has no steps.", trace=trace)
        step = trace.steps[-1]

    output_str = str(step.output)
    if not re.search(pattern, output_str):
        raise AgentAssertionError(
            f"Expected output of step '{step.name}' to match pattern '{pattern}'.\n"
            f"Actual output: {output_str[:500]}",
            step=step,
            trace=trace,
        )


# ---------------------------------------------------------------------------
# Status assertions
# ---------------------------------------------------------------------------


def no_errors(trace: Trace) -> None:
    """Assert that no steps in the trace failed."""
    failed = trace.failed_steps
    if failed:
        names = [f"{s.name} (error: {s.error})" for s in failed]
        raise AgentAssertionError(
            f"Expected no errors, but {len(failed)} step(s) failed: {names}",
            trace=trace,
        )


def step_succeeded(trace: Trace, step_name: str) -> None:
    """Assert that a specific step succeeded."""
    step = trace.find_step(step_name)
    if step is None:
        raise AgentAssertionError(f"Step '{step_name}' not found in trace.", trace=trace)
    if not step.succeeded:
        raise AgentAssertionError(
            f"Expected step '{step_name}' to succeed, but it {step.status.value}.\n"
            f"Error: {step.error}",
            step=step,
            trace=trace,
        )


def step_failed(trace: Trace, step_name: str) -> None:
    """Assert that a specific step failed (useful for negative testing)."""
    step = trace.find_step(step_name)
    if step is None:
        raise AgentAssertionError(f"Step '{step_name}' not found in trace.", trace=trace)
    if not step.failed:
        raise AgentAssertionError(
            f"Expected step '{step_name}' to fail, but it {step.status.value}.",
            step=step,
            trace=trace,
        )


# ---------------------------------------------------------------------------
# Custom / flexible assertions
# ---------------------------------------------------------------------------


def step_matches(
    trace: Trace, step_name: str, predicate: Callable[[Step], bool], message: str = ""
) -> None:
    """Assert that a step satisfies a custom predicate.

    Usage:
        step_matches(trace, "web_search", lambda s: len(s.output["results"]) > 0)
    """
    step = trace.find_step(step_name)
    if step is None:
        raise AgentAssertionError(f"Step '{step_name}' not found in trace.", trace=trace)
    if not predicate(step):
        msg = message or f"Step '{step_name}' did not match the expected condition."
        raise AgentAssertionError(msg, step=step, trace=trace)


def trace_matches(trace: Trace, predicate: Callable[[Trace], bool], message: str = "") -> None:
    """Assert that the entire trace satisfies a custom predicate."""
    if not predicate(trace):
        msg = message or "Trace did not match the expected condition."
        raise AgentAssertionError(msg, trace=trace)


def no_repeated_tool_calls(trace: Trace, tool_name: str, max_repeats: int = 1) -> None:
    """Assert a tool isn't called repeatedly in a row (catches infinite loops)."""
    consecutive = 0
    for step in trace.steps:
        if step.step_type == StepType.TOOL_CALL and step.name == tool_name:
            consecutive += 1
            if consecutive > max_repeats:
                raise AgentAssertionError(
                    f"Tool '{tool_name}' was called {consecutive} times consecutively "
                    f"(max allowed: {max_repeats}). Possible infinite loop.",
                    trace=trace,
                )
        else:
            consecutive = 0

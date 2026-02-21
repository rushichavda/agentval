"""pytest plugin for AgentProbe.

Auto-registered via pyproject.toml entry point.
Provides fixtures, custom markers, and trace-aware test output.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from .analysis import analyze
from .types import Trace


def pytest_configure(config: Any) -> None:
    config.addinivalue_line(
        "markers",
        "agentprobe: mark a test as an AgentProbe agent behavior test",
    )


@pytest.fixture
def trace_from_file():
    """Fixture factory that loads a Trace from a JSON file.

    Usage:
        def test_my_agent(trace_from_file):
            trace = trace_from_file("traces/my_agent.json")
            ...
    """

    def _load(path: str | Path) -> Trace:
        return Trace.from_file(path)

    return _load


@pytest.fixture
def empty_trace() -> Trace:
    """Fixture that provides a fresh empty Trace."""
    return Trace(name="test_trace")


@pytest.fixture
def analyze_trace():
    """Fixture that runs analysis on a trace and returns the report.

    Usage:
        def test_my_agent(analyze_trace):
            report = analyze_trace(some_trace)
            assert not report.has_failures
    """

    def _analyze(trace: Trace):
        return analyze(trace)

    return _analyze


def pytest_terminal_summary(terminalreporter: Any, exitstatus: int, config: Any) -> None:
    """Add AgentProbe summary to pytest output."""
    reports = terminalreporter.getreports("failed")
    agent_failures = []

    for report in reports:
        if hasattr(report, "longreprtext") and "AgentAssertionError" in report.longreprtext:
            agent_failures.append(report)

    if agent_failures:
        terminalreporter.write_sep("=", "AgentProbe Failures")
        terminalreporter.write_line(f"{len(agent_failures)} agent behavior test(s) failed")

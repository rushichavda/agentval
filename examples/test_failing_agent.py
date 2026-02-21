"""Example: Analyzing a failing agent with root cause tracing.

Run with: pytest examples/test_failing_agent.py -v
"""

from pathlib import Path

import agentval as ap

TRACES_DIR = Path(__file__).parent / "traces"


def test_delete_agent_fails():
    """Demonstrate root cause analysis on a failing trace."""
    trace = ap.Trace.from_file(TRACES_DIR / "failing_agent.json")

    # The trace has failures
    assert trace.has_failures

    # Run root cause analysis
    report = ap.analyze(trace)
    assert report.has_failures

    # The root cause should point to scan_directory returning empty results
    rc = report.root_causes[0]
    assert rc.root_cause_step.name == "scan_directory"

    # Print the report (useful for debugging)
    print(report)


def test_delete_should_not_happen_without_confirmation_tool():
    """Safety: delete_files should never be called without a human confirmation tool."""
    trace = ap.Trace.from_file(TRACES_DIR / "failing_agent.json")

    # This test checks that the agent shouldn't delete after scanning
    # without a proper confirmation step (not just an LLM deciding)
    # In a real scenario, you'd check for a "human_confirm" tool call
    ap.tool_not_called(trace, "human_confirm")


def test_agent_should_handle_empty_scan():
    """The agent should gracefully handle empty scan results."""
    trace = ap.Trace.from_file(TRACES_DIR / "failing_agent.json")

    # find_duplicates should have caught that scan returned nothing useful
    step = trace.find_step("find_duplicates")
    assert step is not None

    # It produced null output — this is the root problem
    ap.step_matches(
        trace,
        "find_duplicates",
        lambda s: s.output.get("result") is not None,
        message="find_duplicates should not produce null output",
    )

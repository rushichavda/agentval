"""Example: Testing a search-and-summarize agent.

Run with: pytest examples/test_search_agent.py -v
"""

from pathlib import Path

import agentprobe as ap

TRACES_DIR = Path(__file__).parent / "traces"


def test_agent_searches_before_summarizing():
    """The agent should always search before summarizing."""
    trace = ap.Trace.from_file(TRACES_DIR / "search_agent.json")
    ap.step_order(trace, ["web_search", "summarize"])


def test_agent_uses_search_tool():
    """The agent must use the web_search tool."""
    trace = ap.Trace.from_file(TRACES_DIR / "search_agent.json")
    ap.tool_called(trace, "web_search")


def test_agent_reads_sources():
    """The agent should read at least one page it found."""
    trace = ap.Trace.from_file(TRACES_DIR / "search_agent.json")
    ap.tool_called(trace, "read_page")


def test_agent_does_not_delete_anything():
    """Safety check: search agent should never call delete tools."""
    trace = ap.Trace.from_file(TRACES_DIR / "search_agent.json")
    ap.tool_not_called(trace, "delete_file")
    ap.tool_not_called(trace, "delete_files")


def test_agent_completes_within_step_limit():
    """Agent should not take more than 10 steps."""
    trace = ap.Trace.from_file(TRACES_DIR / "search_agent.json")
    ap.max_steps(trace, 10)


def test_agent_produces_summary():
    """The final summary should contain actual content."""
    trace = ap.Trace.from_file(TRACES_DIR / "search_agent.json")
    ap.output_contains(trace, "async", step_name="summarize")


def test_no_errors_in_happy_path():
    """The happy path should have zero errors."""
    trace = ap.Trace.from_file(TRACES_DIR / "search_agent.json")
    ap.no_errors(trace)

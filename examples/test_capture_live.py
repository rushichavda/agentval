"""Example: Capturing traces from live function calls.

This shows how to use @trace_tool and capture() to record
traces from your own agent code without any framework.

Run with: pytest examples/test_capture_live.py -v
"""

import agentval as ap


# --- Simulated agent tools ---


@ap.trace_tool()
def web_search(query: str) -> list[dict]:
    """Simulate a web search."""
    return [
        {"title": f"Result for {query}", "url": "https://example.com"},
    ]


@ap.trace_tool()
def read_url(url: str) -> str:
    """Simulate reading a URL."""
    return f"Content from {url}: Python is a great language for AI development."


@ap.trace_llm()
def summarize(context: str) -> str:
    """Simulate an LLM summarization call."""
    return f"Summary: {context[:100]}"


# --- Tests ---


def test_live_capture():
    """Capture a trace from live function calls and test it."""
    with ap.capture("live_search_agent") as trace:
        results = web_search("python AI")
        content = read_url(results[0]["url"])
        summary = summarize(content)

    # Now test the captured trace
    assert len(trace) == 3
    ap.tool_called(trace, "web_search")
    ap.tool_called(trace, "read_url")
    ap.step_order(trace, ["web_search", "read_url", "summarize"])
    ap.no_errors(trace)
    ap.output_contains(trace, "Python", step_name="read_url")


def test_capture_with_failure():
    """Capture a trace where a tool fails."""

    @ap.trace_tool()
    def failing_tool():
        raise ValueError("Something went wrong")

    with ap.capture("failing_agent") as trace:
        try:
            failing_tool()
        except ValueError:
            pass

    assert trace.has_failures
    ap.step_failed(trace, "failing_tool")

    report = ap.analyze(trace)
    assert report.has_failures

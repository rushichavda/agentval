# AgentVal

**Testing framework for multi-step, multi-agent AI workflows.**

Test agent *behavior*, not just outputs. Like pytest for your AI agent's decision-making process.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-69%20passed-brightgreen.svg)]()

---

## The Problem

Existing eval tools test **inputs → outputs** (black box). But when your 10-step agent workflow fails at step 8, they can't tell you *why*.

- Was it a bad LLM decision at step 3?
- Did a tool return empty results at step 2 that cascaded?
- Is the agent calling tools in a dangerous order?

**AgentVal tests the journey, not just the destination.**

## Quick Start

```bash
pip install agentval
```

### Test a pre-recorded trace

```python
import agentval as ap

def test_agent_searches_before_summarizing():
    trace = ap.Trace.from_file("traces/my_agent.json")

    # Assert tool was called
    ap.tool_called(trace, "web_search")

    # Assert step order
    ap.step_order(trace, ["web_search", "summarize"])

    # Assert safety: agent should never delete anything
    ap.tool_not_called(trace, "delete_file")

    # Assert output quality
    ap.output_contains(trace, "python", step_name="summarize")

    # Assert no errors
    ap.no_errors(trace)
```

```bash
pytest test_my_agent.py -v
```

### Capture traces from live code

```python
import agentval as ap

@ap.trace_tool()
def web_search(query: str) -> list[dict]:
    return call_search_api(query)

@ap.trace_tool()
def read_url(url: str) -> str:
    return fetch_page(url)

@ap.trace_llm()
def summarize(context: str) -> str:
    return call_llm(context)

def test_live_agent():
    with ap.capture("search_agent") as trace:
        results = web_search("python async patterns")
        content = read_url(results[0]["url"])
        summary = summarize(content)

    ap.tool_called(trace, "web_search")
    ap.step_order(trace, ["web_search", "read_url", "summarize"])
    ap.no_errors(trace)
```

### Root cause analysis

When things fail, AgentVal traces back to find *where it actually went wrong*:

```python
import agentval as ap

trace = ap.Trace.from_file("traces/failing_agent.json")
report = ap.analyze(trace)

print(report)
```

```
AgentVal Analysis: failing_search_agent
Steps: 5 | Failures: 1
------------------------------------------------------------

Failure #1:
  Step 4 (delete_files) failed. Root cause traced to step 1 (scan_directory):
  Produced empty output (possible upstream data issue)

  Failed: step 4 (delete_files)
  Root cause: step 1 (scan_directory)

  Causal chain:
    [1] scan_directory: Produced empty output (possible upstream data issue)
    [2] find_duplicates: Produced empty output (possible upstream data issue)
    [4] delete_files: Failed with error: TypeError: Cannot iterate over NoneType
```

Step 4 failed, but the real problem was step 1 returning empty results.

## Assertions Reference

### Tool assertions
```python
ap.tool_called(trace, "web_search")            # tool was used
ap.tool_called(trace, "search", times=2)       # called exactly N times
ap.tool_not_called(trace, "delete_file")       # tool was NOT used
ap.tool_called_with(trace, "search", query="python")  # called with specific args
```

### Step order assertions
```python
ap.step_order(trace, ["search", "summarize"])   # relative order (non-consecutive ok)
ap.exact_step_order(trace, ["a", "b", "c"])     # exact match
ap.step_not_after(trace, "delete", "search")    # safety: delete never after search
```

### Output assertions
```python
ap.output_contains(trace, "python")                           # last step output
ap.output_contains(trace, "results", step_name="web_search")  # specific step
ap.output_matches(trace, r"Python.*language")                  # regex
```

### Status assertions
```python
ap.no_errors(trace)                       # zero failures
ap.step_succeeded(trace, "web_search")    # specific step ok
ap.step_failed(trace, "bad_step")         # expected failure (negative testing)
```

### Count assertions
```python
ap.max_steps(trace, 10)    # agent shouldn't take more than 10 steps
ap.min_steps(trace, 2)     # agent should do at least 2 things
```

### Custom assertions
```python
ap.step_matches(trace, "search", lambda s: len(s.output["results"]) > 0)
ap.trace_matches(trace, lambda t: t.duration_ms < 5000)
ap.no_repeated_tool_calls(trace, "search", max_repeats=2)  # catch infinite loops
```

## Trace Format

AgentVal uses a simple JSON trace format:

```json
{
  "trace_id": "abc123",
  "name": "my_agent",
  "steps": [
    {
      "step_id": "step_001",
      "name": "web_search",
      "step_type": "tool_call",
      "input": {"kwargs": {"query": "python"}},
      "output": {"result": [{"title": "Python.org"}]},
      "status": "success",
      "timestamp": 1708000000.0,
      "duration_ms": 450
    }
  ]
}
```

Step types: `llm_call`, `tool_call`, `handoff`, `decision`, `error`, `custom`

## Framework Adapters

### OpenAI Agents SDK

```bash
pip install agentval[openai]
```

```python
from agentval.adapters.openai_adapter import OpenAIAgentsAdapter
from agents import Agent, Runner

adapter = OpenAIAgentsAdapter()

agent = Agent(name="my_agent", instructions="...")
result = Runner.run_sync(agent, "hello")

trace = adapter.from_run_result(result)
ap.tool_called(trace, "web_search")
```

### Custom adapter

```python
from agentval.adapters.base import BaseAdapter

class MyFrameworkAdapter(BaseAdapter):
    def capture(self, **kwargs):
        # implement trace capture for your framework
        ...

    def parse_trace(self, raw_data):
        # convert framework data to AgentVal Trace
        ...
```

## pytest Integration

AgentVal registers as a pytest plugin automatically. Built-in fixtures:

```python
def test_with_fixture(trace_from_file):
    trace = trace_from_file("traces/my_agent.json")
    ap.no_errors(trace)

def test_with_analysis(analyze_trace, trace_from_file):
    trace = trace_from_file("traces/my_agent.json")
    report = analyze_trace(trace)
    assert not report.has_failures
```

## Why not DeepEval / Promptfoo / Ragas?

Those are great tools. They evaluate LLM **outputs** — accuracy, hallucination, relevance.

AgentVal evaluates agent **behavior** — what tools it called, in what order, whether it followed safety rules, and where things went wrong in multi-step workflows.

| | DeepEval/Promptfoo/Ragas | AgentVal |
|---|---|---|
| **Tests** | LLM output quality | Agent decision-making |
| **Scope** | Single LLM call | Multi-step workflows |
| **When fails** | "Output was wrong" | "Step 3 returned empty → Step 7 crashed" |
| **Approach** | Black box (input → output) | White box (full execution trace) |

Use them together. They're complementary.

## Roadmap

- [ ] Multi-agent handoff testing
- [ ] Drift detection (scheduled eval runs)
- [ ] Visual trace explorer (web UI)
- [ ] CI/CD GitHub Action
- [ ] LangChain/LangGraph adapter
- [ ] CrewAI adapter
- [ ] Smart sampling (statistical confidence with fewer LLM calls)
- [ ] Cost tracking per test run

## Contributing

Contributions welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Areas where help is most needed:
- Framework adapters (LangGraph, CrewAI, AutoGen, Google ADK)
- More assertion types
- Documentation and examples
- Real-world trace examples

## License

MIT

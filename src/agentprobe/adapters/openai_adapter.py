"""Adapter for OpenAI Agents SDK.

Captures traces from OpenAI's agent framework by hooking into
the Runner's event stream.

Requires: pip install agentprobe[openai]
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Generator

from ..types import Step, StepStatus, StepType, Trace
from .base import BaseAdapter


class OpenAIAgentsAdapter(BaseAdapter):
    """Adapter for the OpenAI Agents SDK.

    Converts OpenAI agent run results into AgentProbe traces.

    Usage:
        from agentprobe.adapters.openai_adapter import OpenAIAgentsAdapter
        from agents import Agent, Runner

        adapter = OpenAIAgentsAdapter()

        agent = Agent(name="my_agent", instructions="...")
        result = Runner.run_sync(agent, "hello")

        trace = adapter.from_run_result(result)
    """

    @contextmanager
    def capture(self, **kwargs: Any) -> Generator[Trace]:
        """Capture is not yet implemented for live OpenAI runs.

        Use from_run_result() instead to convert completed runs.
        """
        trace = Trace(name="openai_agent", metadata={"adapter": "openai"})
        yield trace

    def from_run_result(self, result: Any) -> Trace:
        """Convert an OpenAI Agents SDK RunResult to a Trace.

        Args:
            result: A RunResult from agents.Runner.run_sync() or similar.
        """
        trace = Trace(name="openai_agent", metadata={"adapter": "openai"})

        # Walk through the run's raw responses and tool calls
        for item in getattr(result, "raw_responses", []):
            # LLM call
            trace.add_step(
                Step(
                    name="llm_call",
                    step_type=StepType.LLM_CALL,
                    input={"model": getattr(item, "model", "unknown")},
                    output={"raw": str(item)[:500]},
                    status=StepStatus.SUCCESS,
                    metadata={"adapter": "openai"},
                )
            )

        # Extract tool calls from new_items if available
        for item in getattr(result, "new_items", []):
            item_type = type(item).__name__

            if "ToolCall" in item_type:
                trace.add_step(
                    Step(
                        name=getattr(item, "name", getattr(item, "type", "unknown_tool")),
                        step_type=StepType.TOOL_CALL,
                        input={"arguments": getattr(item, "arguments", "")},
                        output={"output": getattr(item, "output", "")},
                        status=StepStatus.SUCCESS,
                        metadata={"adapter": "openai", "item_type": item_type},
                    )
                )
            elif "Handoff" in item_type:
                trace.add_step(
                    Step(
                        name=f"handoff_{getattr(item, 'target_agent', 'unknown')}",
                        step_type=StepType.HANDOFF,
                        input={"source": getattr(item, "source_agent", "unknown")},
                        output={"target": getattr(item, "target_agent", "unknown")},
                        status=StepStatus.SUCCESS,
                        metadata={"adapter": "openai", "item_type": item_type},
                    )
                )
            elif "Message" in item_type:
                trace.add_step(
                    Step(
                        name="llm_response",
                        step_type=StepType.LLM_CALL,
                        output={"content": getattr(item, "content", "")[:500]},
                        status=StepStatus.SUCCESS,
                        metadata={"adapter": "openai", "item_type": item_type},
                    )
                )

        # Set final output
        final_output = getattr(result, "final_output", None)
        if final_output:
            trace.metadata["final_output"] = str(final_output)[:1000]

        return trace

    def parse_trace(self, raw_data: Any) -> Trace:
        """Parse raw OpenAI trace data (e.g., from logs)."""
        if hasattr(raw_data, "final_output"):
            return self.from_run_result(raw_data)

        # If it's a dict, try to parse as our standard format
        if isinstance(raw_data, dict):
            return Trace.from_dict(raw_data)

        raise ValueError(f"Cannot parse trace from {type(raw_data)}")

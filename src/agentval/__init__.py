"""AgentVal - Testing framework for multi-step, multi-agent AI workflows.

Test agent behavior, not just outputs.
"""

from .analysis import AnalysisReport, RootCauseReport, analyze, analyze_root_cause
from .assertions import (
    AgentAssertionError,
    exact_step_order,
    max_steps,
    min_steps,
    no_errors,
    no_repeated_tool_calls,
    output_contains,
    output_matches,
    step_failed,
    step_matches,
    step_not_after,
    step_order,
    step_succeeded,
    tool_called,
    tool_called_with,
    tool_not_called,
    trace_matches,
)
from .capture import capture, get_active_trace, record_step, trace_llm, trace_tool
from .types import Step, StepStatus, StepType, Trace

__version__ = "0.1.0"

__all__ = [
    # Types
    "Step",
    "StepStatus",
    "StepType",
    "Trace",
    # Capture
    "capture",
    "get_active_trace",
    "record_step",
    "trace_tool",
    "trace_llm",
    # Assertions
    "AgentAssertionError",
    "tool_called",
    "tool_not_called",
    "tool_called_with",
    "step_order",
    "exact_step_order",
    "step_not_after",
    "max_steps",
    "min_steps",
    "output_contains",
    "output_matches",
    "no_errors",
    "step_succeeded",
    "step_failed",
    "step_matches",
    "trace_matches",
    "no_repeated_tool_calls",
    # Analysis
    "analyze",
    "analyze_root_cause",
    "AnalysisReport",
    "RootCauseReport",
]

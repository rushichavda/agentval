"""Root cause analysis for agent trace failures.

When step 8 fails, this module traces back through the execution
to find where things actually went wrong.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .types import Step, StepStatus, StepType, Trace


@dataclass
class CausalLink:
    """A link in the causal chain from root cause to failure."""

    step_index: int
    step: Step
    reason: str


@dataclass
class RootCauseReport:
    """Report explaining why a trace failed and where the root cause is."""

    failed_step_index: int
    failed_step: Step
    root_cause_index: int
    root_cause_step: Step
    causal_chain: list[CausalLink] = field(default_factory=list)
    summary: str = ""

    def __str__(self) -> str:
        lines = [self.summary, ""]
        lines.append(f"  Failed: step {self.failed_step_index} ({self.failed_step.name})")
        lines.append(f"  Root cause: step {self.root_cause_index} ({self.root_cause_step.name})")

        if self.causal_chain:
            lines.append("")
            lines.append("  Causal chain:")
            for link in self.causal_chain:
                lines.append(f"    [{link.step_index}] {link.step.name}: {link.reason}")

        return "\n".join(lines)


@dataclass
class AnalysisReport:
    """Full analysis report for a trace."""

    trace: Trace
    root_causes: list[RootCauseReport] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def has_failures(self) -> bool:
        return len(self.root_causes) > 0

    def __str__(self) -> str:
        lines = [f"AgentVal Analysis: {self.trace.name or self.trace.trace_id}"]
        lines.append(f"Steps: {len(self.trace)} | Failures: {len(self.root_causes)}")
        lines.append("-" * 60)

        if not self.root_causes:
            lines.append("No failures detected.")
        else:
            for i, rc in enumerate(self.root_causes):
                lines.append(f"\nFailure #{i + 1}:")
                lines.append(str(rc))

        if self.warnings:
            lines.append("\nWarnings:")
            for w in self.warnings:
                lines.append(f"  - {w}")

        return "\n".join(lines)


def _is_empty_output(output: dict) -> bool:
    """Check if a step produced empty/null output."""
    if not output:
        return True
    result = output.get("result")
    if result is None:
        return True
    if isinstance(result, (list, dict, str)) and len(result) == 0:
        return True
    return False


def _find_data_dependency(trace: Trace, failed_index: int) -> list[CausalLink]:
    """Trace back through steps to find data flow issues.

    Heuristic: Look for earlier steps that failed or produced empty output,
    which could have cascaded into the failure.
    """
    chain: list[CausalLink] = []
    failed_step = trace.steps[failed_index]

    # Walk backwards through steps before the failure
    for i in range(failed_index - 1, -1, -1):
        step = trace.steps[i]

        if step.failed:
            chain.append(
                CausalLink(
                    step_index=i,
                    step=step,
                    reason=f"Failed with error: {step.error}",
                )
            )
        elif _is_empty_output(step.output):
            chain.append(
                CausalLink(
                    step_index=i,
                    step=step,
                    reason="Produced empty output (possible upstream data issue)",
                )
            )

    # If the failed step has a parent, check that too
    if failed_step.parent_id:
        for i, step in enumerate(trace.steps):
            if step.step_id == failed_step.parent_id and step.failed:
                chain.append(
                    CausalLink(
                        step_index=i,
                        step=step,
                        reason=f"Parent step failed: {step.error}",
                    )
                )

    # Sort by step index (earliest first)
    chain.sort(key=lambda c: c.step_index)
    return chain


def _detect_loops(trace: Trace) -> list[str]:
    """Detect potential infinite loops in tool calls."""
    warnings = []
    consecutive: dict[str, int] = {}
    last_name = ""

    for step in trace.steps:
        if step.step_type == StepType.TOOL_CALL:
            if step.name == last_name:
                consecutive[step.name] = consecutive.get(step.name, 1) + 1
            else:
                last_name = step.name
                consecutive[step.name] = 1

    for name, count in consecutive.items():
        if count >= 3:
            warnings.append(f"Tool '{name}' was called {count} times consecutively (possible loop)")

    return warnings


def _detect_high_step_count(trace: Trace, threshold: int = 20) -> list[str]:
    """Warn if trace has unusually many steps."""
    if len(trace) > threshold:
        return [
            f"Trace has {len(trace)} steps (threshold: {threshold}). "
            f"Consider if the agent is being efficient."
        ]
    return []


def analyze_root_cause(trace: Trace, failed_step_index: int) -> RootCauseReport:
    """Analyze a specific failure and trace it back to its root cause."""
    failed_step = trace.steps[failed_step_index]
    chain = _find_data_dependency(trace, failed_step_index)

    if chain:
        root = chain[0]
        # Add the failed step itself at the end of the chain
        chain.append(
            CausalLink(
                step_index=failed_step_index,
                step=failed_step,
                reason=f"Failed with error: {failed_step.error}",
            )
        )
        summary = (
            f"Step {failed_step_index} ({failed_step.name}) failed. "
            f"Root cause traced to step {root.step_index} ({root.step.name}): "
            f"{root.reason}"
        )
    else:
        root = CausalLink(
            step_index=failed_step_index,
            step=failed_step,
            reason=f"Failed with error: {failed_step.error}",
        )
        chain = [root]
        summary = (
            f"Step {failed_step_index} ({failed_step.name}) failed "
            f"with no identifiable upstream cause. Error: {failed_step.error}"
        )

    return RootCauseReport(
        failed_step_index=failed_step_index,
        failed_step=failed_step,
        root_cause_index=chain[0].step_index,
        root_cause_step=chain[0].step,
        causal_chain=chain,
        summary=summary,
    )


def analyze(trace: Trace) -> AnalysisReport:
    """Run full analysis on a trace.

    Finds all failures, traces root causes, and detects warnings.
    """
    root_causes = []
    for i, step in enumerate(trace.steps):
        if step.status == StepStatus.FAILED:
            root_causes.append(analyze_root_cause(trace, i))

    warnings = _detect_loops(trace) + _detect_high_step_count(trace)

    return AnalysisReport(
        trace=trace,
        root_causes=root_causes,
        warnings=warnings,
    )

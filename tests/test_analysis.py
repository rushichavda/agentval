"""Tests for root cause analysis."""

from agentval import Step, StepStatus, StepType, Trace, analyze


class TestAnalyze:
    def test_no_failures(self, simple_trace):
        report = analyze(simple_trace)
        assert not report.has_failures
        assert len(report.root_causes) == 0

    def test_finds_failure(self, failing_trace):
        report = analyze(failing_trace)
        assert report.has_failures
        assert len(report.root_causes) == 1

    def test_root_cause_traces_back(self, failing_trace):
        report = analyze(failing_trace)
        rc = report.root_causes[0]

        # Failed step is "format" (index 2)
        assert rc.failed_step.name == "format"
        assert rc.failed_step_index == 2

        # Root cause should be "search" (index 0) which returned empty results
        assert rc.root_cause_step.name == "search"
        assert rc.root_cause_index == 0

    def test_causal_chain(self, failing_trace):
        report = analyze(failing_trace)
        rc = report.root_causes[0]

        # Chain should include: search (empty) -> process (null) -> format (failed)
        assert len(rc.causal_chain) >= 2

    def test_report_string(self, failing_trace):
        report = analyze(failing_trace)
        output = str(report)
        assert "format" in output
        assert "search" in output

    def test_standalone_failure(self):
        """A failure with no upstream cause."""
        trace = Trace(name="test")
        trace.add_step(
            Step(
                name="good_step",
                step_type=StepType.TOOL_CALL,
                output={"result": "all good"},
            )
        )
        trace.add_step(
            Step(
                name="bad_step",
                step_type=StepType.TOOL_CALL,
                status=StepStatus.FAILED,
                error="Random network error",
            )
        )

        report = analyze(trace)
        assert report.has_failures
        rc = report.root_causes[0]
        assert rc.failed_step.name == "bad_step"
        assert "no identifiable upstream cause" in rc.summary


class TestWarnings:
    def test_loop_detection(self):
        trace = Trace(name="test")
        for _ in range(5):
            trace.add_step(Step(name="retry", step_type=StepType.TOOL_CALL))

        report = analyze(trace)
        assert any("retry" in w for w in report.warnings)

    def test_high_step_count(self):
        trace = Trace(name="test")
        for i in range(25):
            trace.add_step(Step(name=f"step_{i}", step_type=StepType.TOOL_CALL))

        report = analyze(trace)
        assert any("25 steps" in w for w in report.warnings)

    def test_no_warnings_for_normal_trace(self, simple_trace):
        report = analyze(simple_trace)
        assert len(report.warnings) == 0

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-02-20

### Added

- Core trace data models (`Trace`, `Step`, `StepType`, `StepStatus`)
- JSON serialization/deserialization for traces
- Trace capture via context manager (`capture()`)
- `@trace_tool` and `@trace_llm` decorators for automatic step recording
- Manual step recording with `record_step()`
- 16 assertion functions:
  - Tool assertions: `tool_called`, `tool_not_called`, `tool_called_with`
  - Step order: `step_order`, `exact_step_order`, `step_not_after`
  - Output: `output_contains`, `output_matches`
  - Status: `no_errors`, `step_succeeded`, `step_failed`
  - Counts: `max_steps`, `min_steps`
  - Custom: `step_matches`, `trace_matches`, `no_repeated_tool_calls`
- Root cause analysis engine (`analyze()`, `analyze_root_cause()`)
  - Causal chain tracing from failure back to root cause
  - Loop detection warnings
  - High step count warnings
- pytest plugin (auto-registered) with fixtures
- Base adapter interface for framework integrations
- OpenAI Agents SDK adapter
- Example traces and test files
- 69 unit tests

"""Core data models for AgentVal traces."""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class StepType(str, Enum):
    """Types of steps in an agent trace."""

    LLM_CALL = "llm_call"
    TOOL_CALL = "tool_call"
    HANDOFF = "handoff"
    DECISION = "decision"
    ERROR = "error"
    CUSTOM = "custom"


class StepStatus(str, Enum):
    """Status of a step execution."""

    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class Step:
    """A single step in an agent's execution trace.

    Represents one action the agent took: an LLM call, a tool call,
    a handoff to another agent, a decision point, or an error.
    """

    name: str
    step_type: StepType
    input: dict[str, Any] = field(default_factory=dict)
    output: dict[str, Any] = field(default_factory=dict)
    status: StepStatus = StepStatus.SUCCESS
    error: str | None = None
    timestamp: float = field(default_factory=time.time)
    duration_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    parent_id: str | None = None
    step_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])

    @property
    def failed(self) -> bool:
        return self.status == StepStatus.FAILED

    @property
    def succeeded(self) -> bool:
        return self.status == StepStatus.SUCCESS

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["step_type"] = self.step_type.value
        d["status"] = self.status.value
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Step:
        data = data.copy()
        data["step_type"] = StepType(data["step_type"])
        data["status"] = StepStatus(data.get("status", "success"))
        return cls(**data)


@dataclass
class Trace:
    """A complete execution trace of an agent workflow.

    Contains the ordered sequence of steps the agent took,
    along with metadata about the overall execution.
    """

    steps: list[Step] = field(default_factory=list)
    trace_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    name: str = ""
    start_time: float = field(default_factory=time.time)
    end_time: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def duration_ms(self) -> float | None:
        if self.end_time is None:
            return None
        return (self.end_time - self.start_time) * 1000

    @property
    def failed_steps(self) -> list[Step]:
        return [s for s in self.steps if s.failed]

    @property
    def has_failures(self) -> bool:
        return len(self.failed_steps) > 0

    @property
    def step_names(self) -> list[str]:
        return [s.name for s in self.steps]

    @property
    def tool_calls(self) -> list[Step]:
        return [s for s in self.steps if s.step_type == StepType.TOOL_CALL]

    @property
    def llm_calls(self) -> list[Step]:
        return [s for s in self.steps if s.step_type == StepType.LLM_CALL]

    def add_step(self, step: Step) -> None:
        self.steps.append(step)

    def find_step(self, name: str) -> Step | None:
        """Find the first step with the given name."""
        for step in self.steps:
            if step.name == name:
                return step
        return None

    def find_steps(self, name: str) -> list[Step]:
        """Find all steps with the given name."""
        return [s for s in self.steps if s.name == name]

    def find_steps_by_type(self, step_type: StepType) -> list[Step]:
        """Find all steps of a given type."""
        return [s for s in self.steps if s.step_type == step_type]

    def get_step_at(self, index: int) -> Step:
        """Get step at a specific index."""
        return self.steps[index]

    def get_children(self, parent_id: str) -> list[Step]:
        """Get all steps that are children of the given step."""
        return [s for s in self.steps if s.parent_id == parent_id]

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "name": self.name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "metadata": self.metadata,
            "steps": [s.to_dict() for s in self.steps],
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    def save(self, path: str | Path) -> None:
        """Save trace to a JSON file."""
        Path(path).write_text(self.to_json())

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Trace:
        data = data.copy()
        steps = [Step.from_dict(s) for s in data.pop("steps", [])]
        return cls(steps=steps, **data)

    @classmethod
    def from_json(cls, json_str: str) -> Trace:
        return cls.from_dict(json.loads(json_str))

    @classmethod
    def from_file(cls, path: str | Path) -> Trace:
        """Load a trace from a JSON file."""
        return cls.from_json(Path(path).read_text())

    def __len__(self) -> int:
        return len(self.steps)

    def __getitem__(self, index: int) -> Step:
        return self.steps[index]

    def __iter__(self):
        return iter(self.steps)

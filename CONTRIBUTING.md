# Contributing to AgentProbe

Thanks for your interest in contributing. This guide will help you get started.

## Development Setup

```bash
git clone https://github.com/rushichavda/agentprobe.git
cd agentprobe
uv venv .venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

## Running Tests

```bash
pytest tests/ -v
```

Run examples (one test is intentionally failing as a demo):
```bash
pytest examples/ -v
```

## Code Style

We use [ruff](https://github.com/astral-sh/ruff) for linting and formatting:

```bash
ruff check src/ tests/
ruff format src/ tests/
```

## What to Contribute

### High Impact

- **Framework adapters** — LangGraph, CrewAI, AutoGen, Google ADK, Anthropic Agent SDK
- **New assertion types** — anything you find yourself needing when testing agents
- **Real-world trace examples** — anonymized traces from actual agent workflows

### Medium Impact

- Bug fixes and edge case handling
- Documentation improvements
- Performance optimizations

### Always Welcome

- Bug reports with reproduction steps
- Feature requests with use cases
- Typo fixes

## Pull Request Process

1. Fork the repo and create a branch from `main`
2. Add tests for any new functionality
3. Ensure all tests pass (`pytest tests/ -v`)
4. Run the linter (`ruff check src/ tests/`)
5. Write a clear PR description explaining what and why

## Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add LangGraph adapter
fix: handle empty trace in step_order assertion
docs: add example for multi-agent testing
test: add edge cases for root cause analysis
```

## Adding a Framework Adapter

1. Create `src/agentprobe/adapters/your_framework.py`
2. Extend `BaseAdapter` from `agentprobe.adapters.base`
3. Implement `capture()` and `parse_trace()`
4. Add tests in `tests/test_adapters_your_framework.py`
5. Add an optional dependency in `pyproject.toml`
6. Add an example in `examples/`

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

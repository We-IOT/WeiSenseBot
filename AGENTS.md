# Development Guidelines for weisensebot

## Build / Lint / Test Commands

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run all tests
pytest tests/

# Run a single test file
pytest tests/test_commands.py

# Run a specific test function
pytest tests/test_commands.py::test_onboard_fresh_install

# Run tests with verbose output
pytest -v tests/

# Run tests with coverage
pytest --cov=weisensebot tests/

# Lint code
ruff check .

# Format code
ruff format .

# Check and fix linting issues
ruff check . --fix

# Type checking (if mypy is installed)
mypy weisensebot/
```

## Code Style Guidelines

### Imports

- Use `from __future__ import annotations` in new files for forward compatibility
- Group imports: standard library → third-party → local
- Sort imports within each group
- Use absolute imports: `from weisensebot.agent.loop import AgentLoop`
- Use `TYPE_CHECKING` guard for type hints that would cause circular imports

```python
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING, Any

from loguru import logger

from weisensebot.agent.tools.base import Tool

if TYPE_CHECKING:
    from weisensebot.config.schema import Config
```

### Formatting

- Line length: 100 characters
- Use 4 spaces for indentation (no tabs)
- No trailing whitespace
- One blank line between top-level definitions
- Two blank lines before top-level classes
- Use f-strings for string formatting

### Type Hints

- Use modern Python 3.10+ union syntax: `str | None` instead of `Union[str, None]`
- Use built-in generics: `list[str]` instead of `List[str]`
- Type hints required for all public APIs
- Use `Any` sparingly; prefer specific types
- Use `typing.TYPE_CHECKING` for circular import type hints

```python
async def execute(self, command: str, working_dir: str | None = None) -> str:
    ...
```

### Naming Conventions

- **Classes**: PascalCase (`AgentLoop`, `Tool`, `SessionManager`)
- **Functions/Methods**: snake_case (`build_system_prompt`, `get_identity`)
- **Constants**: UPPER_SNAKE_CASE (`BOOTSTRAP_FILES`, `_TOOL_RESULT_MAX_CHARS`)
- **Private members**: prefix with `_` (`_cache`, `_load`)
- **Module-level private**: prefix with `_` (`_internal_function`)
- **Instance variables**: snake_case (`self.workspace`, `self.bus`)

### Docstrings

- Use triple quotes for all modules, classes, and public methods
- Format: concise one-line summary + optional details
- Use `"""` not `'''`

```python
class Tool(ABC):
    """Base class for agent tools."""

    async def execute(self, **kwargs: Any) -> str:
        """Execute the tool with given parameters.

        Args:
            **kwargs: Tool-specific parameters.

        Returns:
            String result of the tool execution.
        """
        ...
```

### Error Handling

- Catch specific exceptions: `except FileNotFoundError` not `except Exception`
- Use `logger.exception()` for errors with full tracebacks
- Use `logger.warning()` for non-fatal issues
- Tool methods return error strings rather than raising
- Use context managers for resource cleanup

```python
try:
    data = json.loads(content)
except json.JSONDecodeError as e:
    logger.warning("Failed to parse JSON from {}: {}", key, e)
    return None
```

### Async/Await

- Use `asyncio.create_task()` for concurrent execution
- Use `asyncio.gather()` for waiting on multiple coroutines
- Use `@functools.lru_cache` for caching synchronous functions
- Use `async`/`await` consistently throughout

### Pydantic Models

- Inherit from `BaseModel` (custom base in `config/schema.py`)
- Use `Field(default_factory=list)` for mutable defaults
- Use `Field()` for validation rules
- Use `Literal` for string enums

```python
class ToolConfig(Base):
    enabled: bool = False
    allow_patterns: list[str] = Field(default_factory=list)
    mode: Literal["strict", "permissive"] = "permissive"
```

### Testing

- Use `pytest` for all tests
- Use `pytest.fixture` for test setup/teardown
- Use `unittest.mock.patch` for mocking
- Test filenames: `test_*.py`
- Test functions: `test_*`
- Use descriptive test names

```python
def test_onboard_fresh_install(mock_paths):
    """No existing config — should create from scratch."""
    result = runner.invoke(app, ["onboard"])
    assert result.exit_code == 0
    assert "Created config" in result.stdout
```

### File Structure

- Place tests in `tests/` directory mirroring `weisensebot/` structure
- Keep modules focused and single-purpose
- Use `__init__.py` for package organization
- Main entry point: `weisensebot/__main__.py`

### Configuration

- Use `pydantic-settings` for env var loading
- Config files in `~/.weisensebot/` or workspace-specific
- Use snake_case in config keys, with camelCase aliases supported
- Prefer `Field(default=...)` over default arguments

### Logging

- Use `loguru.logger` (imported as `logger`)
- Use appropriate levels: `DEBUG`, `INFO`, `WARNING`, `ERROR`
- Log important state transitions and external API calls
- Avoid logging sensitive data (API keys, tokens)

### Security

- Never commit secrets (API keys, tokens, credentials)
- Use environment variables or config files for secrets
- Validate all user inputs in tools
- Use allowlists over denylists where possible
- Consider workspace restrictions for file/shell operations

### Adding New Features

1. **New Provider**: Add to `providers/registry.py` and `config/schema.py`
2. **New Channel**: Inherit from `channels/base.py::BaseChannel`
3. **New Tool**: Inherit from `agent/tools/base.py::Tool`
4. **New Skill**: Create directory in `skills/` with `SKILL.md`
5. **New MCP Server**: Add to `config.json` under `tools.mcpServers`

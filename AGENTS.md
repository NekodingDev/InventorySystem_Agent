# AGENTS.md

## Build/Test Commands
- **Install dependencies**: `uv sync`
- **Run server**: `uv run python main.py`
- **Run with MCP**: `uv run mcp run main.py`
- **Lint**: `uv run ruff check .` (if ruff is added)
- **Format**: `uv run ruff format .` (if ruff is added)
- **Type check**: `uv run mypy .` (if mypy is added)

## Code Style Guidelines
- **Language**: Python 3.12+
- **Package Manager**: UV
- **Framework**: MCP (Model Context Protocol) with FastMCP
- **Imports**: Use standard imports, group standard library first
- **Naming**: snake_case for functions/variables, PascalCase for classes
- **Docstrings**: Use triple quotes, include Spanish descriptions where appropriate
- **Decorators**: Use `@mcp.tool()` for tools, `@mcp.resource()` for resources, `@mcp.prompt()` for prompts
- **Error Handling**: Use try/except blocks, handle MCP-specific errors
- **Comments**: Minimal, focus on clarity in code
- **File Structure**: Single main.py file for MCP server definitions
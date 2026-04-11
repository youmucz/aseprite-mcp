# CLAUDE.md

This file provides guidance when working with code in this repository.

## Project Overview

A Python MCP (Model Context Protocol) server that exposes Aseprite's pixel art and animation capabilities through AI assistants. The server generates Lua scripts and executes them via Aseprite's CLI (`--batch --script`) to create and manipulate sprites.

## Commands

```bash
# Run the MCP server (stdio transport)
uv run -m aseprite_mcp

# Health check
uv run -m aseprite_mcp --health

# Debug mode
uv run -m aseprite_mcp --debug

# Run tests
uv run pytest

# Install dependencies
uv sync

# Install with analysis extras (Pillow, scikit-learn)
uv sync --extra analysis
```

## Configuration

Three priority sources for Aseprite path:

1. **Environment variable**: `ASEPRITE_PATH=/path/to/aseprite`
2. **Config file**: `~/.config/aseprite-mcp/config.json`
3. **Project setting.json**: `external_tools.aseprite.executable`

Config file format (`~/.config/aseprite-mcp/config.json`):
```json
{
  "aseprite_path": "/absolute/path/to/aseprite",
  "temp_dir": "/tmp/aseprite-mcp",
  "timeout": 30,
  "log_level": "info",
  "log_file": "",
  "enable_timing": false
}
```

## Architecture

```
MCP Client (OpenCode, Claude, etc.)
    ↕ stdio (JSON-RPC)
FastMCP Server (Python)
    ├── config.py         Configuration loading (env > config.json > setting.json)
    ├── client.py         Aseprite CLI subprocess wrapper
    ├── lua/*.py          Lua script generation (core IP, ported from Go)
    └── tools/*.py        MCP tool definitions (40+ tools)
        ↕
    Aseprite --batch --script <temp.lua>
```

## Project Structure

```
src/aseprite_mcp/
├── __init__.py
├── __main__.py           Entry point
├── config.py             Configuration management
├── client.py             Aseprite CLI subprocess
├── server.py             FastMCP server entry
├── lua/                  Lua script generation (ported from Go lua_*.go)
│   ├── core.py           escape_string, format_color, transaction wrapper
│   ├── canvas.py         Sprite/layer/frame Lua generation
│   ├── drawing.py        Drawing primitives Lua generation
│   ├── animation.py      Animation Lua generation
│   ├── selection.py      Selection/clipboard Lua generation
│   ├── palette.py        Palette Lua generation
│   ├── export.py         Export/import Lua generation
│   ├── inspection.py     Pixel inspection Lua generation
│   ├── transform.py      Transform Lua generation
│   ├── auto_shading.py   Auto shading Lua generation
│   ├── quantization.py   Quantization Lua generation
│   └── ...
└── tools/                MCP tool definitions (ported from Go tools/*.go)
    ├── canvas.py         7 tools
    ├── drawing.py         6 tools
    ├── animation.py       5 tools
    ├── selection.py       8 tools
    ├── palette.py         7 tools
    ├── export.py          4 tools
    ├── inspection.py      1 tool
    ├── analysis.py        1 tool
    ├── dithering.py       1 tool
    ├── quantization.py    2 tools
    ├── auto_shading.py    1 tool
    ├── antialiasing.py    1 tool
    ├── transform.py       6 tools
    └── common.py          Shared types (Color, Point, Rectangle, etc.)
```

## Key Design Constraints

- **Stateless**: Each operation is independent, no shared state
- **Batch Mode Only**: All operations run via Aseprite `--batch` mode
- **Lua-based**: Operations use Aseprite's Lua API, not GUI automation
- **File-centric**: Operations work with sprite files on disk
- **Security**: Lua script injection prevention via `escape_string()`

## Code Style

- Use `from __future__ import annotations` at top of each file
- Follow PEP 8 conventions
- Tool functions must have docstrings (FastMCP uses them for descriptions)
- No comments in code

## Dependencies

Core: `mcp>=1.0.0` (FastMCP)
Optional: `Pillow>=10.0`, `scikit-learn>=1.3`, `numpy>=1.24` (for analysis tools)

## Aseprite Requirement

- Minimum: 1.3.0
- Recommended: 1.3.10+

from __future__ import annotations

import json
from mcp.server.fastmcp import FastMCP

from aseprite_mcp.client import AsepriteClient
from aseprite_mcp.config import Config
from aseprite_mcp.lua.batch import generate_batch_operations


def register_batch_tools(mcp: FastMCP, client: AsepriteClient, config: Config) -> None:

    @mcp.tool()
    async def batch_operations(sprite_path: str, operations: list[dict]) -> str:
        """Execute multiple Aseprite operations in a single process call. Combines multiple Lua scripts into one batch execution, dramatically reducing process overhead.

        Args:
            sprite_path: Path to the Aseprite sprite file. Use empty string "" for operations starting with create_canvas.
            operations: Array of operations to execute in order. Each operation has "type" and "params" fields. Supported types: create_canvas, set_palette, add_layer, add_frame, draw_pixels, draw_contour, draw_line, draw_rectangle, draw_circle, fill_area, save_as, export_sprite.

        Returns:
            JSON with success status and sprite_path
        """
        if not operations:
            return json.dumps({"error": "operations array cannot be empty"})

        for i, op in enumerate(operations):
            if "type" not in op:
                return json.dumps({"error": f"Operation {i}: missing 'type' field"})
            if "params" not in op and op["type"] != "create_canvas":
                return json.dumps({"error": f"Operation {i}: missing 'params' field"})

        has_create = operations[0]["type"] == "create_canvas"

        try:
            result_path, lua_script = generate_batch_operations(
                operations,
                temp_dir=config.temp_dir,
                has_existing_sprite=bool(sprite_path and not has_create),
            )
        except ValueError as e:
            return json.dumps({"error": str(e)})

        has_create = operations[0]["type"] == "create_canvas"
        effective_path = sprite_path or result_path

        exec_path = "" if has_create else effective_path

        if not has_create and not sprite_path:
            return json.dumps(
                {"error": "sprite_path is required when not using create_canvas"}
            )

        try:
            output = await client.execute_lua(lua_script, exec_path)
        except Exception as e:
            return json.dumps({"error": f"Batch execution failed: {str(e)}"})

        results = []
        for line in output.strip().split("\n"):
            line = line.strip()
            if line:
                results.append(line)

        return json.dumps(
            {
                "success": True,
                "sprite_path": effective_path,
                "results": results,
                "operations_executed": len(operations),
            }
        )

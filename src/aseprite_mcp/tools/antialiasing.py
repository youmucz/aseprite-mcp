from __future__ import annotations

import json
from mcp.server.fastmcp import FastMCP

from aseprite_mcp.client import AsepriteClient
from aseprite_mcp.config import Config
from aseprite_mcp.lua.antialiasing import generate_suggest_antialiasing, generate_apply_antialiasing_pixels


def register_antialiasing_tools(mcp: FastMCP, client: AsepriteClient, config: Config) -> None:

    @mcp.tool()
    async def suggest_antialiasing(sprite_path: str, layer_name: str, frame_number: int, region_x: int = 0, region_y: int = 0, region_width: int = 0, region_height: int = 0, threshold: int = 128, auto_apply: bool = False, use_palette: bool = False) -> str:
        f"""Analyze pixel art for jagged diagonal edges and suggest intermediate colors to smooth them (antialiasing). Detects stair-step patterns on diagonals and calculates blended colors to create smoother curves. Use auto_apply to automatically apply suggestions or use_palette to constrain intermediate colors to the sprite's palette. Returns suggestions with positions, colors, and directions for manual review or automatic application.

        Args:
            sprite_path: Path to the Aseprite sprite file
            layer_name: Name of the layer to analyze
            frame_number: Frame number to analyze (1-based)
            region_x: X coordinate of region to analyze (defaults to 0)
            region_y: Y coordinate of region to analyze (defaults to 0)
            region_width: Width of region to analyze (defaults to sprite width)
            region_height: Height of region to analyze (defaults to sprite height)
            threshold: Edge detection sensitivity 0-255 (default: 128)
            auto_apply: If true applies smoothing automatically (default: false)
            use_palette: If true snaps intermediate colors to palette (default: false)

        Returns:
            JSON with suggestions, applied, and total_edges
        """
        if frame_number < 1:
            return json.dumps({"error": "frame_number must be >= 1"})
        if not layer_name:
            return json.dumps({"error": "layer_name is required"})
        if threshold < 0 or threshold > 255:
            return json.dumps({"error": "threshold must be 0-255"})

        if region_width == 0 or region_height == 0:
            try:
                from aseprite_mcp.lua.canvas import generate_get_sprite_info
                info_script = generate_get_sprite_info()
                info_result = await client.execute_lua(info_script, sprite_path)
                info = json.loads(info_result)

                if region_width == 0:
                    region_width = info["width"]
                if region_height == 0:
                    region_height = info["height"]
            except (json.JSONDecodeError, KeyError):
                region_width = 100
                region_height = 100

        script = generate_suggest_antialiasing(layer_name, frame_number, region_x, region_y, region_width, region_height, threshold, use_palette)
        result = await client.execute_lua(script, sprite_path)

        try:
            data = json.loads(result)
        except json.JSONDecodeError:
            return json.dumps({"error": "Failed to parse antialiasing result"})

        if auto_apply and data.get("suggestions"):
            apply_script = generate_apply_antialiasing_pixels(layer_name, frame_number, data["suggestions"], use_palette)
            await client.execute_lua(apply_script, sprite_path)
            data["applied"] = True

        return json.dumps(data)

from __future__ import annotations

import json
import os
from mcp.server.fastmcp import FastMCP

from aseprite_mcp.client import AsepriteClient
from aseprite_mcp.config import Config
from aseprite_mcp.lua.export import (
    generate_export_sprite,
    generate_export_spritesheet,
    generate_import_image,
    generate_save_as,
)

from aseprite_mcp.tools.common import extract_mcp_output


def register_export_tools(mcp: FastMCP, client: AsepriteClient, config: Config) -> None:

    @mcp.tool()
    async def export_sprite(
        sprite_path: str, output_path: str, format: str, frame_number: int = 0
    ) -> str:
        """Export sprite to common image formats (PNG, GIF, JPG, BMP).

        Args:
            sprite_path: Path to the Aseprite sprite file
            output_path: Output file path for exported image
            format: Export format: png, gif, jpg, bmp
            frame_number: Specific frame to export (0 = all frames, 1-based)

        Returns:
            JSON with exported_path and file_size
        """
        if not output_path:
            return json.dumps({"error": "output_path cannot be empty"})

        valid_formats = ["png", "gif", "jpg", "bmp"]
        format_lower = format.lower()
        if format_lower not in valid_formats:
            return json.dumps(
                {"error": f"invalid format: {format} (valid: png, gif, jpg, bmp)"}
            )

        if frame_number < 0:
            return json.dumps({"error": "frame_number must be non-negative"})

        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        script = generate_export_sprite(output_path, frame_number)
        output = await client.execute_lua(script, sprite_path)

        mcp_output = extract_mcp_output(output)
        if "Exported successfully" not in mcp_output:
            return json.dumps({"error": "Export failed", "details": output})

        file_size = 0
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)

        return json.dumps({"exported_path": output_path, "file_size": file_size})

    @mcp.tool()
    async def export_spritesheet(
        sprite_path: str,
        output_path: str,
        layout: str = "horizontal",
        padding: int = 0,
        include_json: bool = False,
    ) -> str:
        """Export animation frames as spritesheet with layout options.

        Args:
            sprite_path: Path to the Aseprite sprite file
            output_path: Output file path for spritesheet
            layout: Spritesheet layout: horizontal, vertical, rows, columns, or packed
            padding: Padding between frames in pixels (0-100)
            include_json: Include JSON metadata file

        Returns:
            JSON with spritesheet_path, metadata_path (if included), and frame_count
        """
        if not output_path:
            return json.dumps({"error": "output_path cannot be empty"})

        if not sprite_path:
            return json.dumps({"error": "sprite_path cannot be empty"})

        valid_layouts = ["horizontal", "vertical", "rows", "columns", "packed"]
        if layout not in valid_layouts:
            return json.dumps(
                {
                    "error": f"invalid layout: {layout} (valid: horizontal, vertical, rows, columns, packed)"
                }
            )

        if padding < 0 or padding > 100:
            return json.dumps({"error": "padding must be between 0 and 100"})

        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        script = generate_export_spritesheet(output_path, layout, padding, include_json)
        output = await client.execute_lua(script, sprite_path)

        mcp_output = extract_mcp_output(output)
        try:
            parsed = json.loads(mcp_output)
        except json.JSONDecodeError:
            return json.dumps(
                {"error": "Failed to parse spritesheet output", "details": output}
            )

        return json.dumps(parsed)

    @mcp.tool()
    async def import_image(
        sprite_path: str,
        image_path: str,
        layer_name: str,
        frame_number: int,
        x: int = None,
        y: int = None,
    ) -> str:
        """Import an external image file as a layer in the sprite.

        Args:
            sprite_path: Path to the Aseprite sprite file
            image_path: Path to image file to import
            layer_name: Layer name for imported image
            frame_number: Frame number to place image (1-based)
            x: X position to place image (optional, defaults to 0)
            y: Y position to place image (optional, defaults to 0)

        Returns:
            JSON with success status
        """
        if not sprite_path:
            return json.dumps({"error": "sprite_path cannot be empty"})

        if not image_path:
            return json.dumps({"error": "image_path cannot be empty"})

        if not layer_name:
            return json.dumps({"error": "layer_name cannot be empty"})

        if frame_number < 1:
            return json.dumps({"error": "frame_number must be >= 1"})

        if not os.path.exists(image_path):
            return json.dumps({"error": f"image file not found: {image_path}"})

        script = generate_import_image(image_path, layer_name, frame_number, x, y)
        output = await client.execute_lua(script, sprite_path)

        mcp_output = extract_mcp_output(output)
        if "Image imported successfully" not in mcp_output:
            return json.dumps({"error": "Import failed", "details": output})

        return json.dumps({"success": True})

    @mcp.tool()
    async def save_as(sprite_path: str, output_path: str) -> str:
        """Save sprite to a new .aseprite file path.

        Args:
            sprite_path: Path to the Aseprite sprite file
            output_path: New .aseprite file path

        Returns:
            JSON with success status and file_path
        """
        if not sprite_path:
            return json.dumps({"error": "sprite_path cannot be empty"})

        if not output_path:
            return json.dumps({"error": "output_path cannot be empty"})

        if not (output_path.endswith(".aseprite") or output_path.endswith(".ase")):
            return json.dumps(
                {"error": "output_path must have .aseprite or .ase extension"}
            )

        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        script = generate_save_as(output_path)
        output = await client.execute_lua(script, sprite_path)

        mcp_output = extract_mcp_output(output)
        try:
            parsed = json.loads(mcp_output)
        except json.JSONDecodeError:
            return json.dumps(
                {"error": "Failed to parse save_as output", "details": output}
            )

        return json.dumps(parsed)

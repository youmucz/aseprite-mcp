from __future__ import annotations

import json
import os
import time
from mcp.server.fastmcp import FastMCP

from aseprite_mcp.client import AsepriteClient
from aseprite_mcp.config import Config
from aseprite_mcp.lua.canvas import generate_create_sprite
from aseprite_mcp.lua.palette import generate_set_palette
from aseprite_mcp.lua.canvas import generate_add_layer
from aseprite_mcp.lua.drawing import (
    generate_draw_pixels,
    generate_draw_contour,
    generate_fill_area,
)
from aseprite_mcp.lua.export import generate_save_as, generate_export_sprite
from aseprite_mcp.tools.common import Color, ColorMode, Pixel, Point


def register_plan_tools(mcp: FastMCP, client: AsepriteClient, config: Config) -> None:

    @mcp.tool()
    async def draw_from_plan(
        width: int,
        height: int,
        color_mode: str = "indexed",
        palette: list[str] | None = None,
        layers: list[str] | None = None,
        contours: list[dict] | None = None,
        fills: list[dict] | None = None,
        pixel_groups: list[dict] | None = None,
        output_path: str = "",
        export_png: bool = True,
    ) -> str:
        """Create a complete pixel art sprite from a single plan in one process call. Combines canvas creation, palette setup, layer management, drawing, and export into one operation.

        Args:
            width: Canvas width (1-65535)
            height: Canvas height (1-65535)
            color_mode: Color mode (rgb, grayscale, or indexed)
            palette: Array of hex colors for the palette
            layers: Array of layer names to create (in bottom-to-top order)
            contours: Array of contour drawings [{layer_name, frame_number, points: [{x,y}], color, thickness, closed}]
            fills: Array of fill operations [{layer_name, frame_number, x, y, color, tolerance}]
            pixel_groups: Array of pixel group drawings [{layer_name, frame_number, pixels: [{x,y,color}]}]
            output_path: Output .aseprite file path (auto-generated if empty)
            export_png: Also export PNG (default: true)

        Returns:
            JSON with sprite_path, export_path, and operation summary
        """
        if palette is None:
            palette = []
        if layers is None:
            layers = []
        if contours is None:
            contours = []
        if fills is None:
            fills = []
        if pixel_groups is None:
            pixel_groups = []

        if not 1 <= width <= 65535 or not 1 <= height <= 65535:
            return json.dumps({"error": "width and height must be 1-65535"})
        if color_mode not in ("rgb", "grayscale", "indexed"):
            return json.dumps(
                {"error": "color_mode must be rgb, grayscale, or indexed"}
            )

        if not output_path:
            output_path = os.path.join(
                config.temp_dir,
                f"plan-{int(time.time() * 1000)}.aseprite",
            )

        export_path = ""
        if export_png:
            export_path = output_path.rsplit(".", 1)[0] + ".png"

        cm = (
            ColorMode.RGB
            if color_mode == "rgb"
            else (
                ColorMode.GRAYSCALE if color_mode == "grayscale" else ColorMode.INDEXED
            )
        )
        parts: list[str] = []

        parts.append(generate_create_sprite(width, height, cm, output_path))

        if palette:
            parts.append(generate_set_palette(palette))

        for layer_name in layers:
            parts.append(generate_add_layer(layer_name))

        for c in contours:
            points = [Point(x=p["x"], y=p["y"]) for p in c["points"]]
            parts.append(
                generate_draw_contour(
                    c["layer_name"],
                    c.get("frame_number", 1),
                    points,
                    Color.from_hex(c["color"]),
                    c.get("thickness", 1),
                    c.get("closed", False),
                    c.get("use_palette", False),
                )
            )

        for f in fills:
            parts.append(
                generate_fill_area(
                    f["layer_name"],
                    f.get("frame_number", 1),
                    f["x"],
                    f["y"],
                    Color.from_hex(f["color"]),
                    f.get("tolerance", 0),
                    f.get("use_palette", False),
                )
            )

        for pg in pixel_groups:
            pixels = [
                Pixel(x=p["x"], y=p["y"], color=Color.from_hex(p["color"]))
                for p in pg["pixels"]
            ]
            parts.append(
                generate_draw_pixels(
                    pg["layer_name"],
                    pg.get("frame_number", 1),
                    pixels,
                    pg.get("use_palette", False),
                )
            )

        parts.append(generate_save_as(output_path))
        if export_path:
            parts.append(generate_export_sprite(export_path, 0))

        combined_lua = "\n\n".join(parts)

        try:
            output = await client.execute_lua(combined_lua, "")
        except Exception as e:
            return json.dumps({"error": f"draw_from_plan execution failed: {str(e)}"})

        return json.dumps(
            {
                "success": True,
                "sprite_path": output_path,
                "export_path": export_path,
                "summary": {
                    "layers_created": len(layers),
                    "contours_drawn": len(contours),
                    "fills_applied": len(fills),
                    "pixel_groups_drawn": len(pixel_groups),
                    "palette_size": len(palette),
                },
            }
        )

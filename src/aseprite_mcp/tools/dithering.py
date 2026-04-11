from __future__ import annotations

import json
from mcp.server.fastmcp import FastMCP

from aseprite_mcp.client import AsepriteClient
from aseprite_mcp.config import Config
from aseprite_mcp.lua.dithering import generate_draw_with_dither


def register_dithering_tools(mcp: FastMCP, client: AsepriteClient, config: Config) -> None:

    @mcp.tool()
    async def draw_with_dither(sprite_path: str, layer_name: str, frame_number: int, region_x: int, region_y: int, region_width: int, region_height: int, color1: str, color2: str, pattern: str, density: float = 0.5) -> str:
        f"""Fill a region with a dithering pattern to create smooth gradients and textures. Supports 16 patterns: Bayer matrix (bayer_2x2, bayer_4x4, bayer_8x8) for ordered dithering, Floyd-Steinberg error diffusion (floyd_steinberg) for high-quality gradients, checkerboard for 50/50 blends, and texture patterns (grass, water, stone, cloud, brick, dots, diagonal, cross, noise, horizontal_lines, vertical_lines) for organic effects. Use density parameter to control the ratio of color1 to color2 (0.0 = all color1, 1.0 = all color2, 0.5 = even mix). Essential for professional pixel art gradients and textures.

        Args:
            sprite_path: Path to the Aseprite sprite file
            layer_name: Name of the layer to draw on
            frame_number: Frame number to draw on (1-based)
            region_x: X coordinate of top-left corner
            region_y: Y coordinate of top-left corner
            region_width: Width of region
            region_height: Height of region
            color1: First color (hex #RRGGBB or #RRGGBBAA)
            color2: Second color (hex #RRGGBB or #RRGGBBAA)
            pattern: Dithering pattern: bayer_2x2|bayer_4x4|bayer_8x8|checkerboard|floyd_steinberg|grass|water|stone|cloud|brick|dots|diagonal|cross|noise|horizontal_lines|vertical_lines
            density: Ratio of color1 to color2 (0.0-1.0, default: 0.5)

        Returns:
            JSON with success status
        """
        if frame_number < 1:
            return json.dumps({"error": "frame_number must be >= 1"})
        if not layer_name:
            return json.dumps({"error": "layer_name is required"})
        if region_width <= 0 or region_height <= 0:
            return json.dumps({"error": "region width and height must be positive"})

        valid_patterns = {
            "bayer_2x2", "bayer_4x4", "bayer_8x8",
            "checkerboard", "floyd_steinberg",
            "grass", "water", "stone", "cloud", "brick",
            "dots", "diagonal", "cross", "noise",
            "horizontal_lines", "vertical_lines"
        }
        if pattern not in valid_patterns:
            return json.dumps({"error": f"invalid pattern: {pattern}"})

        if not color1.startswith("#") or len(color1) not in (7, 9):
            return json.dumps({"error": "invalid color1 format (expected #RRGGBB or #RRGGBBAA)"})
        if not color2.startswith("#") or len(color2) not in (7, 9):
            return json.dumps({"error": "invalid color2 format (expected #RRGGBB or #RRGGBBAA)"})

        if density < 0.0 or density > 1.0:
            return json.dumps({"error": "density must be between 0.0 and 1.0"})

        script = generate_draw_with_dither(layer_name, frame_number, region_x, region_y, region_width, region_height, color1, color2, pattern, density)
        await client.execute_lua(script, sprite_path)

        return json.dumps({"success": True})

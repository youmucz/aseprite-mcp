from __future__ import annotations

import json
from mcp.server.fastmcp import FastMCP

from aseprite_mcp.client import AsepriteClient
from aseprite_mcp.config import Config
from aseprite_mcp.lua.analysis import generate_analyze_reference


def register_analysis_tools(mcp: FastMCP, client: AsepriteClient, config: Config) -> None:

    @mcp.tool()
    async def analyze_reference(reference_path: str, target_width: int, target_height: int, palette_size: int = 16, brightness_levels: int = 5, edge_threshold: int = 30) -> str:
        f"""Extract structured data from reference images to guide pixel art creation. Performs k-means palette extraction, brightness/edge detection, and composition analysis. Returns palette sorted by hue/lightness, brightness map with quantized levels, edge map with major contours, composition guides (rule of thirds, focal points), and suggested dithering zones.

        Args:
            reference_path: Path to reference image (.jpg, .png, .gif, .bmp, .aseprite)
            target_width: Pixel art target width (1-65535)
            target_height: Pixel art target height (1-65535)
            palette_size: Number of colors to extract (5-32, default: 16)
            brightness_levels: Quantize brightness into N levels (2-10, default: 5)
            edge_threshold: Edge detection sensitivity (0-255, default: 30)

        Returns:
            JSON with palette, brightness_map, edge_map, composition, metadata, and dithering_zones
        """
        if target_width < 1 or target_width > 65535:
            return json.dumps({"error": "target_width must be between 1 and 65535"})
        if target_height < 1 or target_height > 65535:
            return json.dumps({"error": "target_height must be between 1 and 65535"})
        if palette_size < 5 or palette_size > 32:
            return json.dumps({"error": "palette_size must be between 5 and 32"})
        if brightness_levels < 2 or brightness_levels > 10:
            return json.dumps({"error": "brightness_levels must be between 2 and 10"})
        if edge_threshold < 0 or edge_threshold > 255:
            return json.dumps({"error": "edge_threshold must be between 0 and 255"})

        script = generate_analyze_reference(reference_path, target_width, target_height, palette_size, brightness_levels, edge_threshold)
        result = await client.execute_lua(script, "")

        try:
            data = json.loads(result)
        except json.JSONDecodeError:
            return json.dumps({"error": "Failed to parse analysis result"})

        return json.dumps(data)

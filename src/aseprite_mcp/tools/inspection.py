from __future__ import annotations

import json
from mcp.server.fastmcp import FastMCP

from aseprite_mcp.client import AsepriteClient
from aseprite_mcp.config import Config
from aseprite_mcp.lua.inspection import generate_get_pixels_with_pagination


def register_inspection_tools(mcp: FastMCP, client: AsepriteClient, config: Config) -> None:
    
    @mcp.tool()
    async def get_pixels(sprite_path: str, layer_name: str, frame_number: int, x: int, y: int, width: int, height: int, cursor: str = "", page_size: int = 1000) -> str:
        f"""Read pixel data from a rectangular region of a sprite. Returns an array of pixels with their coordinates and colors in hex format (#RRGGBBAA). Supports pagination for large regions using cursor and page_size parameters (default page size: 1000, max: 10000).
        
        Args:
            sprite_path: Path to the Aseprite sprite file
            layer_name: Name of the layer to read from
            frame_number: Frame number to read from (1-based)
            x: X coordinate of top-left corner of region
            y: Y coordinate of top-left corner of region
            width: Width of region to read
            height: Height of region to read
            cursor: Pagination cursor for fetching next page (optional)
            page_size: Number of pixels to return per page (default: 1000, max: 10000)
        
        Returns:
            JSON with pixels array, next_cursor (empty if no more pages), and total_pixels
        """
        if width <= 0 or height <= 0:
            return json.dumps({"error": "width and height must be positive"})
        
        if frame_number < 1:
            return json.dumps({"error": "frame_number must be >= 1"})
        
        if page_size <= 0:
            page_size = 1000
        if page_size > 10000:
            page_size = 10000
        
        offset = 0
        if cursor:
            try:
                offset = int(cursor)
            except ValueError:
                return json.dumps({"error": "invalid cursor"})
        
        total_pixel_count = width * height
        
        script = generate_get_pixels_with_pagination(layer_name, frame_number, x, y, width, height, offset, page_size)
        output = await client.execute_lua(script, sprite_path)
        
        try:
            pixels = json.loads(output)
        except json.JSONDecodeError:
            return json.dumps({"error": "Failed to parse pixel data", "details": output})
        
        next_cursor = ""
        next_offset = offset + len(pixels)
        if next_offset < total_pixel_count:
            next_cursor = str(next_offset)
        
        return json.dumps({
            "pixels": pixels,
            "next_cursor": next_cursor,
            "total_pixels": total_pixel_count
        })

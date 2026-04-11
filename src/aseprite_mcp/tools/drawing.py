from __future__ import annotations

import json
from mcp.server.fastmcp import FastMCP

from aseprite_mcp.client import AsepriteClient
from aseprite_mcp.config import Config
from aseprite_mcp.lua.drawing import (
    generate_draw_pixels,
    generate_draw_line,
    generate_draw_contour,
    generate_draw_rectangle,
    generate_draw_circle,
    generate_fill_area,
)
from aseprite_mcp.tools.common import Color, Point


def register_drawing_tools(mcp: FastMCP, client: AsepriteClient, config: Config) -> None:
    
    @mcp.tool()
    async def draw_pixels(sprite_path: str, layer_name: str, frame_number: int, pixels: list[dict], use_palette: bool = False) -> str:
        f"""Draw individual pixels at specified coordinates.
        
        Args:
            sprite_path: Path to the Aseprite sprite file
            layer_name: Name of the layer to draw on
            frame_number: Frame number to draw on (1-based)
            pixels: Array of pixels to draw with positions and colors
            use_palette: Snap colors to nearest palette color (default: false)
        
        Returns:
            JSON with pixels_drawn count
        """
        if not layer_name:
            return json.dumps({"error": "layer_name cannot be empty"})
        if frame_number < 1:
            return json.dumps({"error": "frame_number must be at least 1"})
        if not pixels:
            return json.dumps({"error": "pixels array cannot be empty"})
        
        pixel_objs = []
        for i, p in enumerate(pixels):
            try:
                color = Color.from_hex(p["color"])
                pixel_objs.append(Pixel(x=p["x"], y=p["y"], color=color))
            except (KeyError, ValueError) as e:
                return json.dumps({"error": f"Invalid pixel at index {i}: {e}"})
        
        script = generate_draw_pixels(layer_name, frame_number, pixel_objs, use_palette)
        await client.execute_lua(script, sprite_path)
        
        return json.dumps({"pixels_drawn": len(pixel_objs)})
    
    @mcp.tool()
    async def draw_line(sprite_path: str, layer_name: str, frame_number: int, x1: int, y1: int, x2: int, y2: int, color: str, thickness: int = 1, use_palette: bool = False) -> str:
        f"""Draw a line between two points.
        
        Args:
            sprite_path: Path to the Aseprite sprite file
            layer_name: Name of the layer to draw on
            frame_number: Frame number to draw on (1-based)
            x1: X coordinate of line start point
            y1: Y coordinate of line start point
            x2: X coordinate of line end point
            y2: Y coordinate of line end point
            color: Hex color string in format #RRGGBB or #RRGGBBAA
            thickness: Line thickness in pixels (1-100)
            use_palette: Snap colors to nearest palette color (default: false)
        
        Returns:
            JSON with success status
        """
        if not layer_name:
            return json.dumps({"error": "layer_name cannot be empty"})
        if frame_number < 1:
            return json.dumps({"error": "frame_number must be at least 1"})
        if thickness < 1 or thickness > 100:
            return json.dumps({"error": "thickness must be 1-100"})
        
        try:
            color_obj = Color.from_hex(color)
        except ValueError:
            return json.dumps({"error": "Invalid color format"})
        
        script = generate_draw_line(layer_name, frame_number, x1, y1, x2, y2, color_obj, thickness, use_palette)
        await client.execute_lua(script, sprite_path)
        
        return json.dumps({"success": True})
    
    @mcp.tool()
    async def draw_contour(sprite_path: str, layer_name: str, frame_number: int, points: list[dict], color: str, thickness: int = 1, closed: bool = False, use_palette: bool = False) -> str:
        f"""Draw a polyline or polygon by connecting multiple points.
        
        Args:
            sprite_path: Path to the Aseprite sprite file
            layer_name: Name of the layer to draw on
            frame_number: Frame number to draw on (1-based)
            points: Array of points to connect (minimum 2 points)
            color: Hex color string in format #RRGGBB or #RRGGBBAA
            thickness: Line thickness in pixels (1-100)
            closed: Connect last point to first to form a closed polygon (default: false)
            use_palette: Snap colors to nearest palette color (default: false)
        
        Returns:
            JSON with success status
        """
        if not layer_name:
            return json.dumps({"error": "layer_name cannot be empty"})
        if frame_number < 1:
            return json.dumps({"error": "frame_number must be at least 1"})
        if len(points) < 2:
            return json.dumps({"error": "at least 2 points are required"})
        if thickness < 1 or thickness > 100:
            return json.dumps({"error": "thickness must be 1-100"})
        
        try:
            color_obj = Color.from_hex(color)
        except ValueError:
            return json.dumps({"error": "Invalid color format"})
        
        point_objs = [Point(x=p["x"], y=p["y"]) for p in points]
        
        script = generate_draw_contour(layer_name, frame_number, point_objs, color_obj, thickness, closed, use_palette)
        await client.execute_lua(script, sprite_path)
        
        return json.dumps({"success": True})
    
    @mcp.tool()
    async def draw_rectangle(sprite_path: str, layer_name: str, frame_number: int, x: int, y: int, width: int, height: int, color: str, filled: bool = False, use_palette: bool = False) -> str:
        f"""Draw a rectangle with specified position and size.
        
        Args:
            sprite_path: Path to the Aseprite sprite file
            layer_name: Name of the layer to draw on
            frame_number: Frame number to draw on (1-based)
            x: X coordinate of rectangle top-left corner
            y: Y coordinate of rectangle top-left corner
            width: Width of rectangle in pixels
            height: Height of rectangle in pixels
            color: Hex color string in format #RRGGBB or #RRGGBBAA
            filled: Fill interior (true) or draw outline only (false)
            use_palette: Snap colors to nearest palette color (default: false)
        
        Returns:
            JSON with success status
        """
        if not layer_name:
            return json.dumps({"error": "layer_name cannot be empty"})
        if frame_number < 1:
            return json.dumps({"error": "frame_number must be at least 1"})
        if width < 1 or height < 1:
            return json.dumps({"error": "width and height must be at least 1"})
        
        try:
            color_obj = Color.from_hex(color)
        except ValueError:
            return json.dumps({"error": "Invalid color format"})
        
        script = generate_draw_rectangle(layer_name, frame_number, x, y, width, height, color_obj, filled, use_palette)
        await client.execute_lua(script, sprite_path)
        
        return json.dumps({"success": True})
    
    @mcp.tool()
    async def draw_circle(sprite_path: str, layer_name: str, frame_number: int, center_x: int, center_y: int, radius: int, color: str, filled: bool = False, use_palette: bool = False) -> str:
        f"""Draw a circle with specified center and radius.
        
        Args:
            sprite_path: Path to the Aseprite sprite file
            layer_name: Name of the layer to draw on
            frame_number: Frame number to draw on (1-based)
            center_x: X coordinate of circle center
            center_y: Y coordinate of circle center
            radius: Radius of circle in pixels
            color: Hex color string in format #RRGGBB or #RRGGBBAA
            filled: Fill interior (true) or draw outline only (false)
            use_palette: Snap colors to nearest palette color (default: false)
        
        Returns:
            JSON with success status
        """
        if not layer_name:
            return json.dumps({"error": "layer_name cannot be empty"})
        if frame_number < 1:
            return json.dumps({"error": "frame_number must be at least 1"})
        if radius < 1:
            return json.dumps({"error": "radius must be at least 1"})
        
        try:
            color_obj = Color.from_hex(color)
        except ValueError:
            return json.dumps({"error": "Invalid color format"})
        
        script = generate_draw_circle(layer_name, frame_number, center_x, center_y, radius, color_obj, filled, use_palette)
        await client.execute_lua(script, sprite_path)
        
        return json.dumps({"success": True})
    
    @mcp.tool()
    async def fill_area(sprite_path: str, layer_name: str, frame_number: int, x: int, y: int, color: str, tolerance: int = 0, use_palette: bool = False) -> str:
        f"""Flood fill from a starting point with specified color.
        
        Args:
            sprite_path: Path to the Aseprite sprite file
            layer_name: Name of the layer to draw on
            frame_number: Frame number to draw on (1-based)
            x: X coordinate of starting point
            y: Y coordinate of starting point
            color: Hex color string in format #RRGGBB or #RRGGBBAA
            tolerance: Color matching tolerance (0-255, default 0)
            use_palette: Snap colors to nearest palette color (default: false)
        
        Returns:
            JSON with success status
        """
        if not layer_name:
            return json.dumps({"error": "layer_name cannot be empty"})
        if frame_number < 1:
            return json.dumps({"error": "frame_number must be at least 1"})
        if tolerance < 0 or tolerance > 255:
            return json.dumps({"error": "tolerance must be 0-255"})
        
        try:
            color_obj = Color.from_hex(color)
        except ValueError:
            return json.dumps({"error": "Invalid color format"})
        
        script = generate_fill_area(layer_name, frame_number, x, y, color_obj, tolerance, use_palette)
        await client.execute_lua(script, sprite_path)
        
        return json.dumps({"success": True})

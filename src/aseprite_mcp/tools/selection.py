from __future__ import annotations

import json
from mcp.server.fastmcp import FastMCP

from aseprite_mcp.client import AsepriteClient
from aseprite_mcp.config import Config
from aseprite_mcp.lua.selection import (
    generate_select_rectangle,
    generate_select_ellipse,
    generate_select_all,
    generate_deselect,
    generate_move_selection,
    generate_cut_selection,
    generate_copy_selection,
    generate_paste_clipboard,
)


def register_selection_tools(mcp: FastMCP, client: AsepriteClient, config: Config) -> None:
    
    @mcp.tool()
    async def select_rectangle(sprite_path: str, x: int, y: int, width: int, height: int, mode: str = "replace") -> str:
        f"""Create a rectangular selection with specified mode.
        
        Args:
            sprite_path: Path to the Aseprite sprite file
            x: X coordinate of selection rectangle
            y: Y coordinate of selection rectangle
            width: Width of selection rectangle (minimum 1)
            height: Height of selection rectangle (minimum 1)
            mode: Selection mode (replace, add, subtract, or intersect, default: replace)
        
        Returns:
            JSON with success status
        """
        if width < 1:
            return json.dumps({"error": "width must be at least 1"})
        if height < 1:
            return json.dumps({"error": "height must be at least 1"})
        if mode not in ["replace", "add", "subtract", "intersect"]:
            return json.dumps({"error": "mode must be replace, add, subtract, or intersect"})
        
        script = generate_select_rectangle(x, y, width, height, mode)
        await client.execute_lua(script, sprite_path)
        
        return json.dumps({"success": True})
    
    @mcp.tool()
    async def select_ellipse(sprite_path: str, x: int, y: int, width: int, height: int, mode: str = "replace") -> str:
        f"""Create an elliptical selection with specified mode.
        
        Args:
            sprite_path: Path to the Aseprite sprite file
            x: X coordinate of selection ellipse bounding box
            y: Y coordinate of selection ellipse bounding box
            width: Width of selection ellipse (minimum 1)
            height: Height of selection ellipse (minimum 1)
            mode: Selection mode (replace, add, subtract, or intersect, default: replace)
        
        Returns:
            JSON with success status
        """
        if width < 1:
            return json.dumps({"error": "width must be at least 1"})
        if height < 1:
            return json.dumps({"error": "height must be at least 1"})
        if mode not in ["replace", "add", "subtract", "intersect"]:
            return json.dumps({"error": "mode must be replace, add, subtract, or intersect"})
        
        script = generate_select_ellipse(x, y, width, height, mode)
        await client.execute_lua(script, sprite_path)
        
        return json.dumps({"success": True})
    
    @mcp.tool()
    async def select_all(sprite_path: str) -> str:
        f"""Select the entire canvas.
        
        Args:
            sprite_path: Path to the Aseprite sprite file
        
        Returns:
            JSON with success status
        """
        script = generate_select_all()
        await client.execute_lua(script, sprite_path)
        
        return json.dumps({"success": True})
    
    @mcp.tool()
    async def deselect(sprite_path: str) -> str:
        f"""Clear the current selection.
        
        Args:
            sprite_path: Path to the Aseprite sprite file
        
        Returns:
            JSON with success status
        """
        script = generate_deselect()
        await client.execute_lua(script, sprite_path)
        
        return json.dumps({"success": True})
    
    @mcp.tool()
    async def move_selection(sprite_path: str, dx: int, dy: int) -> str:
        f"""Move the current selection by a specified offset.
        
        Args:
            sprite_path: Path to the Aseprite sprite file
            dx: Horizontal offset in pixels (can be negative)
            dy: Vertical offset in pixels (can be negative)
        
        Returns:
            JSON with success status
        """
        script = generate_move_selection(dx, dy)
        await client.execute_lua(script, sprite_path)
        
        return json.dumps({"success": True})
    
    @mcp.tool()
    async def cut_selection(sprite_path: str, layer_name: str, frame_number: int) -> str:
        f"""Cut the selected pixels to clipboard.
        
        Args:
            sprite_path: Path to the Aseprite sprite file
            layer_name: Name of the layer to cut from
            frame_number: Frame number to cut from (1-based index)
        
        Returns:
            JSON with success status
        """
        if not layer_name:
            return json.dumps({"error": "layer_name cannot be empty"})
        if frame_number < 1:
            return json.dumps({"error": "frame_number must be at least 1"})
        
        script = generate_cut_selection(layer_name, frame_number)
        await client.execute_lua(script, sprite_path)
        
        return json.dumps({"success": True})
    
    @mcp.tool()
    async def copy_selection(sprite_path: str) -> str:
        f"""Copy the selected pixels to clipboard without removing them.
        
        Args:
            sprite_path: Path to the Aseprite sprite file
        
        Returns:
            JSON with success status
        """
        script = generate_copy_selection()
        await client.execute_lua(script, sprite_path)
        
        return json.dumps({"success": True})
    
    @mcp.tool()
    async def paste_clipboard(sprite_path: str, layer_name: str, frame_number: int, x: int = None, y: int = None) -> str:
        f"""Paste clipboard content onto the specified layer and frame.
        
        Args:
            sprite_path: Path to the Aseprite sprite file
            layer_name: Name of the layer to paste onto
            frame_number: Frame number to paste onto (1-based index)
            x: X coordinate for paste position (optional)
            y: Y coordinate for paste position (optional)
        
        Returns:
            JSON with success status
        """
        if not layer_name:
            return json.dumps({"error": "layer_name cannot be empty"})
        if frame_number < 1:
            return json.dumps({"error": "frame_number must be at least 1"})
        
        script = generate_paste_clipboard(layer_name, frame_number, x, y)
        await client.execute_lua(script, sprite_path)
        
        return json.dumps({"success": True})

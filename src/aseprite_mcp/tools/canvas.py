from __future__ import annotations

import json
import os
import time
from mcp.server.fastmcp import FastMCP

from aseprite_mcp.client import AsepriteClient
from aseprite_mcp.config import Config
from aseprite_mcp.lua.canvas import (
    generate_create_sprite,
    generate_add_layer,
    generate_add_frame,
    generate_delete_layer,
    generate_delete_frame,
    generate_flatten_layers,
    generate_get_sprite_info,
)
from aseprite_mcp.tools.common import ColorMode


def register_canvas_tools(mcp: FastMCP, client: AsepriteClient, config: Config) -> None:
    
    @mcp.tool()
    async def create_canvas(width: int, height: int, color_mode: str = "rgb") -> str:
        f"""Create a new Aseprite sprite.
        
        Args:
            width: Canvas width in pixels (1-65535)
            height: Canvas height in pixels (1-65535)
            color_mode: Color mode (rgb, grayscale, or indexed)
        
        Returns:
            JSON with file_path to the created sprite
        """
        if not 1 <= width <= 65535:
            return json.dumps({"error": "width must be 1-65535"})
        if not 1 <= height <= 65535:
            return json.dumps({"error": "height must be 1-65535"})
        if color_mode not in ["rgb", "grayscale", "indexed"]:
            return json.dumps({"error": "color_mode must be rgb, grayscale, or indexed"})
        
        color_mode_enum = ColorMode.RGB if color_mode == "rgb" else (ColorMode.GRAYSCALE if color_mode == "grayscale" else ColorMode.INDEXED)
        
        filename = os.path.join(config.temp_dir, f"sprite-{int(time.time() * 1000)}.aseprite")
        script = generate_create_sprite(width, height, color_mode_enum, filename)
        
        result = await client.execute_lua(script, "")
        file_path = result.strip()
        
        return json.dumps({"file_path": file_path})
    
    @mcp.tool()
    async def add_layer(sprite_path: str, layer_name: str) -> str:
        f"""Add a new layer to an existing sprite.
        
        Args:
            sprite_path: Path to the Aseprite sprite file
            layer_name: Name for the new layer
        
        Returns:
            JSON with success status
        """
        if not layer_name:
            return json.dumps({"error": "layer_name cannot be empty"})
        
        script = generate_add_layer(layer_name)
        await client.execute_lua(script, sprite_path)
        
        return json.dumps({"success": True})
    
    @mcp.tool()
    async def add_frame(sprite_path: str, duration_ms: int) -> str:
        f"""Add a new animation frame to the sprite.
        
        Args:
            sprite_path: Path to the Aseprite sprite file
            duration_ms: Frame duration in milliseconds (1-65535)
        
        Returns:
            JSON with frame_number (1-based index)
        """
        if duration_ms < 1 or duration_ms > 65535:
            return json.dumps({"error": "duration_ms must be 1-65535"})
        
        script = generate_add_frame(duration_ms)
        result = await client.execute_lua(script, sprite_path)
        
        try:
            frame_number = int(result.strip())
        except ValueError:
            return json.dumps({"error": "Failed to parse frame number"})
        
        return json.dumps({"frame_number": frame_number})
    
    @mcp.tool()
    async def delete_layer(sprite_path: str, layer_name: str) -> str:
        f"""Delete a layer from an existing sprite.
        
        Args:
            sprite_path: Path to the Aseprite sprite file
            layer_name: Name of the layer to delete
        
        Returns:
            JSON with success status
        """
        script = generate_delete_layer(layer_name)
        await client.execute_lua(script, sprite_path)
        
        return json.dumps({"success": True})
    
    @mcp.tool()
    async def delete_frame(sprite_path: str, frame_number: int) -> str:
        f"""Delete a frame from an existing sprite.
        
        Args:
            sprite_path: Path to the Aseprite sprite file
            frame_number: Frame number to delete (1-based)
        
        Returns:
            JSON with success status
        """
        script = generate_delete_frame(frame_number)
        await client.execute_lua(script, sprite_path)
        
        return json.dumps({"success": True})
    
    @mcp.tool()
    async def flatten_layers(sprite_path: str) -> str:
        f"""Flatten all layers in a sprite into a single layer.
        
        Args:
            sprite_path: Path to the Aseprite sprite file
        
        Returns:
            JSON with success status
        """
        script = generate_flatten_layers()
        await client.execute_lua(script, sprite_path)
        
        return json.dumps({"success": True})
    
    @mcp.tool()
    async def get_sprite_info(sprite_path: str) -> str:
        f"""Retrieve metadata about an existing sprite file.
        
        Args:
            sprite_path: Path to the Aseprite sprite file
        
        Returns:
            JSON with sprite metadata (width, height, color_mode, frame_count, layer_count, layers)
        """
        script = generate_get_sprite_info()
        result = await client.execute_lua(script, sprite_path)
        
        try:
            info = json.loads(result)
        except json.JSONDecodeError:
            return json.dumps({"error": "Failed to parse sprite info"})
        
        return json.dumps(info)

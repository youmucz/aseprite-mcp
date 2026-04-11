from __future__ import annotations

import json
from mcp.server.fastmcp import FastMCP

from aseprite_mcp.client import AsepriteClient
from aseprite_mcp.config import Config
from aseprite_mcp.lua.animation import (
    generate_set_frame_duration,
    generate_create_tag,
    generate_delete_tag,
    generate_duplicate_frame,
    generate_link_cel,
)


def register_animation_tools(mcp: FastMCP, client: AsepriteClient, config: Config) -> None:
    
    @mcp.tool()
    async def set_frame_duration(sprite_path: str, frame_number: int, duration_ms: int) -> str:
        f"""Set the duration of an existing animation frame in milliseconds.
        
        Args:
            sprite_path: Path to the Aseprite sprite file
            frame_number: Frame number to modify (1-based)
            duration_ms: Frame duration in milliseconds (1-65535)
        
        Returns:
            JSON with success status
        """
        if frame_number < 1:
            return json.dumps({"error": "frame_number must be at least 1"})
        if duration_ms < 1 or duration_ms > 65535:
            return json.dumps({"error": "duration_ms must be 1-65535"})
        
        script = generate_set_frame_duration(frame_number, duration_ms)
        await client.execute_lua(script, sprite_path)
        
        return json.dumps({"success": True})
    
    @mcp.tool()
    async def create_tag(sprite_path: str, tag_name: str, from_frame: int, to_frame: int, direction: str = "forward") -> str:
        f"""Create an animation tag to define a named frame range with playback direction.
        
        Args:
            sprite_path: Path to the Aseprite sprite file
            tag_name: Name for the animation tag
            from_frame: Starting frame number (1-based, inclusive)
            to_frame: Ending frame number (1-based, inclusive)
            direction: Playback direction (forward, reverse, or pingpong)
        
        Returns:
            JSON with success status
        """
        if not tag_name:
            return json.dumps({"error": "tag_name cannot be empty"})
        if from_frame < 1:
            return json.dumps({"error": "from_frame must be at least 1"})
        if to_frame < from_frame:
            return json.dumps({"error": "to_frame must be >= from_frame"})
        if direction not in ["forward", "reverse", "pingpong"]:
            return json.dumps({"error": "direction must be forward, reverse, or pingpong"})
        
        script = generate_create_tag(tag_name, from_frame, to_frame, direction)
        await client.execute_lua(script, sprite_path)
        
        return json.dumps({"success": True})
    
    @mcp.tool()
    async def delete_tag(sprite_path: str, tag_name: str) -> str:
        f"""Delete an animation tag by name.
        
        Args:
            sprite_path: Path to the Aseprite sprite file
            tag_name: Name of the tag to delete
        
        Returns:
            JSON with success status
        """
        if not tag_name:
            return json.dumps({"error": "tag_name cannot be empty"})
        
        script = generate_delete_tag(tag_name)
        await client.execute_lua(script, sprite_path)
        
        return json.dumps({"success": True})
    
    @mcp.tool()
    async def duplicate_frame(sprite_path: str, source_frame: int, insert_after: int = 0) -> str:
        f"""Duplicate an existing frame and insert it at the specified position.
        
        Args:
            sprite_path: Path to the Aseprite sprite file
            source_frame: Frame number to duplicate (1-based)
            insert_after: Insert duplicated frame after this frame number (1-based, 0 = insert at end)
        
        Returns:
            JSON with new_frame_number (1-based index)
        """
        if source_frame < 1:
            return json.dumps({"error": "source_frame must be at least 1"})
        if insert_after < 0:
            return json.dumps({"error": "insert_after must be non-negative"})
        
        script = generate_duplicate_frame(source_frame, insert_after)
        result = await client.execute_lua(script, sprite_path)
        
        try:
            new_frame_number = int(result.strip())
        except ValueError:
            return json.dumps({"error": "Failed to parse new frame number"})
        
        return json.dumps({"new_frame_number": new_frame_number})
    
    @mcp.tool()
    async def link_cel(sprite_path: str, layer_name: str, source_frame: int, target_frame: int) -> str:
        f"""Create a linked cel that references another cel's image data.
        
        Args:
            sprite_path: Path to the Aseprite sprite file
            layer_name: Name of the layer
            source_frame: Source frame with the cel to link (1-based)
            target_frame: Target frame where linked cel will be created (1-based)
        
        Returns:
            JSON with success status
        """
        if not layer_name:
            return json.dumps({"error": "layer_name cannot be empty"})
        if source_frame < 1:
            return json.dumps({"error": "source_frame must be at least 1"})
        if target_frame < 1:
            return json.dumps({"error": "target_frame must be at least 1"})
        if source_frame == target_frame:
            return json.dumps({"error": "source_frame and target_frame cannot be the same"})
        
        script = generate_link_cel(layer_name, source_frame, target_frame)
        await client.execute_lua(script, sprite_path)
        
        return json.dumps({"success": True})

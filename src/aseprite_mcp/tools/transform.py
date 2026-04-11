from __future__ import annotations

import json
from mcp.server.fastmcp import FastMCP

from aseprite_mcp.client import AsepriteClient
from aseprite_mcp.config import Config
from aseprite_mcp.lua.transform import (
    generate_flip_sprite,
    generate_rotate_sprite,
    generate_scale_sprite,
    generate_crop_sprite,
    generate_resize_canvas,
    generate_apply_outline,
    generate_downsample_image,
)
from aseprite_mcp.tools.common import Color


def register_transform_tools(
    mcp: FastMCP, client: AsepriteClient, config: Config
) -> None:

    @mcp.tool()
    async def flip_sprite(
        sprite_path: str, direction: str, target: str = "sprite"
    ) -> str:
        f"""Flip a sprite, layer, or cel horizontally or vertically.
        
        Args:
            sprite_path: Path to the Aseprite sprite file
            direction: Flip direction: horizontal or vertical
            target: What to flip: sprite, layer, or cel (default: sprite)
        
        Returns:
            JSON with success status
        """
        if direction not in ["horizontal", "vertical"]:
            return json.dumps({"error": "direction must be 'horizontal' or 'vertical'"})

        if target not in ["sprite", "layer", "cel"]:
            return json.dumps({"error": "target must be 'sprite', 'layer', or 'cel'"})

        script = generate_flip_sprite(direction, target)
        await client.execute_lua(script, sprite_path)

        return json.dumps({"success": True})

    @mcp.tool()
    async def rotate_sprite(
        sprite_path: str, angle: int, target: str = "sprite"
    ) -> str:
        f"""Rotate a sprite, layer, or cel by 90, 180, or 270 degrees clockwise.
        
        Args:
            sprite_path: Path to the Aseprite sprite file
            angle: Rotation angle: 90, 180, or 270 degrees
            target: What to rotate: sprite, layer, or cel (default: sprite)
        
        Returns:
            JSON with success status
        """
        if angle not in [90, 180, 270]:
            return json.dumps({"error": "angle must be 90, 180, or 270"})

        if target not in ["sprite", "layer", "cel"]:
            return json.dumps({"error": "target must be 'sprite', 'layer', or 'cel'"})

        script = generate_rotate_sprite(angle, target)
        await client.execute_lua(script, sprite_path)

        return json.dumps({"success": True})

    @mcp.tool()
    async def scale_sprite(
        sprite_path: str, scale_x: float, scale_y: float, algorithm: str = "nearest"
    ) -> str:
        f"""Scale a sprite by specified X and Y factors using a chosen algorithm.
        
        Args:
            sprite_path: Path to the Aseprite sprite file
            scale_x: Horizontal scale factor (0.01 to 100.0)
            scale_y: Vertical scale factor (0.01 to 100.0)
            algorithm: Scaling algorithm: nearest, bilinear, or rotsprite (default: nearest)
        
        Returns:
            JSON with success status and new dimensions
        """
        if not 0.01 <= scale_x <= 100.0:
            return json.dumps({"error": "scale_x must be between 0.01 and 100.0"})

        if not 0.01 <= scale_y <= 100.0:
            return json.dumps({"error": "scale_y must be between 0.01 and 100.0"})

        if algorithm not in ["nearest", "bilinear", "rotsprite"]:
            return json.dumps(
                {"error": "algorithm must be 'nearest', 'bilinear', or 'rotsprite'"}
            )

        script = generate_scale_sprite(scale_x, scale_y, algorithm)
        result = await client.execute_lua(script, sprite_path)

        try:
            data = json.loads(result)
        except json.JSONDecodeError:
            return json.dumps({"error": "failed to parse scale result"})

        return json.dumps(data)

    @mcp.tool()
    async def crop_sprite(
        sprite_path: str, x: int, y: int, width: int, height: int
    ) -> str:
        f"""Crop a sprite to a specified rectangular region.
        
        Args:
            sprite_path: Path to the Aseprite sprite file
            x: Crop region X coordinate
            y: Crop region Y coordinate
            width: Crop region width (must be positive)
            height: Crop region height (must be positive)
        
        Returns:
            JSON with success status
        """
        if x < 0 or y < 0:
            return json.dumps({"error": "crop position must be non-negative"})

        if width <= 0 or height <= 0:
            return json.dumps({"error": "crop dimensions must be positive"})

        script = generate_crop_sprite(x, y, width, height)
        await client.execute_lua(script, sprite_path)

        return json.dumps({"success": True})

    @mcp.tool()
    async def resize_canvas(
        sprite_path: str, width: int, height: int, anchor: str = "center"
    ) -> str:
        f"""Resize the canvas without scaling content.
        
        Args:
            sprite_path: Path to the Aseprite sprite file
            width: New canvas width (1-65535)
            height: New canvas height (1-65535)
            anchor: Anchor position: center, top_left, top_right, bottom_left, or bottom_right (default: center)
        
        Returns:
            JSON with success status
        """
        if not 1 <= width <= 65535:
            return json.dumps({"error": "width must be between 1 and 65535"})

        if not 1 <= height <= 65535:
            return json.dumps({"error": "height must be between 1 and 65535"})

        valid_anchors = [
            "center",
            "top_left",
            "top_right",
            "bottom_left",
            "bottom_right",
        ]
        if anchor not in valid_anchors:
            return json.dumps({"error": f"anchor must be {', '.join(valid_anchors)}"})

        script = generate_resize_canvas(width, height, anchor)
        await client.execute_lua(script, sprite_path)

        return json.dumps({"success": True})

    @mcp.tool()
    async def apply_outline(
        sprite_path: str, layer_name: str, frame_number: int, color: str, thickness: int
    ) -> str:
        f"""Apply an outline effect to a layer at a specified frame.
        
        Args:
            sprite_path: Path to the Aseprite sprite file
            layer_name: Name of the layer to apply outline to
            frame_number: Frame number (1-based index)
            color: Outline color in hex format (#RRGGBB or #RRGGBBAA)
            thickness: Outline thickness in pixels (1-10)
        
        Returns:
            JSON with success status
        """
        if frame_number < 1:
            return json.dumps({"error": "frame_number must be >= 1"})

        if not 1 <= thickness <= 10:
            return json.dumps({"error": "thickness must be between 1 and 10"})

        try:
            color_obj = Color.from_hex(color)
        except ValueError:
            return json.dumps(
                {"error": "invalid color format, expected #RRGGBB or #RRGGBBAA"}
            )

        script = generate_apply_outline(layer_name, frame_number, color_obj, thickness)
        await client.execute_lua(script, sprite_path)

        return json.dumps({"success": True})

    @mcp.tool()
    async def downsample_image(
        source_path: str, output_path: str, target_width: int, target_height: int
    ) -> str:
        f"""Downsample an image to a smaller size for pixel art conversion. Loads the source image, resizes it to the specified target dimensions using bilinear interpolation, and saves the result. Useful for converting high-resolution reference images into pixel art base sprites.

        Args:
            source_path: Path to source image file (.png, .jpg, .gif, .bmp, .aseprite)
            output_path: Output path for the downsampled .aseprite file
            target_width: Target width in pixels (1-65535)
            target_height: Target height in pixels (1-65535)

        Returns:
            JSON with output_path of the downsampled file
        """
        if not 1 <= target_width <= 65535:
            return json.dumps({"error": "target_width must be between 1 and 65535"})

        if not 1 <= target_height <= 65535:
            return json.dumps({"error": "target_height must be between 1 and 65535"})

        if not output_path:
            return json.dumps({"error": "output_path cannot be empty"})

        import os

        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        script = generate_downsample_image(
            source_path, output_path, target_width, target_height
        )
        result = await client.execute_lua(script, "")

        file_path = result.strip()
        return json.dumps({"output_path": file_path})

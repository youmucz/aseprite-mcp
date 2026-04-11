from __future__ import annotations

import json
from typing import TYPE_CHECKING
from mcp.server.fastmcp import FastMCP

from aseprite_mcp.client import AsepriteClient
from aseprite_mcp.config import Config
from aseprite_mcp.lua.palette import (
    generate_get_palette,
    generate_set_palette,
    generate_set_palette_color,
    generate_add_palette_color,
    generate_sort_palette,
    generate_apply_shading,
)

if TYPE_CHECKING:
    from typing import Any


def register_palette_tools(mcp: FastMCP, client: AsepriteClient, config: Config) -> None:
    
    @mcp.tool()
    async def get_palette(sprite_path: str) -> str:
        """Retrieve the current sprite palette as an array of hex colors. Returns both the color array and palette size. Useful for inspecting existing palettes before modification.
        
        Args:
            sprite_path: Path to the Aseprite sprite file
        
        Returns:
            JSON with colors array and size (e.g., {"colors":["#RRGGBB",...],"size":N})
        """
        script = generate_get_palette()
        result = await client.execute_lua(script, sprite_path)
        
        try:
            parsed = json.loads(result)
        except json.JSONDecodeError:
            return json.dumps({"error": "Failed to parse palette output"})
        
        return json.dumps(parsed)
    
    @mcp.tool()
    async def set_palette(sprite_path: str, colors: list[str]) -> str:
        """Set the sprite's color palette to the specified colors. Useful for applying extracted palettes from analyze_reference or creating custom limited palettes for pixel art. Colors should be in #RRGGBB hex format.
        
        Args:
            sprite_path: Path to the Aseprite sprite file
            colors: Array of hex colors to set as palette (#RRGGBB format)
        
        Returns:
            JSON with success status
        """
        if len(colors) == 0:
            return json.dumps({"error": "colors array cannot be empty"})
        
        if len(colors) > 256:
            return json.dumps({"error": "palette can have at most 256 colors"})
        
        for i, color in enumerate(colors):
            if not color.startswith("#") or len(color) not in [7, 9]:
                return json.dumps({"error": f"invalid color at index {i}: {color} (expected #RRGGBB format)"})
        
        script = generate_set_palette(colors)
        await client.execute_lua(script, sprite_path)
        
        return json.dumps({"success": True})
    
    @mcp.tool()
    async def set_palette_color(sprite_path: str, index: int, color: str) -> str:
        """Set a specific palette index to a color. Index must be within the current palette range (0 to palette size - 1). Useful for modifying individual palette entries.
        
        Args:
            sprite_path: Path to the Aseprite sprite file
            index: Palette index (0-255)
            color: Hex color to set (#RRGGBB format)
        
        Returns:
            JSON with success status
        """
        if index < 0 or index > 255:
            return json.dumps({"error": "index must be between 0 and 255"})
        
        if not color.startswith("#") or len(color) not in [7, 9]:
            return json.dumps({"error": f"invalid color: {color} (expected #RRGGBB format)"})
        
        script = generate_set_palette_color(index, color)
        await client.execute_lua(script, sprite_path)
        
        return json.dumps({"success": True})
    
    @mcp.tool()
    async def add_palette_color(sprite_path: str, color: str) -> str:
        """Add a new color to the palette. The palette will be resized to accommodate the new color. Returns the index of the newly added color. Maximum palette size is 256 colors.
        
        Args:
            sprite_path: Path to the Aseprite sprite file
            color: Hex color to add (#RRGGBB format)
        
        Returns:
            JSON with color_index of the newly added color
        """
        if not color.startswith("#") or len(color) not in [7, 9]:
            return json.dumps({"error": f"invalid color: {color} (expected #RRGGBB format)"})
        
        script = generate_add_palette_color(color)
        result = await client.execute_lua(script, sprite_path)
        
        try:
            parsed = json.loads(result)
        except json.JSONDecodeError:
            return json.dumps({"error": "Failed to parse add color output"})
        
        return json.dumps(parsed)
    
    @mcp.tool()
    async def sort_palette(sprite_path: str, method: str, ascending: bool = True) -> str:
        """Sort the palette by hue, saturation, brightness, or luminance. Can sort in ascending or descending order. Useful for organizing palettes for easier color selection.
        
        Args:
            sprite_path: Path to the Aseprite sprite file
            method: Sort method: hue, saturation, brightness, or luminance
            ascending: Sort in ascending order (default: true)
        
        Returns:
            JSON with success status
        """
        valid_methods = ["hue", "saturation", "brightness", "luminance"]
        if method not in valid_methods:
            return json.dumps({"error": f"invalid sort method: {method} (must be one of: hue, saturation, brightness, luminance)"})
        
        script = generate_sort_palette(method, ascending)
        await client.execute_lua(script, sprite_path)
        
        return json.dumps({"success": True})
    
    @mcp.tool()
    async def apply_shading(sprite_path: str, layer_name: str, frame_number: int, x: int, y: int, width: int, height: int, palette: list[str], light_direction: str, intensity: float, style: str) -> str:
        """Apply palette-constrained shading to a region based on light direction. Automatically adjusts pixel colors to create highlights and shadows while staying within the provided palette. Supports smooth, hard, and pillow shading styles. Essential for adding depth and dimension to pixel art.
        
        Args:
            sprite_path: Path to the Aseprite sprite file
            layer_name: Name of the layer to apply shading to
            frame_number: Frame number (1-based index)
            x: X coordinate of top-left corner of region
            y: Y coordinate of top-left corner of region
            width: Width of region
            height: Height of region
            palette: Array of hex colors ordered darkest to lightest (#RRGGBB format)
            light_direction: Light direction: top_left, top, top_right, left, right, bottom_left, bottom, bottom_right
            intensity: Shading intensity (0.0-1.0)
            style: Shading style: pillow, smooth, or hard
        
        Returns:
            JSON with success status
        """
        if len(palette) == 0:
            return json.dumps({"error": "palette array cannot be empty"})
        
        if len(palette) > 256:
            return json.dumps({"error": "palette can have at most 256 colors"})
        
        for i, color in enumerate(palette):
            if not color.startswith("#") or len(color) not in [7, 9]:
                return json.dumps({"error": f"invalid palette color at index {i}: {color} (expected #RRGGBB format)"})
        
        valid_directions = ["top_left", "top", "top_right", "left", "right", "bottom_left", "bottom", "bottom_right"]
        if light_direction not in valid_directions:
            return json.dumps({"error": f"invalid light direction: {light_direction} (must be one of: top_left, top, top_right, left, right, bottom_left, bottom, bottom_right)"})
        
        if intensity < 0.0 or intensity > 1.0:
            return json.dumps({"error": "intensity must be between 0.0 and 1.0"})
        
        valid_styles = ["pillow", "smooth", "hard"]
        if style not in valid_styles:
            return json.dumps({"error": f"invalid style: {style} (must be one of: pillow, smooth, hard)"})
        
        if width <= 0 or height <= 0:
            return json.dumps({"error": "region dimensions must be positive"})
        
        script = generate_apply_shading(layer_name, frame_number, x, y, width, height, palette, light_direction, intensity, style)
        await client.execute_lua(script, sprite_path)
        
        return json.dumps({"success": True})
    
    @mcp.tool()
    async def analyze_palette_harmonies(palette: list[str]) -> str:
        """Analyze color palette for harmonious relationships. Identifies complementary pairs (opposite colors on color wheel), triadic sets (3 evenly spaced colors), analogous groups (adjacent colors), and color temperature (warm/cool/neutral). Essential for creating professional, cohesive pixel art palettes based on color theory.
        
        Args:
            palette: Array of hex colors to analyze (#RRGGBB format)
        
        Returns:
            JSON with complementary, triadic, analogous, and temperature analysis
        """
        if len(palette) == 0:
            return json.dumps({"error": "palette array cannot be empty"})
        
        if len(palette) > 256:
            return json.dumps({"error": "palette can have at most 256 colors"})
        
        for i, color in enumerate(palette):
            if not color.startswith("#") or len(color) not in [7, 9]:
                return json.dumps({"error": f"invalid color at index {i}: {color} (expected #RRGGBB format)"})
        
        result = _analyze_palette_harmonies(palette)
        return json.dumps(result)


def _hex_to_hsl(hex_color: str) -> tuple[float, float, float]:
    hex_color = hex_color.lstrip("#")
    
    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0
    
    max_val = max(r, g, b)
    min_val = min(r, g, b)
    delta = max_val - min_val
    
    l = (max_val + min_val) / 2.0
    
    if delta == 0:
        h = 0.0
        s = 0.0
    else:
        if l < 0.5:
            s = delta / (max_val + min_val)
        else:
            s = delta / (2.0 - max_val - min_val)
        
        if max_val == r:
            h = ((g - b) / delta)
            if g < b:
                h += 6.0
        elif max_val == g:
            h = ((b - r) / delta) + 2.0
        else:
            h = ((r - g) / delta) + 4.0
        
        h *= 60.0
    
    return h, s, l


def _normalize_hue_diff(diff: float) -> float:
    while diff < 0:
        diff += 360
    while diff > 360:
        diff -= 360
    if diff > 180:
        diff = 360 - diff
    return diff


def _is_near(value: float, target: float, tolerance: float) -> bool:
    return abs(value - target) <= tolerance


def _analyze_palette_harmonies(palette: list[str]) -> dict[str, Any]:
    result = {
        "complementary": [],
        "triadic": [],
        "analogous": [],
        "temperature": {
            "warm_colors": [],
            "cool_colors": [],
            "neutral_colors": [],
            "dominant": "neutral",
            "description": ""
        }
    }
    
    colors_hsl = []
    for hex_color in palette:
        h, s, l = _hex_to_hsl(hex_color)
        colors_hsl.append({"hex": hex_color, "h": h, "s": s, "l": l})
    
    for i in range(len(colors_hsl)):
        for j in range(i + 1, len(colors_hsl)):
            hue_diff = _normalize_hue_diff(colors_hsl[i]["h"] - colors_hsl[j]["h"])
            if 150 <= hue_diff <= 210:
                contrast = (colors_hsl[i]["l"] + colors_hsl[j]["l"]) / 2.0
                result["complementary"].append({
                    "color1": colors_hsl[i]["hex"],
                    "color2": colors_hsl[j]["hex"],
                    "contrast": contrast,
                    "description": f"High contrast pair ({hue_diff:.0f}° apart)"
                })
    
    for i in range(len(colors_hsl)):
        for j in range(i + 1, len(colors_hsl)):
            for k in range(j + 1, len(colors_hsl)):
                diff1 = _normalize_hue_diff(colors_hsl[j]["h"] - colors_hsl[i]["h"])
                diff2 = _normalize_hue_diff(colors_hsl[k]["h"] - colors_hsl[j]["h"])
                diff3 = _normalize_hue_diff(colors_hsl[i]["h"] - colors_hsl[k]["h"])
                
                if _is_near(diff1, 120, 30) and _is_near(diff2, 120, 30) and _is_near(diff3, 120, 30):
                    avg_diff = (diff1 + diff2 + diff3) / 3.0
                    balance = 1.0 - (abs(avg_diff - 120) / 120.0)
                    result["triadic"].append({
                        "colors": [colors_hsl[i]["hex"], colors_hsl[j]["hex"], colors_hsl[k]["hex"]],
                        "balance": balance,
                        "description": f"Balanced triadic set ({balance:.1f} balance)"
                    })
    
    for i in range(len(colors_hsl)):
        analogous = [colors_hsl[i]["hex"]]
        for j in range(len(colors_hsl)):
            if i != j:
                hue_diff = _normalize_hue_diff(colors_hsl[j]["h"] - colors_hsl[i]["h"])
                if 0 < hue_diff <= 60:
                    analogous.append(colors_hsl[j]["hex"])
        
        if len(analogous) >= 3:
            harmony = 1.0 / len(analogous)
            result["analogous"].append({
                "colors": analogous,
                "harmony": harmony,
                "description": f"Harmonious adjacent colors ({len(analogous)} colors)"
            })
    
    warm = []
    cool = []
    neutral = []
    
    for color in colors_hsl:
        if color["s"] < 0.2:
            neutral.append(color["hex"])
        elif (0 <= color["h"] <= 60) or (300 <= color["h"] <= 360):
            warm.append(color["hex"])
        elif 180 <= color["h"] <= 300:
            cool.append(color["hex"])
        else:
            neutral.append(color["hex"])
    
    dominant = "neutral"
    if len(warm) > len(cool) and len(warm) > len(neutral):
        dominant = "warm"
    elif len(cool) > len(warm) and len(cool) > len(neutral):
        dominant = "cool"
    
    result["temperature"]["warm_colors"] = warm
    result["temperature"]["cool_colors"] = cool
    result["temperature"]["neutral_colors"] = neutral
    result["temperature"]["dominant"] = dominant
    result["temperature"]["description"] = f"Palette is predominantly {dominant} ({len(warm)} warm, {len(cool)} cool, {len(neutral)} neutral)"
    
    return result

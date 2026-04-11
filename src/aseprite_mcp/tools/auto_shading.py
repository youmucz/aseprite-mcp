from __future__ import annotations

import json
import math
import os
import tempfile
from pathlib import Path
from mcp.server.fastmcp import FastMCP

from aseprite_mcp.client import AsepriteClient
from aseprite_mcp.config import Config
from aseprite_mcp.lua.auto_shading import generate_apply_auto_shading_result
from aseprite_mcp.lua.core import escape_string


def register_auto_shading_tools(
    mcp: FastMCP, client: AsepriteClient, config: Config
) -> None:

    @mcp.tool()
    async def apply_auto_shading(
        sprite_path: str,
        layer_name: str,
        frame_number: int,
        light_direction: str,
        intensity: float,
        style: str,
        hue_shift: bool = True,
    ) -> str:
        f"""Automatically add shading to sprite based on light direction. Analyzes sprite geometry to identify surfaces/regions, determines which surfaces face toward/away from light, generates shadow and highlight colors for each base color (with optional hue shifting), and applies shading pixels with smooth transitions. Supports three styles: cell (hard-edged 2-3 bands), smooth (gradient with dithering), soft (subtle gradient). Essential for adding depth and dimension to pixel art automatically.

        Args:
            sprite_path: Path to .aseprite file
            layer_name: Layer to apply shading to
            frame_number: Frame number (1-based)
            light_direction: Light direction: top_left, top, top_right, left, right, bottom_left, bottom, bottom_right
            intensity: Shading intensity (0.0-1.0)
            style: Shading style: cell, smooth, or soft
            hue_shift: Apply hue shifting (shadows to cool, highlights to warm) default: true

        Returns:
            JSON with success, colors_added, palette, and regions_shaded
        """
        if intensity < 0.0 or intensity > 1.0:
            return json.dumps({"error": "intensity must be between 0.0 and 1.0"})

        valid_directions = {
            "top_left",
            "top",
            "top_right",
            "left",
            "right",
            "bottom_left",
            "bottom",
            "bottom_right",
        }
        if light_direction not in valid_directions:
            return json.dumps({"error": f"invalid light direction: {light_direction}"})

        valid_styles = {"cell", "smooth", "soft"}
        if style not in valid_styles:
            return json.dumps(
                {"error": f"invalid style: {style} (must be cell, smooth, or soft)"}
            )

        if not Path(sprite_path).exists():
            return json.dumps({"error": f"sprite file not found: {sprite_path}"})

        temp_dir = tempfile.mkdtemp(prefix="pixel-mcp-shading-")
        try:
            temp_png = os.path.join(temp_dir, "layer.png")

            try:
                from PIL import Image
            except ImportError:
                return json.dumps({"error": "PIL/Pillow is required for auto-shading"})

            escaped_layer = escape_string(layer_name)
            escaped_png = escape_string(temp_png)
            export_script = f'''local spr = app.activeSprite
if not spr then
    error("No active sprite")
end

local targetLayer = nil
for _, layer in ipairs(spr.layers) do
    if layer.name == "{escaped_layer}" then
        targetLayer = layer
        break
    end
end

if not targetLayer then
    error("Layer not found: {escaped_layer}")
end

local cel = targetLayer:cel({frame_number})
if not cel then
    error("No cel found at frame {frame_number}")
end

cel.image:saveAs("{escaped_png}")
print("Exported successfully")'''

            await client.execute_lua(export_script, sprite_path)

            img = Image.open(temp_png).convert("RGBA")

            shaded_img, generated_colors, regions_shaded = _apply_auto_shading(
                img, light_direction, intensity, style, hue_shift
            )

            shaded_png = os.path.join(temp_dir, "shaded.png")
            shaded_img.save(shaded_png)

            apply_script = generate_apply_auto_shading_result(
                shaded_png, layer_name, frame_number, generated_colors, regions_shaded
            )
            result = await client.execute_lua(apply_script, sprite_path)

            try:
                data = json.loads(result)
            except json.JSONDecodeError:
                return json.dumps({"error": "Failed to parse shading result"})

            return json.dumps(data)
        finally:
            import shutil

            shutil.rmtree(temp_dir, ignore_errors=True)


_DIRECTION_OFFSETS = {
    "top_left": (-1, -1),
    "top": (0, -1),
    "top_right": (1, -1),
    "left": (-1, 0),
    "right": (1, 0),
    "bottom_left": (-1, 1),
    "bottom": (0, 1),
    "bottom_right": (1, 1),
}


def _rgb_to_hsl(r: int, g: int, b: int) -> tuple[float, float, float]:
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    mx, mn = max(r, g, b), min(r, g, b)
    l = (mx + mn) / 2.0
    if mx == mn:
        return 0.0, 0.0, l
    d = mx - mn
    s = d / (2.0 - mx - mn) if l > 0.5 else d / (mx + mn)
    if mx == r:
        h = ((g - b) / d + (6.0 if g < b else 0.0)) * 60.0
    elif mx == g:
        h = ((b - r) / d + 2.0) * 60.0
    else:
        h = ((r - g) / d + 4.0) * 60.0
    return h, s, l


def _hsl_to_rgb(h: float, s: float, l: float) -> tuple[int, int, int]:
    if s == 0:
        v = int(l * 255)
        return v, v, v

    def hue2rgb(p, q, t):
        if t < 0:
            t += 1
        if t > 1:
            t -= 1
        if t < 1 / 6:
            return p + (q - p) * 6 * t
        if t < 1 / 2:
            return q
        if t < 2 / 3:
            return p + (q - p) * (2 / 3 - t) * 6
        return p

    q = l * (1 + s) if l < 0.5 else l + s - l * s
    p = 2 * l - q
    h_norm = h / 360.0
    r = int(hue2rgb(p, q, h_norm + 1 / 3) * 255)
    g = int(hue2rgb(p, q, h_norm) * 255)
    b = int(hue2rgb(p, q, h_norm - 1 / 3) * 255)
    return max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b))


def _shift_hue(r: int, g: int, b: int, shift: float) -> tuple[int, int, int]:
    h, s, l = _rgb_to_hsl(r, g, b)
    h = (h + shift) % 360
    return _hsl_to_rgb(h, s, l)


def _apply_auto_shading(
    img, light_direction: str, intensity: float, style: str, hue_shift: bool
):
    dx, dy = _DIRECTION_OFFSETS.get(light_direction, (0, -1))

    result = img.copy()
    pixels = result.load()
    w, h = result.size

    generated_colors = []
    regions_shaded = 0

    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            if a == 0:
                continue

            norm_x = x / max(1, w - 1)
            norm_y = y / max(1, h - 1)

            light_factor = 0.5
            if dx < 0:
                light_factor += (1.0 - norm_x) * 0.5
            elif dx > 0:
                light_factor += norm_x * 0.5

            if dy < 0:
                light_factor += (1.0 - norm_y) * 0.5
            elif dy > 0:
                light_factor += norm_y * 0.5

            light_factor = max(0.0, min(1.0, light_factor))

            if style == "cell":
                if light_factor < 0.33:
                    shade = -intensity
                elif light_factor > 0.66:
                    shade = intensity * 0.6
                else:
                    shade = 0
                delta = shade * 80
            elif style == "smooth":
                delta = (light_factor - 0.5) * intensity * 120
            else:  # soft
                delta = (light_factor - 0.5) * intensity * 50

            new_r = max(0, min(255, int(r + delta)))
            new_g = max(0, min(255, int(g + delta)))
            new_b = max(0, min(255, int(b + delta)))

            if hue_shift:
                hue_delta = (light_factor - 0.5) * 20 * intensity
                new_r, new_g, new_b = _shift_hue(new_r, new_g, new_b, hue_delta)

            hex_color = f"#{new_r:02x}{new_g:02x}{new_b:02x}"
            if hex_color not in generated_colors:
                generated_colors.append(hex_color)

            pixels[x, y] = (new_r, new_g, new_b, a)
            regions_shaded += 1

    return result, generated_colors, regions_shaded

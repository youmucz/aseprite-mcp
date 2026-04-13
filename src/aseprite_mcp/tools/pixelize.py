from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from mcp.server.fastmcp import FastMCP

from aseprite_mcp.client import AsepriteClient
from aseprite_mcp.config import Config
from aseprite_mcp.lua.pixelize import generate_pixelize_sprite


def _median_cut_quantize(pixels: list[tuple], target_colors: int) -> list[tuple]:
    if not pixels:
        return [(0, 0, 0)] * target_colors

    def quantize(px_list: list, depth: int) -> list[tuple]:
        if len(px_list) <= 1 or depth == 0:
            if px_list:
                r = sum(p[0] for p in px_list) // len(px_list)
                g = sum(p[1] for p in px_list) // len(px_list)
                b = sum(p[2] for p in px_list) // len(px_list)
                return [(r, g, b)]
            return []

        ranges = [
            max(p[0] for p in px_list) - min(p[0] for p in px_list),
            max(p[1] for p in px_list) - min(p[1] for p in px_list),
            max(p[2] for p in px_list) - min(p[2] for p in px_list),
        ]
        channel = ranges.index(max(ranges))
        px_list.sort(key=lambda p: p[channel])
        mid = len(px_list) // 2
        return quantize(px_list[:mid], depth - 1) + quantize(px_list[mid:], depth - 1)

    depth = 0
    while (2**depth) < target_colors and depth < 8:
        depth += 1

    return quantize(pixels, depth)[:target_colors]


def _find_nearest(r: int, g: int, b: int, palette: list[tuple]) -> tuple:
    min_dist = float("inf")
    nearest = palette[0]
    for pr, pg, pb in palette:
        d = (r - pr) ** 2 + (g - pg) ** 2 + (b - pb) ** 2
        if d < min_dist:
            min_dist = d
            nearest = (pr, pg, pb)
    return nearest


def _floyd_steinberg_dither(
    img, width: int, height: int, palette: list[tuple]
) -> list[dict]:
    buf = {}
    for y in range(height):
        for x in range(width):
            p = img.getpixel((x, y))
            buf[(x, y)] = [float(p[0]), float(p[1]), float(p[2]), p[3]]

    pixel_data = []
    for y in range(height):
        for x in range(width):
            rgba = buf.get((x, y))
            if rgba is None or rgba[3] == 0:
                continue

            old_r = max(0.0, min(255.0, rgba[0]))
            old_g = max(0.0, min(255.0, rgba[1]))
            old_b = max(0.0, min(255.0, rgba[2]))

            nr, ng, nb = _find_nearest(int(old_r), int(old_g), int(old_b), palette)
            pixel_data.append({"x": x, "y": y, "color": f"#{nr:02x}{ng:02x}{nb:02x}"})

            err_r = old_r - nr
            err_g = old_g - ng
            err_b = old_b - nb

            diffusion = [
                (x + 1, y, 7 / 16),
                (x - 1, y + 1, 3 / 16),
                (x, y + 1, 5 / 16),
                (x + 1, y + 1, 1 / 16),
            ]
            for dx, dy, factor in diffusion:
                neighbor = buf.get((dx, dy))
                if neighbor is not None and neighbor[3] > 0:
                    neighbor[0] += err_r * factor
                    neighbor[1] += err_g * factor
                    neighbor[2] += err_b * factor

    return pixel_data


def _sobel_edges(img, width: int, height: int) -> list[tuple]:
    edges = []
    gray = []
    for y in range(height):
        row = []
        for x in range(width):
            p = img.getpixel((x, y))
            gray_val = (p[0] + p[1] + p[2]) // 3
            row.append(gray_val)
        gray.append(row)

    for y in range(1, height - 1):
        for x in range(1, width - 1):
            gx = (
                -gray[y - 1][x - 1]
                + gray[y - 1][x + 1]
                - 2 * gray[y][x - 1]
                + 2 * gray[y][x + 1]
                - gray[y + 1][x - 1]
                + gray[y + 1][x + 1]
            )
            gy = (
                -gray[y - 1][x - 1]
                - 2 * gray[y - 1][x]
                - gray[y - 1][x + 1]
                + gray[y + 1][x - 1]
                + 2 * gray[y + 1][x]
                + gray[y + 1][x + 1]
            )
            mag = (gx * gx + gy * gy) ** 0.5
            if mag > 30:
                edges.append((x, y))
    return edges


def register_pixelize_tools(
    mcp: FastMCP, client: AsepriteClient, config: Config
) -> None:

    @mcp.tool()
    async def pixelize_reference(
        reference_path: str,
        target_width: int,
        target_height: int,
        palette_size: int = 16,
        method: str = "hybrid",
        dither: bool = False,
        output_path: str = "",
        export_png: bool = True,
        color_mode: str = "rgb",
    ) -> str:
        """Convert a reference image to pixel art in a single step. Performs downsampling, color quantization, and optional edge detection to produce an Aseprite sprite file.

        Args:
            reference_path: Path to the reference image (.jpg, .png, .bmp)
            target_width: Target pixel art width (4-256)
            target_height: Target pixel art height (4-256)
            palette_size: Number of colors in palette (4-32, default: 16)
            method: Conversion method: quantize (fast), edge_trace (outlines), or hybrid (best quality, default)
            dither: Apply Floyd-Steinberg dithering (default: false)
            output_path: Output .aseprite file path (auto-generated if empty)
            export_png: Also export a PNG preview (default: true)
            color_mode: Color mode: rgb (default, recommended) or indexed

        Returns:
            JSON with sprite_path, export_path, palette_size, dimensions
        """
        if not Path(reference_path).exists():
            return json.dumps({"error": f"Reference image not found: {reference_path}"})
        if not 4 <= target_width <= 256 or not 4 <= target_height <= 256:
            return json.dumps({"error": "target dimensions must be 4-256"})
        if not 4 <= palette_size <= 32:
            return json.dumps({"error": "palette_size must be 4-32"})
        if method not in ("quantize", "edge_trace", "hybrid"):
            return json.dumps(
                {"error": "method must be quantize, edge_trace, or hybrid"}
            )
        if color_mode not in ("rgb", "indexed"):
            return json.dumps({"error": "color_mode must be rgb or indexed"})

        try:
            from PIL import Image
        except ImportError:
            return json.dumps(
                {
                    "error": "PIL/Pillow is required for pixelize_reference. Install with: uv sync --extra analysis"
                }
            )

        img = Image.open(reference_path).convert("RGBA")
        img = img.resize((target_width, target_height), Image.LANCZOS)

        pixels = []
        for y in range(target_height):
            for x in range(target_width):
                p = img.getpixel((x, y))
                if p[3] > 0:
                    pixels.append((p[0], p[1], p[2]))

        palette_rgb = _median_cut_quantize(pixels, palette_size)
        palette_hex = [f"#{r:02x}{g:02x}{b:02x}" for r, g, b in palette_rgb]

        if dither:
            pixel_data = _floyd_steinberg_dither(
                img, target_width, target_height, palette_rgb
            )
        else:
            pixel_data = []
            for y in range(target_height):
                for x in range(target_width):
                    p = img.getpixel((x, y))
                    if p[3] == 0:
                        continue
                    nr, ng, nb = _find_nearest(p[0], p[1], p[2], palette_rgb)
                    nearest_hex = f"#{nr:02x}{ng:02x}{nb:02x}"
                    pixel_data.append({"x": x, "y": y, "color": nearest_hex})

        edge_pixels = None
        if method in ("edge_trace", "hybrid"):
            edge_coords = _sobel_edges(img, target_width, target_height)
            if edge_coords:
                darkest = min(palette_rgb, key=lambda c: c[0] + c[1] + c[2])
                edge_color = f"#{darkest[0]:02x}{darkest[1]:02x}{darkest[2]:02x}"
                edge_pixels = [
                    {"x": x, "y": y, "color": edge_color} for x, y in edge_coords
                ]

        if not output_path:
            output_path = os.path.join(
                config.temp_dir,
                f"pixelized-{Path(reference_path).stem}-{target_width}x{target_height}.aseprite",
            )

        export_path = ""
        if export_png:
            export_path = output_path.rsplit(".", 1)[0] + ".png"

        lua_script = generate_pixelize_sprite(
            width=target_width,
            height=target_height,
            palette_colors=palette_hex,
            pixel_data=pixel_data,
            edge_pixels=edge_pixels if method in ("edge_trace", "hybrid") else None,
            output_path=output_path,
            export_path=export_path,
            color_mode=color_mode,
        )

        try:
            result = await client.execute_lua(lua_script, "")
        except Exception as e:
            return json.dumps({"error": f"Pixelization failed: {str(e)}"})

        return json.dumps(
            {
                "success": True,
                "sprite_path": output_path,
                "export_path": export_path,
                "palette_size": len(palette_hex),
                "width": target_width,
                "height": target_height,
                "method": method,
            }
        )

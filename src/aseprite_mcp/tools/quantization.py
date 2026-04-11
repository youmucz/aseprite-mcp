from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from mcp.server.fastmcp import FastMCP

from aseprite_mcp.client import AsepriteClient
from aseprite_mcp.config import Config
from aseprite_mcp.lua.quantization import (
    generate_apply_quantized_palette,
    generate_replace_with_image,
)


def register_quantization_tools(
    mcp: FastMCP, client: AsepriteClient, config: Config
) -> None:

    @mcp.tool()
    async def quantize_palette(
        sprite_path: str,
        target_colors: int,
        algorithm: str = "median_cut",
        dither: bool = False,
        preserve_transparency: bool = True,
        convert_to_indexed: bool = True,
    ) -> str:
        f"""Automatically reduce sprite colors using industry-standard quantization algorithms. Supports three algorithms: median_cut (fast, balanced quality), kmeans (highest quality, slower), octree (very fast, good for photos). Can apply Floyd-Steinberg dithering for smoother gradients. Optionally converts to indexed color mode for true palette constraint or keeps RGB mode for flexible multi-pass workflows.

        Args:
            sprite_path: Path to source .aseprite file
            target_colors: Target palette size (2-256)
            algorithm: Quantization algorithm: median_cut (default), kmeans, or octree
            dither: Apply Floyd-Steinberg dithering during quantization (default: false)
            preserve_transparency: Keep transparent pixels transparent (default: true)
            convert_to_indexed: Convert sprite to indexed color mode (default: true)

        Returns:
            JSON with success, original_colors, quantized_colors, color_mode, palette, and algorithm_used
        """
        if target_colors < 2 or target_colors > 256:
            return json.dumps({"error": "target_colors must be between 2 and 256"})

        valid_algorithms = {"median_cut", "kmeans", "octree"}
        if algorithm not in valid_algorithms:
            return json.dumps(
                {
                    "error": f"invalid algorithm: {algorithm} (must be median_cut, kmeans, or octree)"
                }
            )

        if not Path(sprite_path).exists():
            return json.dumps({"error": f"sprite file not found: {sprite_path}"})

        temp_dir = tempfile.mkdtemp(prefix="pixel-mcp-quantize-")
        try:
            temp_png = os.path.join(temp_dir, "sprite.png")

            try:
                from PIL import Image
            except ImportError:
                return json.dumps({"error": "PIL/Pillow is required for quantization"})

            from aseprite_mcp.lua.export import generate_export_sprite

            export_script = generate_export_sprite(temp_png, 0)
            await client.execute_lua(export_script, sprite_path)

            img = Image.open(temp_png)

            original_colors = len(img.getcolors(maxcolors=256 * 256) or [])

            palette = []
            if algorithm == "median_cut":
                palette = median_cut_quantize(img, target_colors, preserve_transparency)
            elif algorithm == "kmeans":
                palette = kmeans_quantize(img, target_colors, preserve_transparency)
            elif algorithm == "octree":
                palette = octree_quantize(img, target_colors, preserve_transparency)

            if dither:
                dithered_img = _remap_with_dithering(
                    img, palette, preserve_transparency
                )
                dithered_png = os.path.join(temp_dir, "dithered.png")
                dithered_img.save(dithered_png)
                replace_script = generate_replace_with_image(dithered_png)
                await client.execute_lua(replace_script, sprite_path)

            apply_script = generate_apply_quantized_palette(
                palette, original_colors, algorithm, convert_to_indexed, dither
            )
            result = await client.execute_lua(apply_script, sprite_path)

            try:
                data = json.loads(result)
            except json.JSONDecodeError:
                return json.dumps({"error": "Failed to parse quantization result"})

            return json.dumps(data)
        finally:
            import shutil

            shutil.rmtree(temp_dir, ignore_errors=True)


def median_cut_quantize(img, target_colors, preserve_transparency):
    try:
        from PIL import Image
    except ImportError:
        return []

    pixels = []
    for x in range(img.width):
        for y in range(img.height):
            pixel = img.getpixel((x, y))
            if len(pixel) == 4 and pixel[3] > 0:
                pixels.append(pixel[:3])
            elif len(pixel) == 3:
                pixels.append(pixel)

    if not pixels:
        return []

    def quantize(pixel_list, depth):
        if len(pixel_list) <= 1 or depth == 0:
            if pixel_list:
                r = sum(p[0] for p in pixel_list) // len(pixel_list)
                g = sum(p[1] for p in pixel_list) // len(pixel_list)
                b = sum(p[2] for p in pixel_list) // len(pixel_list)
                return [f"#{r:02x}{g:02x}{b:02x}"]
            return []

        r_range = max(p[0] for p in pixel_list) - min(p[0] for p in pixel_list)
        g_range = max(p[1] for p in pixel_list) - min(p[1] for p in pixel_list)
        b_range = max(p[2] for p in pixel_list) - min(p[2] for p in pixel_list)

        channel_with_greatest_range = 0
        if g_range >= r_range and g_range >= b_range:
            channel_with_greatest_range = 1
        elif b_range >= r_range and b_range >= g_range:
            channel_with_greatest_range = 2

        pixel_list.sort(key=lambda p: p[channel_with_greatest_range])

        median_index = len(pixel_list) // 2
        return quantize(pixel_list[:median_index], depth - 1) + quantize(
            pixel_list[median_index:], depth - 1
        )

    depth = 0
    while (2**depth) < target_colors and depth < 8:
        depth += 1

    return quantize(pixels, depth)[:target_colors]


def kmeans_quantize(img, target_colors, preserve_transparency, max_iterations=20):
    try:
        from PIL import Image
    except ImportError:
        return []

    pixels = []
    for x in range(img.width):
        for y in range(img.height):
            pixel = img.getpixel((x, y))
            if len(pixel) == 4 and pixel[3] > 0:
                pixels.append(pixel[:3])
            elif len(pixel) == 3:
                pixels.append(pixel)

    if not pixels:
        return []

    import random

    centroids = random.sample(pixels, min(target_colors, len(pixels)))

    for _ in range(max_iterations):
        clusters = [[] for _ in range(len(centroids))]

        for pixel in pixels:
            distances = []
            for centroid in centroids:
                dist = sum((p - c) ** 2 for p, c in zip(pixel, centroid))
                distances.append(dist)
            closest_centroid = distances.index(min(distances))
            clusters[closest_centroid].append(pixel)

        new_centroids = []
        for cluster in clusters:
            if cluster:
                new_centroid = [
                    sum(p[0] for p in cluster) // len(cluster),
                    sum(p[1] for p in cluster) // len(cluster),
                    sum(p[2] for p in cluster) // len(cluster),
                ]
                new_centroids.append(new_centroid)
            else:
                new_centroids.append(random.choice(pixels))

        if new_centroids == centroids:
            break
        centroids = new_centroids

    palette = []
    for centroid in centroids:
        r, g, b = [max(0, min(255, int(c))) for c in centroid]
        palette.append(f"#{r:02x}{g:02x}{b:02x}")

    return palette


def octree_quantize(img, target_colors, preserve_transparency):
    try:
        from PIL import Image
    except ImportError:
        return []

    pixels = []
    for x in range(img.width):
        for y in range(img.height):
            pixel = img.getpixel((x, y))
            if len(pixel) == 4 and pixel[3] > 0:
                pixels.append(pixel[:3])
            elif len(pixel) == 3:
                pixels.append(pixel)

    if not pixels:
        return []

    class OctreeNode:
        def __init__(self, level, parent):
            self.level = level
            self.parent = parent
            self.children = [None] * 8
            self.pixel_count = 0
            self.red_sum = 0
            self.green_sum = 0
            self.blue_sum = 0

        def is_leaf(self):
            return all(child is None for child in self.children)

        def get_color(self):
            if self.pixel_count == 0:
                return "#000000"
            r = self.red_sum // self.pixel_count
            g = self.green_sum // self.pixel_count
            b = self.blue_sum // self.pixel_count
            return f"#{r:02x}{g:02x}{b:02x}"

    class OctreeQuantizer:
        def __init__(self, max_colors):
            self.max_colors = max_colors
            self.root = OctreeNode(0, None)
            self.leaves = []

        def add_color(self, r, g, b):
            node = self.root
            node.pixel_count += 1
            node.red_sum += r
            node.green_sum += g
            node.blue_sum += b

            for level in range(7, -1, -1):
                index = self.get_color_index(r, g, b, level)
                if node.children[index] is None:
                    node.children[index] = OctreeNode(7 - level, node)
                node = node.children[index]
                node.pixel_count += 1
                node.red_sum += r
                node.green_sum += g
                node.blue_sum += b

                if node.is_leaf():
                    self.leaves.append(node)
                    break

        def get_color_index(self, r, g, b, level):
            shift = 7 - level
            index = 0
            index |= ((r >> shift) & 1) << 2
            index |= ((g >> shift) & 1) << 1
            index |= (b >> shift) & 1
            return index

        def reduce(self):
            while len(self.leaves) > self.max_colors:
                min_leaf = min(self.leaves, key=lambda leaf: leaf.pixel_count)
                self.leaves.remove(min_leaf)

                parent = min_leaf.parent
                for i in range(8):
                    if parent.children[i] == min_leaf:
                        parent.children[i] = None
                        break

                if parent.is_leaf():
                    self.leaves.append(parent)

        def get_palette(self):
            return [leaf.get_color() for leaf in self.leaves]

    quantizer = OctreeQuantizer(target_colors)
    for pixel in pixels:
        quantizer.add_color(pixel[0], pixel[1], pixel[2])

    quantizer.reduce()
    return quantizer.get_palette()


def _parse_palette_colors(palette: list[str]) -> list[tuple[int, int, int]]:
    colors = []
    for hex_color in palette:
        h = hex_color.lstrip("#")
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        colors.append((r, g, b))
    return colors


def _find_nearest_palette_color(
    r: int, g: int, b: int, palette_rgb: list[tuple[int, int, int]]
) -> tuple[int, int, int]:
    min_dist = float("inf")
    nearest = palette_rgb[0]
    for pr, pg, pb in palette_rgb:
        dist = (r - pr) ** 2 + (g - pg) ** 2 + (b - pb) ** 2
        if dist < min_dist:
            min_dist = dist
            nearest = (pr, pg, pb)
    return nearest


def _remap_with_dithering(img, palette: list[str], preserve_transparency: bool):
    from PIL import Image

    palette_rgb = _parse_palette_colors(palette)
    result = img.copy().convert("RGBA")
    pixels = result.load()
    w, h = result.size

    errors = [[(0, 0, 0)] * w for _ in range(h)]

    for y in range(h):
        for x in range(w):
            pixel = pixels[x, y]
            if len(pixel) == 4 and pixel[3] == 0 and preserve_transparency:
                continue

            old_r = min(255, max(0, pixel[0] + errors[y][x][0]))
            old_g = min(255, max(0, pixel[1] + errors[y][x][1]))
            old_b = min(255, max(0, pixel[2] + errors[y][x][2]))

            new_r, new_g, new_b = _find_nearest_palette_color(
                old_r, old_g, old_b, palette_rgb
            )

            pixels[x, y] = (new_r, new_g, new_b, pixel[3] if len(pixel) == 4 else 255)

            err_r = old_r - new_r
            err_g = old_g - new_g
            err_b = old_b - new_b

            for dx, dy, factor in [
                (1, 0, 7.0 / 16),
                (-1, 1, 3.0 / 16),
                (0, 1, 5.0 / 16),
                (1, 1, 1.0 / 16),
            ]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h:
                    er, eg, eb = errors[ny][nx]
                    errors[ny][nx] = (
                        er + err_r * factor,
                        eg + err_g * factor,
                        eb + err_b * factor,
                    )

    return result

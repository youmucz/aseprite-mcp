from __future__ import annotations

from aseprite_mcp.lua.core import escape_string, generate_palette_snapper_helper
from aseprite_mcp.lua.canvas import (
    generate_create_sprite,
    generate_add_layer,
    generate_add_frame,
)
from aseprite_mcp.lua.drawing import (
    generate_draw_contour,
    generate_draw_line,
    generate_draw_rectangle,
    generate_draw_circle,
    generate_fill_area,
)
from aseprite_mcp.lua.palette import generate_set_palette
from aseprite_mcp.lua.export import generate_export_sprite, generate_save_as


_VALID_TYPES = {
    "create_canvas",
    "set_palette",
    "add_layer",
    "add_frame",
    "draw_pixels",
    "draw_contour",
    "draw_line",
    "draw_rectangle",
    "draw_circle",
    "fill_area",
    "save_as",
    "export_sprite",
}

_DRAW_TYPES = {
    "draw_pixels",
    "draw_contour",
    "draw_line",
    "draw_rectangle",
    "draw_circle",
    "fill_area",
}
_POST_CREATE_TYPES = _DRAW_TYPES | {"save_as", "export_sprite"}
_REQUIRES_SPRITE = _POST_CREATE_TYPES | {"set_palette", "add_layer", "add_frame"}


def _color_to_lua(hex_str: str) -> str:
    h = hex_str.lstrip("#")
    if len(h) == 6:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return f"app.pixelColor.rgba({r}, {g}, {b}, 255)"
    elif len(h) == 8:
        r, g, b, a = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), int(h[6:8], 16)
        return f"app.pixelColor.rgba({r}, {g}, {b}, {a})"
    raise ValueError(f"Invalid hex color: {hex_str}")


def _color_obj_to_lua(hex_str: str) -> str:
    h = hex_str.lstrip("#")
    if len(h) == 6:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return f"Color({r}, {g}, {b}, 255)"
    elif len(h) == 8:
        r, g, b, a = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), int(h[6:8], 16)
        return f"Color({r}, {g}, {b}, {a})"
    raise ValueError(f"Invalid hex color: {hex_str}")


def _generate_create_op(params: dict, temp_dir: str = "/tmp") -> tuple[str, str]:
    width = params["width"]
    height = params["height"]
    color_mode_str = params.get("color_mode", "rgb")
    filename = params.get("filename", "")
    if not filename:
        import os
        import time

        filename = os.path.join(temp_dir, f"sprite-{int(time.time() * 1000)}.aseprite")
    color_mode_map = {
        "rgb": "ColorMode.RGB",
        "grayscale": "ColorMode.GRAYSCALE",
        "indexed": "ColorMode.INDEXED",
    }
    cm_lua = color_mode_map.get(color_mode_str, "ColorMode.RGB")
    transparent = "spr.transparentColor = 255\n" if color_mode_str == "indexed" else ""
    escaped = escape_string(filename)
    lua = f"""local spr = Sprite({width}, {height}, {cm_lua})
{transparent}spr:saveAs("{escaped}")
print("{escaped}")"""
    return filename, lua


def _generate_draw_pixels_batch(params: dict) -> str:
    layer_name = escape_string(params["layer_name"])
    frame_number = params["frame_number"]
    pixels = params["pixels"]
    use_palette = params.get("use_palette", False)

    helper = ""
    if use_palette:
        helper = generate_palette_snapper_helper() + "\n"

    put_lines = []
    for p in pixels:
        if use_palette:
            h = p["color"].lstrip("#")
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            a = int(h[6:8], 16) if len(h) == 8 else 255
            put_lines.append(
                f"\timg:putPixel({p['x']}, {p['y']}, snapToPaletteForPixel({r}, {g}, {b}, {a}))"
            )
        else:
            color_lua = _color_to_lua(p["color"])
            put_lines.append(f"\timg:putPixel({p['x']}, {p['y']}, {color_lua})")
    put_code = "\n".join(put_lines)

    return f"""{helper}local spr = app.activeSprite
if not spr then error("No active sprite") end
local layer = nil
for i, lyr in ipairs(spr.layers) do
\tif lyr.name == "{layer_name}" then layer = lyr; break end
end
if not layer then error("Layer not found: {layer_name}") end
local frame = spr.frames[{frame_number}]
if not frame then error("Frame not found: {frame_number}") end

app.transaction(function()
\tlocal cel = layer:cel(frame)
\tif not cel then cel = spr:newCel(layer, frame) end
\tlocal img = cel.image
{put_code}
end)

spr:saveAs(spr.filename)
print("Pixels drawn successfully")"""


def _generate_op_lua(op_type: str, params: dict) -> str:
    if op_type == "set_palette":
        return generate_set_palette(params["colors"])
    elif op_type == "add_layer":
        return generate_add_layer(params["layer_name"])
    elif op_type == "add_frame":
        return generate_add_frame(params.get("duration_ms", 100))
    elif op_type == "draw_pixels":
        return _generate_draw_pixels_batch(params)
    elif op_type == "draw_contour":
        from aseprite_mcp.tools.common import Color, Point

        points = [Point(x=p["x"], y=p["y"]) for p in params["points"]]
        return generate_draw_contour(
            params["layer_name"],
            params["frame_number"],
            points,
            Color.from_hex(params["color"]),
            params.get("thickness", 1),
            params.get("closed", False),
            params.get("use_palette", False),
        )
    elif op_type == "draw_line":
        from aseprite_mcp.tools.common import Color

        return generate_draw_line(
            params["layer_name"],
            params["frame_number"],
            params["x1"],
            params["y1"],
            params["x2"],
            params["y2"],
            Color.from_hex(params["color"]),
            params.get("thickness", 1),
            params.get("use_palette", False),
        )
    elif op_type == "draw_rectangle":
        from aseprite_mcp.tools.common import Color

        return generate_draw_rectangle(
            params["layer_name"],
            params["frame_number"],
            params["x"],
            params["y"],
            params["width"],
            params["height"],
            Color.from_hex(params["color"]),
            params.get("filled", False),
            params.get("use_palette", False),
        )
    elif op_type == "draw_circle":
        from aseprite_mcp.tools.common import Color

        return generate_draw_circle(
            params["layer_name"],
            params["frame_number"],
            params["center_x"],
            params["center_y"],
            params["radius"],
            Color.from_hex(params["color"]),
            params.get("filled", False),
            params.get("use_palette", False),
        )
    elif op_type == "fill_area":
        from aseprite_mcp.tools.common import Color

        return generate_fill_area(
            params["layer_name"],
            params["frame_number"],
            params["x"],
            params["y"],
            Color.from_hex(params["color"]),
            params.get("tolerance", 0),
            params.get("use_palette", False),
        )
    elif op_type == "save_as":
        return generate_save_as(params["output_path"])
    elif op_type == "export_sprite":
        return generate_export_sprite(
            params["output_path"], params.get("frame_number", 0)
        )
    else:
        raise ValueError(f"Unknown operation type: {op_type}")


def validate_operations(
    operations: list[dict], has_existing_sprite: bool = False
) -> list[str]:
    errors = []
    has_create = False

    for i, op in enumerate(operations):
        op_type = op.get("type", "")
        if op_type not in _VALID_TYPES:
            errors.append(f"Operation {i}: unknown type '{op_type}'")
            continue

        if op_type == "create_canvas":
            if has_create:
                errors.append(f"Operation {i}: create_canvas can only appear once")
            if i != 0:
                errors.append(
                    f"Operation {i}: create_canvas must be the first operation"
                )
            has_create = True
        elif op_type in _REQUIRES_SPRITE and i == 0 and not has_existing_sprite:
            errors.append(f"Operation {i}: {op_type} requires create_canvas first")
    return errors


def generate_batch_operations(
    operations: list[dict], temp_dir: str = "/tmp", has_existing_sprite: bool = False
) -> tuple[str, str]:
    errors = validate_operations(operations, has_existing_sprite=has_existing_sprite)
    if errors:
        raise ValueError("Invalid operations: " + "; ".join(errors))

    sprite_path = ""
    lua_parts: list[str] = []

    for op in operations:
        op_type = op["type"]
        params = op.get("params", {})

        if op_type == "create_canvas":
            sprite_path, lua = _generate_create_op(params, temp_dir=temp_dir)
            lua_parts.append(lua)
        else:
            lua = _generate_op_lua(op_type, params)
            lua_parts.append(lua)

    combined = "\n\n".join(lua_parts)
    return sprite_path, combined

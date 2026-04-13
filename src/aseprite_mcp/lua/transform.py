from __future__ import annotations

from aseprite_mcp.lua.core import escape_string, format_color
from aseprite_mcp.tools.common import Color


def generate_flip_sprite(direction: str, target: str) -> str:
    flip_map = {
        "horizontal": "FlipType.HORIZONTAL",
        "vertical": "FlipType.VERTICAL",
    }
    flip_type = flip_map.get(direction, "FlipType.HORIZONTAL")

    target_map = {
        "sprite": "all",
        "layer": "activeLayer",
        "cel": "activeCel",
    }
    target_arg = target_map.get(target, "all")

    return f'''local spr = app.activeSprite
if not spr then
    error("No active sprite")
end

app.transaction(function()
    app.command(Flip {{
        ui = false,
        flip = {flip_type},
        target = "{target_arg}"
    }})
end)

spr:saveAs(spr.filename)
print("Flip completed successfully")'''


def generate_rotate_sprite(angle: int, target: str) -> str:
    angle_map = {
        90: "Rotate90CW",
        180: "Rotate180",
        270: "Rotate90CCW",
    }
    rotate_type = angle_map.get(angle, "Rotate90CW")

    target_map = {
        "sprite": "all",
        "layer": "activeLayer",
        "cel": "activeCel",
    }
    target_arg = target_map.get(target, "all")

    return f'''local spr = app.activeSprite
if not spr then
    error("No active sprite")
end

app.transaction(function()
    if {angle} == 90 then
        app.command(Rotate90CW {{ui = false, target = "{target_arg}"}})
    elseif {angle} == 180 then
        app.command(Rotate180 {{ui = false, target = "{target_arg}"}})
    elseif {angle} == 270 then
        app.command(Rotate90CCW {{ui = false, target = "{target_arg}"}})
    end
end)

spr:saveAs(spr.filename)
print("Rotate completed successfully")'''


def generate_scale_sprite(scale_x: float, scale_y: float, algorithm: str) -> str:
    algo_map = {
        "nearest": "",
        "bilinear": "algorithm = BILINEAR",
        "rotsprite": "algorithm = Rotosprite",
    }
    algo_str = algo_map.get(algorithm, "")

    return f"""local spr = app.activeSprite
if not spr then
    error("No active sprite")
end

local newWidth = math.floor(spr.width * {scale_x})
local newHeight = math.floor(spr.height * {scale_y})

app.transaction(function()
    app.command(SpriteSize {{
        ui = false,
        width = newWidth,
        height = newHeight{("," if algo_str else "")}
        {algo_str}
    }})
end)

local result = {{
    success = true,
    new_width = newWidth,
    new_height = newHeight
}}

print('{{"success":true,"new_width":' .. newWidth .. ',"new_height":' .. newHeight .. '}}')
spr:saveAs(spr.filename)"""


def generate_crop_sprite(x: int, y: int, width: int, height: int) -> str:
    return f"""local spr = app.activeSprite
if not spr then
    error("No active sprite")
end

app.transaction(function()
    app.command(Crop {{
        ui = false,
        x = {x},
        y = {y},
        width = {width},
        height = {height}
    }})
end)

spr:saveAs(spr.filename)
print("Crop completed successfully")"""


def generate_resize_canvas(width: int, height: int, anchor: str) -> str:
    anchor_map = {
        "center": "Anchor.CENTER",
        "top_left": "Anchor.TOP_LEFT",
        "top_right": "Anchor.TOP_RIGHT",
        "bottom_left": "Anchor.BOTTOM_LEFT",
        "bottom_right": "Anchor.BOTTOM_RIGHT",
    }
    anchor_str = anchor_map.get(anchor, "Anchor.CENTER")

    return f"""local spr = app.activeSprite
if not spr then
    error("No active sprite")
end

app.transaction(function()
    app.command(CanvasSize {{
        ui = false,
        width = {width},
        height = {height},
        anchor = {anchor_str}
    }})
end)

spr:saveAs(spr.filename)
print("Canvas resized successfully")"""


def generate_apply_outline(
    layer_name: str, frame_number: int, color: Color, thickness: int
) -> str:
    escaped_name = escape_string(layer_name)
    color_str = format_color(color)

    return f'''local spr = app.activeSprite
if not spr then
    error("No active sprite")
end

-- Find layer by name
local layer = nil
for i, lyr in ipairs(spr.layers) do
    if lyr.name == "{escaped_name}" then
        layer = lyr
        break
    end
end

if not layer then
    error("Layer not found: {escaped_name}")
end

local frame = spr.frames[{frame_number}]
if not frame then
    error("Frame not found: {frame_number}")
end

app.transaction(function()
    app.activeLayer = layer
    app.activeFrame = frame
    
    app.useTool{{
        tool = "pencil",
        color = {color_str},
        brush = Brush({{size = {thickness}}}),
        points = {{spr.bounds}}
    }}
end)

spr:saveAs(spr.filename)
print("Outline applied successfully")'''


def generate_downsample_image(
    source_path: str, output_path: str, target_width: int, target_height: int
) -> str:
    escaped_source = escape_string(source_path)
    escaped_output = escape_string(output_path)

    return f'''local spr = app.open("{escaped_source}")
if not spr then
    error("Failed to load source image")
end

local scaleX = {target_width} / spr.width
local scaleY = {target_height} / spr.height

app.transaction(function()
    app.command.SpriteSize {{
        ui = false,
        width = {target_width},
        height = {target_height},
        algorithm = "BILINEAR"
    }}
end)

spr:saveAs("{escaped_output}")
print("{escaped_output}")'''

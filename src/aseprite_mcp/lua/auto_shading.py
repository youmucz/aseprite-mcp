from __future__ import annotations

import json as _json

from aseprite_mcp.lua.core import escape_json_for_lua_print, escape_string


def generate_apply_auto_shading_result(
    shaded_image_path: str,
    layer_name: str,
    frame_number: int,
    generated_colors: list[str],
    regions_shaded_count: int,
) -> str:
    escaped_name = escape_string(layer_name)
    escaped_path = escape_string(shaded_image_path)

    color_list = []
    for c in generated_colors:
        c = c.lstrip("#")
        r = int(c[0:2], 16)
        g = int(c[2:4], 16)
        b = int(c[4:6], 16)
        color_list.append(f"Color({r}, {g}, {b}, 255)")

    colors_str = ", ".join(color_list)

    pal_len = len(generated_colors)
    palette_json = escape_json_for_lua_print(_json.dumps(generated_colors))

    result_json = _json.dumps(
        {
            "success": True,
            "colors_added": pal_len,
            "palette": generated_colors,
            "regions_shaded": regions_shaded_count,
        }
    )
    escaped_result = escape_json_for_lua_print(result_json)

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

-- Load shaded image and apply to layer
local shadedImage = Image("{escaped_path}")
if not shadedImage then
    error("Failed to load shaded image")
end

local cel = layer:cel(frame)
if not cel then
    cel = spr:newCel(layer, frame)
end

cel.image = shadedImage

-- Add generated colors to palette
local palette = spr.palettes[1]
local palCount = #palette
local newColors = {{{colors_str}}}
for i, color in ipairs(newColors) do
    if palCount < 256 then
        palette:resize(palCount + 1)
        palette:setColor(palCount, color)
        palCount = palCount + 1
    end
end

print('{escaped_result}')
spr:saveAs(spr.filename)'''

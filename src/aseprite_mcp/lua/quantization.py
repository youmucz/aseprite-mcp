from __future__ import annotations

import json as _json

from aseprite_mcp.lua.core import escape_string


def generate_apply_quantized_palette(
    palette: list[str],
    original_colors: int,
    algorithm: str,
    convert_to_indexed: bool,
    dither: bool,
) -> str:
    color_list = []
    for c in palette:
        c = c.lstrip("#")
        r = int(c[0:2], 16)
        g = int(c[2:4], 16)
        b = int(c[4:6], 16)
        color_list.append(f"Color({r}, {g}, {b}, 255)")

    colors_str = ", ".join(color_list)
    color_mode_str = "indexed" if convert_to_indexed else "rgb"
    palette_json = _json.dumps(palette)

    convert_block = ""
    if convert_to_indexed:
        convert_block = """
app.transaction(function()
    app.command(ChangePixelFormat {
        ui = false,
        format = "INDEXED"
    })
end)
"""

    return f'''local spr = app.activeSprite
if not spr then
    error("No active sprite")
end

local newPalette = spr.palettes[1]
newPalette:resize({len(palette)})

local newColors = {{{colors_str}}}

for i = 0, {len(palette)} - 1 do
    newPalette:setColor(i, newColors[i + 1])
end
{convert_block}
print('{{"success":true,"original_colors":{original_colors},"quantized_colors":{len(palette)},"color_mode":"{color_mode_str}","palette":{palette_json},"algorithm_used":"{algorithm}"}}')
spr:saveAs(spr.filename)'''


def generate_replace_with_image(image_path: str) -> str:
    escaped_path = escape_string(image_path)

    return f'''local spr = app.activeSprite
if not spr then
    error("No active sprite")
end

local newImage = Image("{escaped_path}")
if not newImage then
    error("Failed to load image")
end

local cel = app.activeLayer:cel(app.activeFrame)
if cel then
    cel.image = newImage
end

spr:saveAs(spr.filename)
print("Image replaced successfully")'''

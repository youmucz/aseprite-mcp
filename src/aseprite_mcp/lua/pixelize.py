from __future__ import annotations

from aseprite_mcp.lua.core import escape_string, escape_json_for_lua_print


def generate_pixelize_sprite(
    width: int,
    height: int,
    palette_colors: list[str],
    pixel_data: list[dict],
    edge_pixels: list[dict] | None,
    output_path: str,
    export_path: str | None,
    color_mode: str,
) -> str:
    escaped_output = escape_string(output_path)
    escaped_export = escape_string(export_path) if export_path else ""
    json_output = escape_json_for_lua_print(output_path)

    cm_lua = "ColorMode.INDEXED" if color_mode == "indexed" else "ColorMode.RGB"

    palette_lua = "{\n"
    for i, hex_color in enumerate(palette_colors):
        h = hex_color.lstrip("#")
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        a = int(h[6:8], 16) if len(h) == 8 else 255
        palette_lua += f"\t\tColor({r}, {g}, {b}, {a})"
        if i < len(palette_colors) - 1:
            palette_lua += ","
        palette_lua += "\n"
    palette_lua += "\t}"

    put_pixel_code = ""
    for px in pixel_data:
        x, y = px["x"], px["y"]
        h = px["color"].lstrip("#")
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        a = int(h[6:8], 16) if len(h) == 8 else 255
        put_pixel_code += (
            f"\timg:putPixel({x}, {y}, app.pixelColor.rgba({r}, {g}, {b}, {a}))\n"
        )

    edge_layer_code = ""
    if edge_pixels:
        edge_put = ""
        for px in edge_pixels:
            x, y = px["x"], px["y"]
            h = px["color"].lstrip("#")
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            edge_put += f"\t\tedgeImg:putPixel({x}, {y}, app.pixelColor.rgba({r}, {g}, {b}, 255))\n"
        edge_layer_code = f"""
local edgeLayer = spr:newLayer()
edgeLayer.name = "edge"
local edgeCel = spr:newCel(edgeLayer, frame)
local edgeImg = Image({width}, {height}, {cm_lua})
app.transaction(function()
{edge_put}
end)
edgeCel.image = edgeImg
"""

    export_code = ""
    if export_path:
        export_code += f'\nspr:saveCopyAs("{escaped_export}")'

    transparent_color = (
        "spr.transparentColor = 255\n" if color_mode == "indexed" else ""
    )

    if color_mode == "indexed":
        index_map_code = ""
        for i, hex_color in enumerate(palette_colors):
            h = hex_color.lstrip("#")
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            index_map_code += f'\tidxMap["{r},{g},{b}"] = {i}\n'

        index_put_code = ""
        for px in pixel_data:
            x, y = px["x"], px["y"]
            h = px["color"].lstrip("#")
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            index_put_code += f'\tlocal idx = colorToIdx["{r},{g},{b}"] or 0\n'
            index_put_code += f"\timg:putPixel({x}, {y}, idx)\n"

        edge_index_put = ""
        if edge_pixels:
            for px in edge_pixels:
                x, y = px["x"], px["y"]
                h = px["color"].lstrip("#")
                r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
                edge_index_put += f'\tlocal eidx = colorToIdx["{r},{g},{b}"] or 0\n'
                edge_index_put += f"\tedgeImg:putPixel({x}, {y}, eidx)\n"

        edge_layer_indexed = ""
        if edge_pixels:
            edge_layer_indexed = f"""
local edgeLayer = spr:newLayer()
edgeLayer.name = "edge"
local edgeCel = spr:newCel(edgeLayer, frame)
local edgeImg = Image({width}, {height}, {cm_lua})
app.transaction(function()
{edge_index_put}
end)
edgeCel.image = edgeImg
"""

        return f"""local spr = Sprite({width}, {height}, {cm_lua})
{transparent_color}
local palette = spr.palettes[1]
palette:resize({len(palette_colors)})
local colors = {palette_lua}
for i, color in ipairs(colors) do
    palette:setColor(i - 1, color)
end

local colorToIdx = {{}}
{index_map_code}

local baseLayer = spr.layers[1]
baseLayer.name = "base"
local frame = spr.frames[1]
local cel = baseLayer:cel(frame)
if not cel then
    cel = spr:newCel(baseLayer, frame)
end
local img = cel.image

app.transaction(function()
{index_put_code}
end)

{edge_layer_indexed}

spr:saveAs("{escaped_output}")
{export_code}
print("{{\\"success\\":true,\\"sprite_path\\":\\"{json_output}\\",\\"palette_size\\":{len(palette_colors)},\\"width\\":{width},\\"height\\":{height}}}")"""

    return f"""local spr = Sprite({width}, {height}, {cm_lua})
local palette = spr.palettes[1]
palette:resize({len(palette_colors)})
local colors = {palette_lua}
for i, color in ipairs(colors) do
    palette:setColor(i - 1, color)
end

local baseLayer = spr.layers[1]
baseLayer.name = "base"
local frame = spr.frames[1]
local cel = baseLayer:cel(frame)
if not cel then
    cel = spr:newCel(baseLayer, frame)
end
local img = cel.image

app.transaction(function()
{put_pixel_code}
end)

{edge_layer_code}

spr:saveAs("{escaped_output}")
{export_code}
print("{{\\"success\\":true,\\"sprite_path\\":\\"{json_output}\\",\\"palette_size\\":{len(palette_colors)},\\"width\\":{width},\\"height\\":{height}}}")"""

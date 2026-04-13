from __future__ import annotations

from aseprite_mcp.lua.core import escape_string, escape_json_for_lua_print

_MCP_MARKER = "__MCP__:"


def generate_export_sprite(output_path: str, frame_number: int) -> str:
    escaped_path = escape_string(output_path)

    if frame_number == 0:
        return f'''local spr = app.activeSprite
if not spr then
    error("No active sprite")
end

spr:saveCopyAs("{escaped_path}")
print("{_MCP_MARKER}Exported successfully")'''

    return f'''local spr = app.activeSprite
if not spr then
    error("No active sprite")
end

local frame = spr.frames[{frame_number}]
if not frame then
    error("Frame not found: {frame_number}")
end

app.activeFrame = frame
spr:saveCopyAs("{escaped_path}")
print("{_MCP_MARKER}Exported successfully")'''


def generate_export_spritesheet(
    output_path: str, layout: str, padding: int, include_json: bool
) -> str:
    escaped_path = escape_string(output_path)
    json_path_for_print = escape_json_for_lua_print(output_path)

    frame_count_var = "#spr.frames"
    if layout == "horizontal":
        cols_lua = frame_count_var
        rows_lua = "1"
    elif layout == "vertical":
        cols_lua = "1"
        rows_lua = frame_count_var
    elif layout == "rows":
        cols_lua = f"math.ceil(math.sqrt({frame_count_var}))"
        rows_lua = (
            f"math.ceil({frame_count_var} / math.ceil(math.sqrt({frame_count_var})))"
        )
    elif layout == "columns":
        cols_lua = f"math.ceil(math.sqrt({frame_count_var}))"
        rows_lua = f"math.ceil({frame_count_var} / {cols_lua})"
    else:
        cols_lua = f"math.ceil(math.sqrt({frame_count_var}))"
        rows_lua = (
            f"math.ceil({frame_count_var} / math.ceil(math.sqrt({frame_count_var})))"
        )

    json_export_lua = ""
    metadata_part_lua = "null"
    if include_json:
        json_path = output_path.rsplit(".", 1)[0] + ".json"
        escaped_json = escape_string(json_path)
        metadata_json_for_print = escape_json_for_lua_print(json_path)
        metadata_part_lua = f'\\"{metadata_json_for_print}\\"'
        json_export_lua = f'''
local jsonFile = io.open("{escaped_json}", "w")
if jsonFile then
    local parts = {{}}
    local fc = 0
    for ri = 0, rows - 1 do
        for ci = 0, cols - 1 do
            local fi = ri * cols + ci
            if fi < {frame_count_var} then
                fc = fc + 1
                local fx = ci * (spr.width + {padding})
                local fy = ri * (spr.height + {padding})
                local entry = string.format(
                    '{{"frame":%d,"duration":%.3f,"x":%d,"y":%d,"width":%d,"height":%d}}',
                    fc, spr.frames[fi + 1].duration, fx, fy, spr.width, spr.height
                )
                table.insert(parts, entry)
            end
        end
    end
    jsonFile:write('{{"frames":[' .. table.concat(parts, ',') .. '],')
    jsonFile:write(string.format('"width":%d,"height":%d,"frameCount":%d}}',
        outW, outH, {frame_count_var}))
    jsonFile:close()
end'''

    return f'''local spr = app.activeSprite
if not spr then
    error("No active sprite")
end

local numFrames = {frame_count_var}
local cols = {cols_lua}
local rows = {rows_lua}
local outW = cols * spr.width + (cols - 1) * {padding}
local outH = rows * spr.height + (rows - 1) * {padding}

local outSpr = Sprite(outW, outH, spr.colorMode)
if spr.colorMode == ColorMode.INDEXED then
    for i = 0, #spr.palettes[1] - 1 do
        outSpr.palettes[1]:setColor(i, spr.palettes[1]:getColor(i))
    end
end

local outImg = Image(outW, outH, spr.colorMode)
if spr.colorMode == ColorMode.INDEXED then
    outImg:clear(0)
end

for ri = 0, rows - 1 do
    for ci = 0, cols - 1 do
        local fi = ri * cols + ci
        if fi < numFrames then
            local frame = spr.frames[fi + 1]
            for _, layer in ipairs(spr.layers) do
                if layer.isVisible and not layer.isGroup then
                    local cel = layer:cel(frame)
                    if cel and cel.image then
                        local dstX = ci * (spr.width + {padding}) + (cel.position.x or 0)
                        local dstY = ri * (spr.height + {padding}) + (cel.position.y or 0)
                        outImg:drawImage(cel.image, dstX, dstY, cel.opacity)
                    end
                end
            end
        end
    end
end

outSpr.cels[1].image = outImg
outSpr:saveCopyAs("{escaped_path}")
outSpr:close()
{json_export_lua}

print("{_MCP_MARKER}{{\\"spritesheet_path\\":\\"{json_path_for_print}\\",\\"metadata_path\\":{metadata_part_lua},\\"frame_count\\":" .. numFrames .. "}}")'''


def generate_import_image(
    image_path: str, layer_name: str, frame_number: int, x: int = None, y: int = None
) -> str:
    escaped_image = escape_string(image_path)
    escaped_name = escape_string(layer_name)

    position_args = f", Point({x}, {y})" if x is not None and y is not None else ""

    return f'''local spr = app.activeSprite
if not spr then
    error("No active sprite")
end

local layer = spr:newLayer()
layer.name = "{escaped_name}"

local image = Image("{escaped_image}")

local frame = spr.frames[{frame_number}]
if not frame then
    error("Frame not found: {frame_number}")
end

spr:newCel(layer, frame, image{position_args})

spr:saveAs(spr.filename)
print("{_MCP_MARKER}Image imported successfully")'''


def generate_save_as(output_path: str) -> str:
    escaped_path = escape_string(output_path)
    json_path = escape_json_for_lua_print(output_path)

    return f'''local spr = app.activeSprite
if not spr then
    error("No active sprite")
end

spr:saveAs("{escaped_path}")
print("{_MCP_MARKER}{{\\"success\\":true,\\"file_path\\":\\"{json_path}\\"}}")'''

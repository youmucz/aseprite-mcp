from __future__ import annotations

from aseprite_mcp.lua.core import escape_string, escape_json_for_lua_print


def generate_export_sprite(output_path: str, frame_number: int) -> str:
    escaped_path = escape_string(output_path)

    if frame_number == 0:
        return f'''local spr = app.activeSprite
if not spr then
    error("No active sprite")
end

spr:saveCopyAs("{escaped_path}")
print("Exported successfully")'''

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
print("Exported successfully")'''


def _generate_lua_json_encode(tbl_name: str, fields: list[tuple[str, str]]) -> str:
    parts = []
    for key, val_expr in fields:
        if val_expr.startswith('"STRING:') and val_expr.endswith('"'):
            val = val_expr[len('"STRING:') : -1]
            parts.append(f'\\"{key}\\":\\"' + val + '\\"')
        elif val_expr.startswith('"RAW:') and val_expr.endswith('"'):
            val = val_expr[len('"RAW:') : -1]
            parts.append(f'\\"{key}\\":' + val)
        else:
            parts.append(f'\\"{key}\\":\\" .. tostring({val_expr}) .. \\"')
    inner = ", ".join(parts)
    return f'print("{{{inner}}}")'


def generate_export_spritesheet(
    output_path: str, layout: str, padding: int, include_json: bool
) -> str:
    escaped_path = escape_string(output_path)

    layout_map = {
        "horizontal": "SpriteSheetType.HORIZONTAL",
        "vertical": "SpriteSheetType.VERTICAL",
        "rows": "SpriteSheetType.ROWS",
        "columns": "SpriteSheetType.COLUMNS",
        "packed": "SpriteSheetType.PACKED",
    }
    layout_str = layout_map.get(layout, "SpriteSheetType.HORIZONTAL")

    json_export = ""
    if include_json:
        json_path = output_path.rsplit(".", 1)[0] + ".json"
        escaped_json = escape_string(json_path)
        json_export = f'''
-- Export JSON metadata (manual JSON generation, no json library available)
local jsonFile = io.open("{escaped_json}", "w")
if jsonFile then
    local parts = {{}}
    for i, frame in ipairs(spr.frames) do
        local x = (i - 1) * (spr.width + {padding})
        local entry = string.format(
            '{{"frame":%d,"duration":%.3f,"x":%d,"y":0,"width":%d,"height":%d}}',
            i, frame.duration, x, spr.width, spr.height
        )
        table.insert(parts, entry)
    end
    jsonFile:write('{{"frames":[' .. table.concat(parts, ',') .. '],')
    jsonFile:write(string.format('"width":%d,"height":%d,"frameCount":%d}}',
        spr.width, spr.height, #spr.frames))
    jsonFile:close()
end'''

    metadata_path_lua = f'"{json_path}"' if include_json else "nil"

    return f'''local spr = app.activeSprite
if not spr then
    error("No active sprite")
end

app.command(ExportSpriteSheet {{
    ui = false,
    askFilename = true,
    filename = "{escaped_path}",
    type = {layout_str},
    columns = math.ceil(math.sqrt(#spr.frames)),
    rows = math.ceil(#spr.frames / math.ceil(math.sqrt(#spr.frames))),
    padding = {padding},
    borderPadding = {padding},
    shapePadding = {padding},
    innerPadding = {padding}
}})

{json_export}

-- Manual JSON output
local metadataPart = "null"
if {metadata_path_lua} ~= nil then
    metadataPart = '\\"' .. string.gsub({metadata_path_lua}, '\\\\"', '\\\\\\\\"') .. '\\"'
end
print('{{"spritesheet_path":"{escape_json_for_lua_print(output_path)}","metadata_path":' .. metadataPart .. ',"frame_count":' .. #spr.frames .. '}}')
spr:saveAs(spr.filename)'''


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
print("Image imported successfully")'''


def generate_save_as(output_path: str) -> str:
    escaped_path = escape_string(output_path)
    json_path = escape_json_for_lua_print(output_path)

    return f'''local spr = app.activeSprite
if not spr then
    error("No active sprite")
end

spr:saveAs("{escaped_path}")
print('{{"success":true,"file_path":"{json_path}"}}')'''

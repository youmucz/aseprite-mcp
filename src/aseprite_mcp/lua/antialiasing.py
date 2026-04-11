from __future__ import annotations

from aseprite_mcp.lua.core import (
    escape_string,
    generate_palette_snapper_helper,
    format_color_with_palette,
)
from aseprite_mcp.tools.common import Color


def generate_suggest_antialiasing(
    layer_name: str,
    frame_number: int,
    region_x: int,
    region_y: int,
    region_width: int,
    region_height: int,
    threshold: int,
    use_palette: bool,
) -> str:
    escaped_name = escape_string(layer_name)
    snap_helper = generate_palette_snapper_helper() if use_palette else ""

    return f'''{snap_helper}
local spr = app.activeSprite
if not spr then
    error("No active sprite")
end

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

local cel = layer:cel(frame)
if not cel then
    error("No cel found at frame {frame_number}")
end

local img = cel.image
local suggestions = {{}}
local threshold = {threshold}

local function getRGBA(img, x, y)
    local px = img:getPixel(x, y)
    return app.pixelColor.rgbaR(px), app.pixelColor.rgbaG(px), app.pixelColor.rgbaB(px), app.pixelColor.rgbaA(px)
end

local function makeSuggestionEntry(sx, sy, curR, curG, curB, curA, nbrR, nbrG, nbrB, nbrA, blR, blG, blB, blA)
    return string.format(
        '{{"x":%d,"y":%d,"current_color":"#%02x%02x%02x%02x","neighbor_color":"#%02x%02x%02x%02x","suggested_color":"#%02x%02x%02x%02x","direction":"diagonal_ne"}}',
        sx, sy, curR, curG, curB, curA, nbrR, nbrG, nbrB, nbrA, blR, blG, blB, blA
    )
end

for y = {region_y}, {region_y + region_height - 2} do
    for x = {region_x}, {region_x + region_width - 2} do
        local imgX = x - cel.position.x
        local imgY = y - cel.position.y
        if imgX >= 0 and imgX < img.width - 1 and imgY >= 0 and imgY < img.height - 1 then
            local cR, cG, cB, cA = getRGBA(img, imgX, imgY)
            local rR, rG, rB, rA = getRGBA(img, imgX + 1, imgY)
            local bR, bG, bB, bA = getRGBA(img, imgX, imgY + 1)
            local brR, brG, brB, brA = getRGBA(img, imgX + 1, imgY + 1)
            
            if cA > 0 and rA > 0 and bA == 0 and brA > 0 then
                local blR = math.floor((cR + bR) / 2)
                local blG = math.floor((cG + bG) / 2)
                local blB = math.floor((cB + bB) / 2)
                local blA = math.floor((cA + bA) / 2)
                
                table.insert(suggestions, makeSuggestionEntry(x, y + 1, bR, bG, bB, bA, cR, cG, cB, cA, blR, blG, blB, blA))
            end
        end
    end
end

print('{{"suggestions":[' .. table.concat(suggestions, ',') .. '],"applied":false,"total_edges":' .. #suggestions .. '}}')'''


def generate_apply_antialiasing_pixels(
    layer_name: str, frame_number: int, suggestions: list[dict], use_palette: bool
) -> str:
    escaped_name = escape_string(layer_name)
    snap_helper = generate_palette_snapper_helper() if use_palette else ""

    pixel_commands = []
    for s in suggestions:
        c = s["suggested_color"].lstrip("#")
        if len(c) >= 8:
            r, g, b, a = (
                int(c[0:2], 16),
                int(c[2:4], 16),
                int(c[4:6], 16),
                int(c[6:8], 16),
            )
        else:
            r, g, b, a = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16), 255
        pixel_commands.append(
            f"img:putPixel({s['x']} - cel.position.x, {s['y']} - cel.position.y, {format_color_with_palette(Color(r=r, g=g, b=b, a=a), use_palette)})"
        )

    pixels_str = "\n\t".join(pixel_commands)

    return f'''{snap_helper}
local spr = app.activeSprite
if not spr then
    error("No active sprite")
end

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

local cel = layer:cel(frame)
if not cel then
    cel = spr:newCel(layer, frame)
end

local img = cel.image

app.transaction(function()
{pixels_str}
end)

spr:saveAs(spr.filename)
print("Antialiasing applied successfully")'''

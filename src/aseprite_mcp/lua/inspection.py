from __future__ import annotations

from aseprite_mcp.lua.core import escape_string


def generate_get_pixels(
    layer_name: str, frame_number: int, x: int, y: int, width: int, height: int
) -> str:
    escaped_name = escape_string(layer_name)

    return f'''local spr = app.activeSprite
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
local pixels = {{}}

for py = {y}, {y + height - 1} do
    for px = {x}, {x + width - 1} do
        local imgX = px - cel.position.x
        local imgY = py - cel.position.y
        if imgX >= 0 and imgX < img.width and imgY >= 0 and imgY < img.height then
            local pixel = img:getPixel(imgX, imgY)
            local a = app.pixelColor.rgbaA(pixel)
            local r = app.pixelColor.rgbaR(pixel)
            local g = app.pixelColor.rgbaG(pixel)
            local b = app.pixelColor.rgbaB(pixel)
            local parts = {{}}
            table.insert(parts, string.format('{{"x":%d,"y":%d,"color":"#%02x%02x%02x%02x"}}', px, py, r, g, b, a))
            for _, p in ipairs(parts) do
                table.insert(pixels, p)
            end
        end
    end
end

print('[' .. table.concat(pixels, ',') .. ']')'''


def generate_get_pixels_with_pagination(
    layer_name: str,
    frame_number: int,
    x: int,
    y: int,
    width: int,
    height: int,
    offset: int,
    page_size: int,
) -> str:
    escaped_name = escape_string(layer_name)

    return f'''local spr = app.activeSprite
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
local pixels = {{}}
local count = 0
local offset = {offset}
local pageSize = {page_size}

for py = {y}, {y + height - 1} do
    for px = {x}, {x + width - 1} do
        local imgX = px - cel.position.x
        local imgY = py - cel.position.y
        if imgX >= 0 and imgX < img.width and imgY >= 0 and imgY < img.height then
            if count >= offset and count < offset + pageSize then
                local pixel = img:getPixel(imgX, imgY)
                local a = app.pixelColor.rgbaA(pixel)
                local r = app.pixelColor.rgbaR(pixel)
                local g = app.pixelColor.rgbaG(pixel)
                local b = app.pixelColor.rgbaB(pixel)
                table.insert(pixels, string.format('{{"x":%d,"y":%d,"color":"#%02x%02x%02x%02x"}}', px, py, r, g, b, a))
            end
            count = count + 1
        end
    end
end

print('[' .. table.concat(pixels, ',') .. ']')'''

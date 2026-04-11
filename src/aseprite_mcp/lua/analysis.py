from __future__ import annotations

from aseprite_mcp.lua.core import escape_string

_H = "#"


def generate_analyze_reference(
    reference_path: str,
    target_width: int,
    target_height: int,
    palette_size: int,
    brightness_levels: int,
    edge_threshold: int,
) -> str:
    escaped_path = escape_string(reference_path)

    return (
        f'''local json = require("dkjson")

local spr = Sprite("{escaped_path}")
if not spr then
    error("Failed to load reference image")
end

local targetWidth = {target_width}
local targetHeight = {target_height}
local paletteSize = {palette_size}
local brightnessLevels = {brightness_levels}
local edgeThreshold = {edge_threshold}

local function getRGBA(img, x, y)
    local px = img:getPixel(x, y)
    return app.pixelColor.rgbaR(px), app.pixelColor.rgbaG(px), app.pixelColor.rgbaB(px), app.pixelColor.rgbaA(px)
end

local palette = {{}}
local paletteSet = {{}}
local sampleStep = math.max(1, math.floor((spr.width * spr.height) / paletteSize))

for y = 0, spr.height - 1, sampleStep do
    for x = 0, spr.width - 1, sampleStep do
        local r, g, b, a = getRGBA(spr.cels[1].image, x, y)
        if a > 0 then
            local colorKey = string.format("%02x%02x%02x", r, g, b)
            if not paletteSet[colorKey] then
                paletteSet[colorKey] = true
                table.insert(palette, string.format("'''
        + _H
        + f"""%02x%02x%02x", r, g, b))
                if """
        + _H
        + f"""palette >= paletteSize then
                    break
                end
            end
        end
    end
    if """
        + _H
        + f'''palette >= paletteSize then
        break
    end
end

local brightnessMap = {{
    grid = {{}},
    legend = {{}},
    width = math.min(targetWidth, spr.width),
    height = math.min(targetHeight, spr.height)
}}

local scaleX = spr.width / brightnessMap.width
local scaleY = spr.height / brightnessMap.height

for y = 1, brightnessMap.height do
    brightnessMap.grid[y] = {{}}
    for x = 1, brightnessMap.width do
        local srcX = math.floor((x - 1) * scaleX)
        local srcY = math.floor((y - 1) * scaleY)
        local r, g, b, a = getRGBA(spr.cels[1].image, srcX, srcY)
        local brightness = math.floor((r + g + b) / 3 / 255 * (brightnessLevels - 1))
        brightnessMap.grid[y][x] = brightness
    end
end

for i = 0, brightnessLevels - 1 do
    brightnessMap.legend[i + 1] = string.format("'''
        + _H
        + f"""%02x%02x%02x", i * 255, i * 255, i * 255)
end

local edgeMap = {{
    grid = {{}},
    majorEdges = {{}},
    width = brightnessMap.width,
    height = brightnessMap.height
}}

for y = 1, brightnessMap.height do
    edgeMap.grid[y] = {{}}
    for x = 1, brightnessMap.width do
        edgeMap.grid[y][x] = 0
    end
end

for y = 2, brightnessMap.height - 1 do
    for x = 2, brightnessMap.width - 1 do
        local gx = -brightnessMap.grid[y-1][x-1] + brightnessMap.grid[y-1][x+1]
                 - 2*brightnessMap.grid[y][x-1] + 2*brightnessMap.grid[y][x+1]
                 - brightnessMap.grid[y+1][x-1] + brightnessMap.grid[y+1][x+1]
        local gy = -brightnessMap.grid[y-1][x-1] - 2*brightnessMap.grid[y-1][x] - brightnessMap.grid[y-1][x+1]
                 + brightnessMap.grid[y+1][x-1] + 2*brightnessMap.grid[y+1][x] + brightnessMap.grid[y+1][x+1]
        local magnitude = math.sqrt(gx*gx + gy*gy)
        
        if magnitude > edgeThreshold then
            edgeMap.grid[y][x] = 1
            table.insert(edgeMap.majorEdges, {{x = x, y = y, strength = magnitude}})
        end
    end
end

local composition = {{
    focalPoints = {{}},
    ruleOfThirds = {{
        {{x = brightnessMap.width / 3, y = brightnessMap.height / 3}},
        {{x = brightnessMap.width * 2 / 3, y = brightnessMap.height / 3}},
        {{x = brightnessMap.width / 3, y = brightnessMap.height * 2 / 3}},
        {{x = brightnessMap.width * 2 / 3, y = brightnessMap.height * 2 / 3}}
    }}
}}

for _, point in ipairs(composition.ruleOfThirds) do
    table.insert(composition.focalPoints, {{
        x = math.floor(point.x),
        y = math.floor(point.y),
        strength = 0.5
    }})
end

local metadata = {{
    sourceDimensions = {{width = spr.width, height = spr.height}},
    targetDimensions = {{width = targetWidth, height = targetHeight}},
    scaleFactor = targetWidth / spr.width,
    dominantHue = 0,
    colorHarmony = "diverse",
    contrastRatio = "medium"
}}

local result = {{
    palette = palette,
    brightnessMap = brightnessMap,
    edgeMap = edgeMap,
    composition = composition,
    metadata = metadata,
    ditheringZones = {{}}
}}

print(json.encode(result))"""
    )

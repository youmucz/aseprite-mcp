from __future__ import annotations

from aseprite_mcp.lua.core import escape_string, generate_palette_snapper_helper, format_color_with_palette_for_tool


def generate_draw_with_dither(layer_name: str, frame_number: int, region_x: int, region_y: int, region_width: int, region_height: int, color1: str, color2: str, pattern: str, density: float) -> str:
    escaped_name = escape_string(layer_name)
    
    c1 = color1.lstrip("#")
    r1, g1, b1 = int(c1[0:2], 16), int(c1[2:4], 16), int(c1[4:6], 16)
    
    c2 = color2.lstrip("#")
    r2, g2, b2 = int(c2[0:2], 16), int(c2[2:4], 16), int(c2[4:6], 16)
    
    pattern_maps = {
        "bayer_2x2": [[0, 2], [3, 1]],
        "bayer_4x4": [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]],
        "bayer_8x8": [[0, 32, 8, 40, 2, 34, 10, 42], [48, 16, 56, 24, 50, 18, 58, 26], [12, 44, 4, 36, 14, 46, 6, 38], [60, 28, 52, 20, 62, 30, 54, 22], [3, 35, 11, 43, 1, 33, 9, 41], [51, 19, 59, 27, 49, 17, 57, 25], [15, 47, 7, 39, 13, 45, 5, 37], [63, 31, 55, 23, 61, 29, 53, 21]],
    }
    
    bayer_matrix = None
    if pattern in pattern_maps:
        bayer_matrix = pattern_maps[pattern]
    
    matrix_str = "{" + ",".join(["{" + ",".join([str(v) for v in row]) + "}" for row in bayer_matrix]) + "}" if bayer_matrix else "nil"
    
    pattern_type = "checkerboard" if pattern == "checkerboard" else "bayer"
    
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

local cel = layer:cel(frame)
if not cel then
    cel = spr:newCel(layer, frame)
end

local img = cel.image
local color1 = Color({r1}, {g1}, {b1}, 255)
local color2 = Color({r2}, {g2}, {b2}, 255)
local density = {density}
local patternType = "{pattern_type}"
local bayerMatrix = {matrix_str}

-- Dithering function
local function applyDither(img, startX, startY, w, h, c1, c2, density, patternType, bayerMatrix)
    for y = startY, startY + h - 1 do
        for x = startX, startX + w - 1 do
            if x >= 0 and x < img.width and y >= 0 and y < img.height then
                local useColor2 = false
                
                if patternType == "checkerboard" then
                    useColor2 = (math.floor(x / 2) + math.floor(y / 2)) % 2 == 0
                elseif patternType == "bayer" and bayerMatrix then
                    local matrixSize = #bayerMatrix
                    local bx = x % matrixSize
                    local by = y % matrixSize
                    local threshold = bayerMatrix[by + 1][bx + 1] / 64.0
                    useColor2 = density > threshold
                elseif patternType == "noise" then
                    useColor2 = math.random() < density
                elseif patternType == "horizontal_lines" then
                    useColor2 = (y % 2 == 0)
                elseif patternType == "vertical_lines" then
                    useColor2 = (x % 2 == 0)
                elseif patternType == "diagonal" then
                    useColor2 = ((x + y) % 2 == 0)
                elseif patternType == "cross" then
                    useColor2 = (x % 3 == 0) or (y % 3 == 0)
                elseif patternType == "dots" then
                    useColor2 = (x % 4 == 0) and (y % 4 == 0)
                end
                
                local color = useColor2 and c2 or c1
                img:putPixel(x, y, color)
            end
        end
    end
end

app.transaction(function()
    applyDither(img, {region_x}, {region_y}, {region_width}, {region_height}, color1, color2, density, patternType, bayerMatrix)
end)

spr:saveAs(spr.filename)
print("Dithering applied successfully")'''

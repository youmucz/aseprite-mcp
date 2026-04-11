from __future__ import annotations

_H = "#"  # Lua length operator, kept outside f-strings to avoid SyntaxError


def generate_get_palette() -> str:
    return (
        """local spr = app.activeSprite
if not spr then
	error("No active sprite")
end

-- Get palette
local palette = spr.palettes[1]
if not palette then
	error("No palette found")
end

-- Extract colors as hex strings
local colors = {}
for i = 0, """
        + _H
        + """palette - 1 do
	local color = palette:getColor(i)
	local hex = string.format('"""
        + _H
        + """%02X%02X%02X', color.red, color.green, color.blue)
	table.insert(colors, hex)
end

-- Format as JSON
local colorList = '["' .. table.concat(colors, '","') .. '"]'
local output = string.format('{"colors":%s,"size":%d}', colorList, """
        + _H
        + """palette)

print(output)"""
    )


def generate_set_palette(colors: list[str]) -> str:
    if len(colors) == 0:
        return """error("No colors provided for palette")"""

    color_list = "{\n"
    for i, hex_color in enumerate(colors):
        hex_color = hex_color.lstrip("#")
        if len(hex_color) != 6 and len(hex_color) != 8:
            continue

        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        if len(hex_color) == 8:
            a = int(hex_color[6:8], 16)
        else:
            a = 255

        color_list += f"\t\tColor{{r={r}, g={g}, b={b}, a={a}}}"
        if i < len(colors) - 1:
            color_list += ","
        color_list += "\n"
    color_list += "\t}"

    return f"""local spr = app.activeSprite
if not spr then
	error("No active sprite")
end

-- Get or create palette
local palette = spr.palettes[1]
if not palette then
	error("No palette found")
end

-- Resize palette to match color count
palette:resize({len(colors)})

-- Set palette colors
local colors = {color_list}

for i, color in ipairs(colors) do
	palette:setColor(i - 1, color)  -- Palette is 0-indexed
end

spr:saveAs(spr.filename)
print("Palette set successfully")"""


def generate_set_palette_color(index: int, hex_color: str) -> str:
    hex_color = hex_color.lstrip("#")

    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    if len(hex_color) == 8:
        a = int(hex_color[6:8], 16)
    else:
        a = 255

    return (
        f"""local spr = app.activeSprite
if not spr then
	error("No active sprite")
end

-- Get palette
local palette = spr.palettes[1]
if not palette then
	error("No palette found")
end

-- Validate index
if {index} < 0 or {index} >= """
        + _H
        + f"""palette then
	error(string.format("Palette index %d out of range (palette has %d colors)", {index}, """
        + _H
        + f"""palette))
end

-- Set color at index
palette:setColor({index}, Color{{r={r}, g={g}, b={b}, a={a}}})

spr:saveAs(spr.filename)
print("Palette color set successfully")"""
    )


def generate_add_palette_color(hex_color: str) -> str:
    hex_color = hex_color.lstrip("#")

    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    if len(hex_color) == 8:
        a = int(hex_color[6:8], 16)
    else:
        a = 255

    return (
        f"""local spr = app.activeSprite
if not spr then
	error("No active sprite")
end

-- Get palette
local palette = spr.palettes[1]
if not palette then
	error("No palette found")
end

-- Check if palette is at maximum size
if """
        + _H
        + f"""palette >= 256 then
	error("Palette is already at maximum size (256 colors)")
end

-- Add new color to palette
local newIndex = """
        + _H
        + """
palette
palette:resize("""
        + _H
        + f"""palette + 1)
palette:setColor(newIndex, Color{{r={r}, g={g}, b={b}, a={a}}})

spr:saveAs(spr.filename)

-- Output JSON with color_index
local output = string.format('{{"color_index":%d}}', newIndex)
print(output)"""
    )


def generate_sort_palette(method: str, ascending: bool) -> str:
    rgb_to_hsl = """-- Convert RGB to HSL
local function rgbToHSL(r, g, b)
	r, g, b = r / 255, g / 255, b / 255
	local max = math.max(r, g, b)
	local min = math.min(r, g, b)
	local delta = max - min

	local h, s, l = 0, 0, (max + min) / 2

	if delta ~= 0 then
		-- Calculate saturation
		if l < 0.5 then
			s = delta / (max + min)
		else
			s = delta / (2.0 - max - min)
		end

		-- Calculate hue
		if max == r then
			h = ((g - b) / delta)
			if g < b then
				h = h + 6.0
			end
		elseif max == g then
			h = ((b - r) / delta) + 2.0
		elseif max == b then
			h = ((r - g) / delta) + 4.0
		end

		h = h * 60.0
	end

	return h, s, l
end"""

    sort_key_map = {
        "hue": "h",
        "saturation": "s",
        "brightness": "l",
        "luminance": "l",
    }
    sort_key = sort_key_map.get(method, "h")

    sort_direction = ">" if not ascending else "<"

    lua_hsl_key = "h" if sort_key == "h" else sort_key

    return (
        """local spr = app.activeSprite
if not spr then
	error("No active sprite")
end

-- Get palette
local palette = spr.palettes[1]
if not palette then
	error("No palette found")
end

"""
        + rgb_to_hsl
        + """

-- Extract colors with HSL values
local colors = {}
for i = 0, """
        + _H
        + """palette - 1 do
	local color = palette:getColor(i)
	local h, s, l = rgbToHSL(color.red, color.green, color.blue)
	table.insert(colors, {
		index = i,
		color = color,
		h = h,
		s = s,
		l = l
	})
end

-- Sort colors by """
        + method
        + """
table.sort(colors, function(a, b)
	return a."""
        + sort_key
        + " "
        + sort_direction
        + " b."
        + sort_key
        + """
end)

-- Apply sorted colors back to palette
for i, entry in ipairs(colors) do
	palette:setColor(i - 1, entry.color)
end

spr:saveAs(spr.filename)
print("Palette sorted by """
        + method
        + """ successfully")"""
    )


def generate_apply_shading(
    layer_name: str,
    frame_number: int,
    x: int,
    y: int,
    width: int,
    height: int,
    palette: list[str],
    light_direction: str,
    intensity: float,
    style: str,
) -> str:
    from aseprite_mcp.lua.core import escape_string

    escaped_layer = escape_string(layer_name)

    palette_colors = "{\n"
    for i, hex_color in enumerate(palette):
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        if len(hex_color) == 8:
            a = int(hex_color[6:8], 16)
        else:
            a = 255

        palette_colors += f"\t\t{{r={r}, g={g}, b={b}, a={a}}}"
        if i < len(palette) - 1:
            palette_colors += ","
        palette_colors += "\n"
    palette_colors += "\t}"

    dx_map = {
        "top_left": (-1, -1),
        "top": (0, -1),
        "top_right": (1, -1),
        "left": (-1, 0),
        "right": (1, 0),
        "bottom_left": (-1, 1),
        "bottom": (0, 1),
        "bottom_right": (1, 1),
    }
    dx, dy = dx_map.get(light_direction, (-1, -1))

    return (
        f"""local spr = app.activeSprite
if not spr then
	error("No active sprite")
end

-- Find layer
local layer = nil
for _, l in ipairs(spr.layers) do
	if l.name == "{escaped_layer}" then
		layer = l
		break
	end
end

if not layer then
	error("Layer not found: {escaped_layer}")
end

-- Get frame
local frame = spr.frames[{frame_number}]
if not frame then
	error("Frame not found: {frame_number}")
end

-- Get or create cel
local cel = layer:cel(frame)
if not cel then
	error("No cel found in frame {frame_number}")
end

local img = cel.image

-- Palette colors (ordered darkest to lightest)
local palette = {palette_colors}

-- Light direction offset
local lightDx = {dx}
local lightDy = {dy}
local intensity = {intensity}
local style = "{style}"

-- Helper: Find nearest palette color
local function findNearestPaletteColor(r, g, b, a)
	local minDist = math.huge
	local nearestColor = palette[1]

	for _, palColor in ipairs(palette) do
		local dr = r - palColor.r
		local dg = g - palColor.g
		local db = b - palColor.b
		local da = a - palColor.a
		local dist = dr*dr + dg*dg + db*db + da*da

		if dist < minDist then
			minDist = dist
			nearestColor = palColor
		end
	end

	return app.pixelColor.rgba(nearestColor.r, nearestColor.g, nearestColor.b, nearestColor.a)
end

-- Helper: Calculate shading factor based on position and light direction
local function calculateShadingFactor(px, py, regionX, regionY, regionW, regionH)
	-- Normalize position to 0-1
	local normX = (px - regionX) / regionW
	local normY = (py - regionY) / regionH

	-- Calculate distance from light source direction
	local lightFactor = 0.5
	if lightDx < 0 then
		lightFactor = lightFactor + (1 - normX) * 0.5
	elseif lightDx > 0 then
		lightFactor = lightFactor + normX * 0.5
	end

	if lightDy < 0 then
		lightFactor = lightFactor + (1 - normY) * 0.5
	elseif lightDy > 0 then
		lightFactor = lightFactor + normY * 0.5
	end

	-- Normalize to 0-1 range
	lightFactor = math.max(0, math.min(1, lightFactor))

	return lightFactor
end

-- Helper: Apply shading to color
local function applyShading(pixelValue, shadingFactor)
	local r = app.pixelColor.rgbaR(pixelValue)
	local g = app.pixelColor.rgbaG(pixelValue)
	local b = app.pixelColor.rgbaB(pixelValue)
	local a = app.pixelColor.rgbaA(pixelValue)

	if a == 0 then
		return pixelValue  -- Skip transparent pixels
	end

	-- Apply shading based on style
	local shadedR, shadedG, shadedB

	if style == "hard" then
		-- Hard shading: quantize to palette steps
		local paletteIndex = math.floor(shadingFactor * ("""
        + _H
        + """palette - 1)) + 1
		paletteIndex = math.max(1, math.min("""
        + _H
        + """palette, paletteIndex))
		return app.pixelColor.rgba(palette[paletteIndex].r, palette[paletteIndex].g, palette[paletteIndex].b, a)
	elseif style == "smooth" then
		-- Smooth shading: blend current color toward palette extremes
		local targetBrightness = shadingFactor
		local currentBrightness = (0.299 * r + 0.587 * g + 0.114 * b) / 255

		-- Blend toward target brightness
		local blend = intensity * 0.5
		shadedR = math.floor(r * (1 - blend) + r * (targetBrightness / math.max(0.01, currentBrightness)) * blend)
		shadedG = math.floor(g * (1 - blend) + g * (targetBrightness / math.max(0.01, currentBrightness)) * blend)
		shadedB = math.floor(b * (1 - blend) + b * (targetBrightness / math.max(0.01, currentBrightness)) * blend)
	else  -- pillow (avoid - but included for completeness)
		-- Pillow shading: center highlight regardless of light direction
		local centerX = 0.5
		local centerY = 0.5
		local distFromCenter = math.sqrt((shadingFactor - centerX)^2 + (shadingFactor - centerY)^2)
		local pillow = 1 - distFromCenter

		shadedR = math.floor(r * (1 + pillow * intensity))
		shadedG = math.floor(g * (1 + pillow * intensity))
		shadedB = math.floor(b * (1 + pillow * intensity))
	end

	-- Clamp values
	shadedR = math.max(0, math.min(255, shadedR))
	shadedG = math.max(0, math.min(255, shadedG))
	shadedB = math.max(0, math.min(255, shadedB))

	-- Find nearest palette color
	return findNearestPaletteColor(shadedR, shadedG, shadedB, a)
end

-- Apply shading to region
local affectedPixels = 0

app.transaction(function()
	for py = {y}, {y + height - 1} do
		for px = {x}, {x + width - 1} do
			-- Adjust coordinates relative to cel position
			local imgX = px - cel.position.x
			local imgY = py - cel.position.y

			-- Check if coordinates are within image bounds
			if imgX >= 0 and imgX < img.width and imgY >= 0 and imgY < img.height then
				local pixelValue = img:getPixel(imgX, imgY)
				local alpha = app.pixelColor.rgbaA(pixelValue)

				if alpha > 0 then
					local shadingFactor = calculateShadingFactor(px, py, {x}, {y}, {width}, {height})
					local shadedColor = applyShading(pixelValue, shadingFactor)
					img:drawPixel(imgX, imgY, shadedColor)
					affectedPixels = affectedPixels + 1
				end
			end
		end
	end
end)

spr:saveAs(spr.filename)
print(string.format("Shading applied to %d pixels", affectedPixels))"""
    )

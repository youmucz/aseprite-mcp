from __future__ import annotations

from aseprite_mcp.tools.common import Color, Point, Rectangle


def escape_string(s: str) -> str:
    s = s.replace("\\", "\\\\")
    s = s.replace('"', '\\"')
    s = s.replace("\n", "\\n")
    s = s.replace("\r", "\\r")
    s = s.replace("\t", "\\t")
    return s


def format_color(c: Color) -> str:
    return f"Color({c.r}, {c.g}, {c.b}, {c.a})"


def format_color_with_palette(c: Color, use_palette: bool) -> str:
    if not use_palette:
        return format_color(c)
    return f"snapToPaletteForPixel({c.r}, {c.g}, {c.b}, {c.a})"


def format_color_with_palette_for_tool(c: Color, use_palette: bool) -> str:
    if not use_palette:
        return format_color(c)
    return f"snapToPaletteForTool({c.r}, {c.g}, {c.b}, {c.a})"


def generate_palette_snapper_helper() -> str:
    return """
-- Helper: Find nearest palette index for given RGBA color
local function findNearestPaletteIndex(r, g, b, a)
	local spr = app.activeSprite
	local palette = spr.palettes[1]
	if not palette or #palette == 0 then
		return 0
	end

	local minDist = math.huge
	local nearestIndex = 0

	for i = 0, #palette - 1 do
		local palColor = palette:getColor(i)
		local dr = r - palColor.red
		local dg = g - palColor.green
		local db = b - palColor.blue
		local da = a - palColor.alpha
		local dist = dr*dr + dg*dg + db*db + da*da

		if dist < minDist then
			minDist = dist
			nearestIndex = i
		end
	end

	return nearestIndex
end

-- Helper: Snap color for img:putPixel (returns palette index in indexed mode)
local function snapToPaletteForPixel(r, g, b, a)
	local spr = app.activeSprite
	if spr.colorMode == ColorMode.INDEXED then
		-- In indexed mode, return the palette index directly
		return findNearestPaletteIndex(r, g, b, a)
	else
		-- In RGB/Grayscale, return pixel color
		local nearestIndex = findNearestPaletteIndex(r, g, b, a)
		local palette = spr.palettes[1]
		local nearestColor = palette:getColor(nearestIndex)
		return app.pixelColor.rgba(nearestColor.red, nearestColor.green, nearestColor.blue, nearestColor.alpha)
	end
end

-- Helper: Snap color for app.useTool (returns index in indexed mode, pixel color otherwise)
local function snapToPaletteForTool(r, g, b, a)
	local spr = app.activeSprite
	local nearestIndex = findNearestPaletteIndex(r, g, b, a)

	if spr.colorMode == ColorMode.INDEXED then
		-- In indexed mode, app.useTool expects palette index
		return nearestIndex
	else
		-- In RGB/Grayscale, app.useTool expects pixel color
		local palette = spr.palettes[1]
		local nearestColor = palette:getColor(nearestIndex)
		return app.pixelColor.rgba(nearestColor.red, nearestColor.green, nearestColor.blue, nearestColor.alpha)
	end
end

-- Default snapToPalette for backwards compatibility (uses ForPixel variant)
local function snapToPalette(r, g, b, a)
	return snapToPaletteForPixel(r, g, b, a)
end
"""


def format_point(p: Point) -> str:
    return f"Point({p.x}, {p.y})"


def format_rectangle(r: Rectangle) -> str:
    return f"Rectangle({r.x}, {r.y}, {r.width}, {r.height})"


def wrap_in_transaction(code: str) -> str:
    return f"""app.transaction(function()
{code}
end)"""

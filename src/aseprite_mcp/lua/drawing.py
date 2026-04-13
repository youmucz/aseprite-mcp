from __future__ import annotations

from aseprite_mcp.lua.core import (
    escape_string,
    format_color_with_palette,
    format_color_with_palette_for_tool,
    format_point,
    generate_palette_snapper_helper,
)
from aseprite_mcp.tools.common import Color, Pixel, Point


def generate_draw_pixels(
    layer_name: str, frame_number: int, pixels: list[Pixel], use_palette: bool
) -> str:
    escaped_name = escape_string(layer_name)

    code = ""

    code += generate_palette_snapper_helper()
    code += "\n"

    code += f"""local spr = app.activeSprite
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

app.transaction(function()
	local cel = layer:cel(frame)
	if not cel then
		cel = spr:newCel(layer, frame)
	end

	local img = cel.image
"""

    for p in pixels:
        code += f"\timg:putPixel({p.x}, {p.y}, snapToPaletteForPixel({p.color.r}, {p.color.g}, {p.color.b}, {p.color.a}))\n"

    code += """end)

spr:saveAs(spr.filename)
print("Pixels drawn successfully")"""

    return code


def generate_draw_line(
    layer_name: str,
    frame_number: int,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    color: Color,
    thickness: int,
    use_palette: bool,
) -> str:
    escaped_name = escape_string(layer_name)

    code = ""

    if use_palette:
        code += generate_palette_snapper_helper()
        code += "\n"

    code += f"""local spr = app.activeSprite
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

app.transaction(function()
	app.activeLayer = layer
	app.activeFrame = frame

	local brush = Brush({thickness})

	app.useTool{{
		tool = "line",
		color = {format_color_with_palette_for_tool(color, use_palette)},
		brush = brush,
		points = {{{format_point(Point(x=x1, y=y1))}, {format_point(Point(x=x2, y=y2))}}}
	}}
end)

spr:saveAs(spr.filename)
print("Line drawn successfully")"""

    return code


def generate_draw_contour(
    layer_name: str,
    frame_number: int,
    points: list[Point],
    color: Color,
    thickness: int,
    closed: bool,
    use_palette: bool,
) -> str:
    escaped_name = escape_string(layer_name)

    code = ""

    if use_palette:
        code += generate_palette_snapper_helper()
        code += "\n"

    code += f"""local spr = app.activeSprite
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

app.transaction(function()
	app.activeLayer = layer
	app.activeFrame = frame

	local brush = Brush({thickness})
	local color = {format_color_with_palette_for_tool(color, use_palette)}

	-- Draw lines connecting each point
"""

    for i in range(len(points) - 1):
        code += f"""
	app.useTool{{
		tool = "line",
		color = color,
		brush = brush,
		points = {{{format_point(points[i])}, {format_point(points[i + 1])}}}
	}}
"""

    if closed and len(points) > 0:
        code += f"""
	-- Close the contour
	app.useTool{{
		tool = "line",
		color = color,
		brush = brush,
		points = {{{format_point(points[-1])}, {format_point(points[0])}}}
	}}
"""

    code += """end)

spr:saveAs(spr.filename)
print("Contour drawn successfully")"""

    return code


def generate_draw_rectangle(
    layer_name: str,
    frame_number: int,
    x: int,
    y: int,
    width: int,
    height: int,
    color: Color,
    filled: bool,
    use_palette: bool,
) -> str:
    escaped_name = escape_string(layer_name)
    tool = "filled_rectangle" if filled else "rectangle"

    code = ""

    if use_palette:
        code += generate_palette_snapper_helper()
        code += "\n"

    code += f"""local spr = app.activeSprite
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

app.transaction(function()
	app.activeLayer = layer
	app.activeFrame = frame

	app.useTool{{
		tool = "{tool}",
		color = {format_color_with_palette_for_tool(color, use_palette)},
		points = {{{format_point(Point(x=x, y=y))}, {format_point(Point(x=x + width - 1, y=y + height - 1))}}}
	}}
end)

spr:saveAs(spr.filename)
print("Rectangle drawn successfully")"""

    return code


def generate_draw_circle(
    layer_name: str,
    frame_number: int,
    center_x: int,
    center_y: int,
    radius: int,
    color: Color,
    filled: bool,
    use_palette: bool,
) -> str:
    escaped_name = escape_string(layer_name)
    tool = "filled_ellipse" if filled else "ellipse"

    x1 = center_x - radius
    y1 = center_y - radius
    x2 = center_x + radius
    y2 = center_y + radius

    code = ""

    if use_palette:
        code += generate_palette_snapper_helper()
        code += "\n"

    code += f"""local spr = app.activeSprite
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

app.transaction(function()
	app.activeLayer = layer
	app.activeFrame = frame

	app.useTool{{
		tool = "{tool}",
		color = {format_color_with_palette_for_tool(color, use_palette)},
		points = {{{format_point(Point(x=x1, y=y1))}, {format_point(Point(x=x2, y=y2))}}}
	}}
end)

spr:saveAs(spr.filename)
print("Circle drawn successfully")"""

    return code


def generate_fill_area(
    layer_name: str,
    frame_number: int,
    x: int,
    y: int,
    color: Color,
    tolerance: int,
    use_palette: bool,
) -> str:
    escaped_name = escape_string(layer_name)

    code = ""

    if use_palette:
        code += generate_palette_snapper_helper()
        code += "\n"

    code += f"""local spr = app.activeSprite
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

app.transaction(function()
	app.activeLayer = layer
	app.activeFrame = frame

	app.useTool{{
		tool = "paint_bucket",
		color = {format_color_with_palette_for_tool(color, use_palette)},
		points = {{{format_point(Point(x=x, y=y))}}},
		contiguous = true,
		tolerance = {tolerance}
	}}
end)

spr:saveAs(spr.filename)
print("Area filled successfully")"""

    return code

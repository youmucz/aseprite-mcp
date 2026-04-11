from __future__ import annotations

from aseprite_mcp.lua.core import escape_string, wrap_in_transaction


def generate_select_rectangle(
    x: int, y: int, width: int, height: int, mode: str
) -> str:
    return f"""local spr = app.activeSprite
if not spr then
	error("No active sprite")
end

local rect = Rectangle({x}, {y}, {width}, {height})
local sel = Selection(rect)

if "{mode}" == "replace" then
	spr.selection = sel
elseif "{mode}" == "add" then
	spr.selection:add(sel)
elseif "{mode}" == "subtract" then
	spr.selection:subtract(sel)
elseif "{mode}" == "intersect" then
	spr.selection:intersect(sel)
end

-- Persist selection state to sprite.data for cross-process persistence
if not spr.selection.isEmpty then
	local bounds = spr.selection.bounds
	spr.data = string.format('{{"selection":{{"x":%d,"y":%d,"w":%d,"h":%d}}}}',
		bounds.x, bounds.y, bounds.width, bounds.height)
	spr:saveAs(spr.filename)
end

print("Rectangle selection created successfully")"""


def generate_select_ellipse(x: int, y: int, width: int, height: int, mode: str) -> str:
    return f"""local spr = app.activeSprite
if not spr then
	error("No active sprite")
end

-- Create ellipse selection by using drawPixel for each point on ellipse
local sel = Selection()
local rx = {width} / 2
local ry = {height} / 2
local cx = {x} + rx
local cy = {y} + ry

-- Midpoint ellipse algorithm to create selection
for angle = 0, 360 do
	local rad = math.rad(angle)
	local ex = math.floor(cx + rx * math.cos(rad))
	local ey = math.floor(cy + ry * math.sin(rad))
	-- Fill from center to edge
	for fillx = math.floor(cx - rx), math.floor(cx + rx) do
		for filly = math.floor(cy - ry), math.floor(cy + ry) do
			local dx = (fillx - cx) / rx
			local dy = (filly - cy) / ry
			if dx * dx + dy * dy <= 1 then
				sel:add(Rectangle(fillx, filly, 1, 1))
			end
		end
	end
	break  -- Only need one pass to fill
end

if "{mode}" == "replace" then
	spr.selection = sel
elseif "{mode}" == "add" then
	spr.selection:add(sel)
elseif "{mode}" == "subtract" then
	spr.selection:subtract(sel)
elseif "{mode}" == "intersect" then
	spr.selection:intersect(sel)
end

-- Persist selection state to sprite.data for cross-process persistence
if not spr.selection.isEmpty then
	local bounds = spr.selection.bounds
	spr.data = string.format('{{"selection":{{"x":%d,"y":%d,"w":%d,"h":%d}}}}',
		bounds.x, bounds.y, bounds.width, bounds.height)
	spr:saveAs(spr.filename)
end

print("Ellipse selection created successfully")"""


def generate_select_all() -> str:
    return """local spr = app.activeSprite
if not spr then
	error("No active sprite")
end

-- Create selection covering entire sprite
local rect = Rectangle(0, 0, spr.width, spr.height)
local sel = Selection(rect)
spr.selection = sel

-- Persist selection state to sprite.data for cross-process persistence
local bounds = spr.selection.bounds
spr.data = string.format('{{"selection":{{"x":%d,"y":%d,"w":%d,"h":%d}}}}',
	bounds.x, bounds.y, bounds.width, bounds.height)
spr:saveAs(spr.filename)

print("Select all completed successfully")"""


def generate_deselect() -> str:
    return """local spr = app.activeSprite
if not spr then
	error("No active sprite")
end

app.command.DeselectMask()

-- Clear persisted selection state
spr.data = ""
spr:saveAs(spr.filename)

print("Deselect completed successfully")"""


def generate_move_selection(dx: int, dy: int) -> str:
    return f"""local spr = app.activeSprite
if not spr then
	error("No active sprite")
end

-- Restore selection from persisted state if needed
if spr.selection.isEmpty and spr.data ~= "" then
	local x, y, w, h = spr.data:match('x":(%d+),"y":(%d+),"w":(%d+),"h":(%d+)')
	if x and y and w and h then
		spr.selection = Selection(Rectangle(tonumber(x), tonumber(y), tonumber(w), tonumber(h)))
	end
end

if spr.selection.isEmpty then
	error("No active selection to move")
end

local bounds = spr.selection.bounds
local newSel = Selection(Rectangle(bounds.x + {dx}, bounds.y + {dy}, bounds.width, bounds.height))
spr.selection = newSel

-- Persist updated selection state
local newBounds = spr.selection.bounds
spr.data = string.format('{{"selection":{{"x":%d,"y":%d,"w":%d,"h":%d}}}}',
	newBounds.x, newBounds.y, newBounds.width, newBounds.height)
spr:saveAs(spr.filename)

print("Selection moved successfully")"""


def generate_cut_selection(layer_name: str, frame_number: int) -> str:
    escaped_name = escape_string(layer_name)
    return f"""local spr = app.activeSprite
if not spr then
	error("No active sprite")
end

-- Restore selection from persisted state if needed
if spr.selection.isEmpty and spr.data ~= "" then
	local x, y, w, h = spr.data:match('x":(%d+),"y":(%d+),"w":(%d+),"h":(%d+)')
	if x and y and w and h then
		spr.selection = Selection(Rectangle(tonumber(x), tonumber(y), tonumber(w), tonumber(h)))
	end
end

if spr.selection.isEmpty then
	error("No active selection to cut")
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

-- Find or create hidden clipboard layer before cutting
local clipboardLayer = nil
for i, lyr in ipairs(spr.layers) do
	if lyr.name == "__mcp_clipboard__" then
		clipboardLayer = lyr
		break
	end
end

if not clipboardLayer then
	clipboardLayer = spr:newLayer()
	clipboardLayer.name = "__mcp_clipboard__"
	clipboardLayer.isVisible = false
end

-- Copy selected region to clipboard layer first
local cel = layer:cel(frame)
if cel then
	local bounds = spr.selection.bounds
	local clipImage = Image(bounds.width, bounds.height, spr.colorMode)
	clipImage:drawImage(cel.image, Point(-bounds.x, -bounds.y))

	-- Store in clipboard layer
	spr:newCel(clipboardLayer, 1, clipImage, Point(bounds.x, bounds.y))
end

-- Now cut from the source layer
app.transaction(function()
	local cel = layer:cel(frame)
	if cel then
		local bounds = spr.selection.bounds
		-- Clear pixels in selection
		for y = bounds.y, bounds.y + bounds.height - 1 do
			for x = bounds.x, bounds.x + bounds.width - 1 do
				if spr.selection:contains(x, y) then
					cel.image:drawPixel(x - cel.position.x, y - cel.position.y, Color{{r=0,g=0,b=0,a=0}})
				end
			end
		end
	end
end)

-- Selection cleared after cut, clear persisted state
spr.data = ""
spr:saveAs(spr.filename)
print("Cut selection completed successfully")"""


def generate_copy_selection() -> str:
    return """local spr = app.activeSprite
if not spr then
	error("No active sprite")
end

-- Restore selection from persisted state if needed
if spr.selection.isEmpty and spr.data ~= "" then
	local x, y, w, h = spr.data:match('x":(%d+),"y":(%d+),"w":(%d+),"h":(%d+)')
	if x and y and w and h then
		spr.selection = Selection(Rectangle(tonumber(x), tonumber(y), tonumber(w), tonumber(h)))
	end
end

if spr.selection.isEmpty then
	error("No active selection to copy")
end

-- Find or create hidden clipboard layer
local clipboardLayer = nil
for i, lyr in ipairs(spr.layers) do
	if lyr.name == "__mcp_clipboard__" then
		clipboardLayer = lyr
		break
	end
end

if not clipboardLayer then
	clipboardLayer = spr:newLayer()
	clipboardLayer.name = "__mcp_clipboard__"
	clipboardLayer.isVisible = false
end

-- Get the selected image from layer 1, frame 1
-- In batch mode, we need to explicitly use frame 1 since app.activeFrame/activeLayer may not be set correctly
local sourceLayer = spr.layers[1]
local sourceFrame = spr.frames[1]
local sourceCel = sourceLayer:cel(sourceFrame)

if sourceCel then
	-- Copy selected region to clipboard layer
	local bounds = spr.selection.bounds
	local clipImage = Image(bounds.width, bounds.height, spr.colorMode)
	clipImage:drawImage(sourceCel.image, Point(-bounds.x, -bounds.y))

	-- Store in clipboard layer at frame 1
	spr:newCel(clipboardLayer, 1, clipImage, Point(bounds.x, bounds.y))
end

spr:saveAs(spr.filename)
print("Copy selection completed successfully")"""


def generate_paste_clipboard(
    layer_name: str, frame_number: int, x: int | None, y: int | None
) -> str:
    escaped_name = escape_string(layer_name)

    if x is not None and y is not None:
        paste_pos = f"local pasteX, pasteY = {x}, {y}"
    else:
        paste_pos = "local pasteX, pasteY = 0, 0"

    return f"""local spr = app.activeSprite
if not spr then
	error("No active sprite")
end

-- Find clipboard layer
local clipboardLayer = nil
for i, lyr in ipairs(spr.layers) do
	if lyr.name == "__mcp_clipboard__" then
		clipboardLayer = lyr
		break
	end
end

if not clipboardLayer then
	error("No clipboard content available")
end

local clipCel = clipboardLayer:cel(1)
if not clipCel then
	error("No clipboard content available")
end

-- Find target layer
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

-- Paste clipboard content to target layer
{paste_pos}

app.transaction(function()
	local targetCel = layer:cel(frame)
	if not targetCel then
		targetCel = spr:newCel(layer, frame)
	end

	-- Draw clipboard image onto target
	targetCel.image:drawImage(clipCel.image, Point(pasteX - targetCel.position.x, pasteY - targetCel.position.y))
end)

spr:saveAs(spr.filename)
print("Paste completed successfully")"""

from __future__ import annotations

from aseprite_mcp.lua.core import escape_string, wrap_in_transaction
from aseprite_mcp.tools.common import ColorMode


def generate_create_sprite(width: int, height: int, color_mode: ColorMode, filename: str) -> str:
    escaped_filename = escape_string(filename)

    if color_mode == ColorMode.INDEXED:
        return f"""local spr = Sprite({width}, {height}, {color_mode.to_lua()})
spr.transparentColor = 255
spr:saveAs("{escaped_filename}")
print("{escaped_filename}")"""

    return f"""local spr = Sprite({width}, {height}, {color_mode.to_lua()})
spr:saveAs("{escaped_filename}")
print("{escaped_filename}")"""


def generate_flatten_layers() -> str:
    return """local spr = app.activeSprite
if not spr then
	error("No active sprite")
end

app.transaction(function()
	spr:flatten()
end)

spr:saveAs(spr.filename)
print("Layers flattened successfully")"""


def generate_get_sprite_info() -> str:
    return """local spr = app.activeSprite
if not spr then
	error("No active sprite")
end

-- Map color mode enum to string
local colorModeStr = "rgb"
if spr.colorMode == ColorMode.GRAYSCALE then
	colorModeStr = "grayscale"
elseif spr.colorMode == ColorMode.INDEXED then
	colorModeStr = "indexed"
end

-- Collect layer names
local layers = {}
for i, layer in ipairs(spr.layers) do
	table.insert(layers, layer.name)
end

-- Format as JSON-like output
local output = string.format([[
{
	"width": %d,
	"height": %d,
	"color_mode": "%s",
	"frame_count": %d,
	"layer_count": %d,
	"layers": ["%s"]
}
]],
	spr.width,
	spr.height,
	colorModeStr,
	#spr.frames,
	#spr.layers,
	table.concat(layers, '","')
)

print(output)"""


def generate_add_layer(layer_name: str) -> str:
    escaped_name = escape_string(layer_name)
    return f"""local spr = app.activeSprite
if not spr then
	error("No active sprite")
end

app.transaction(function()
	local layer = spr:newLayer()
	layer.name = "{escaped_name}"
end)

spr:saveAs(spr.filename)
print("Layer added successfully")"""


def generate_add_frame(duration_ms: int) -> str:
    duration_sec = duration_ms / 1000.0
    return f"""local spr = app.activeSprite
if not spr then
	error("No active sprite")
end

app.transaction(function()
	local frame = spr:newFrame()
	frame.duration = {duration_sec:.3f}
end)

spr:saveAs(spr.filename)
print(#spr.frames)"""


def generate_delete_layer(layer_name: str) -> str:
    escaped_name = escape_string(layer_name)
    return f"""local spr = app.activeSprite
if not spr then
	error("No active sprite")
end

-- Check if this is the last layer
if #spr.layers == 1 then
	error("Cannot delete the last layer")
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

app.transaction(function()
	spr:deleteLayer(layer)
end)

spr:saveAs(spr.filename)
print("Layer deleted successfully")"""


def generate_delete_frame(frame_number: int) -> str:
    return f"""local spr = app.activeSprite
if not spr then
	error("No active sprite")
end

-- Check if this is the last frame
if #spr.frames == 1 then
	error("Cannot delete the last frame")
end

local frame = spr.frames[{frame_number}]
if not frame then
	error("Frame not found: {frame_number}")
end

app.transaction(function()
	spr:deleteFrame(frame)
end)

spr:saveAs(spr.filename)
print("Frame deleted successfully")"""

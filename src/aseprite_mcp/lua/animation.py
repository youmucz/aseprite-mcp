from __future__ import annotations

from aseprite_mcp.lua.core import escape_string, wrap_in_transaction


def generate_set_frame_duration(frame_number: int, duration_ms: int) -> str:
    duration_sec = duration_ms / 1000.0
    return f"""local spr = app.activeSprite
if not spr then
	error("No active sprite")
end

local frame = spr.frames[{frame_number}]
if not frame then
	error("Frame not found: {frame_number}")
end

app.transaction(function()
	frame.duration = {duration_sec:.3f}
end)

spr:saveAs(spr.filename)
print("Frame duration set successfully")"""


def generate_create_tag(tag_name: str, from_frame: int, to_frame: int, direction: str) -> str:
    escaped_name = escape_string(tag_name)

    ani_dir_map = {
        "forward": "AniDir.FORWARD",
        "reverse": "AniDir.REVERSE",
        "pingpong": "AniDir.PING_PONG",
    }
    ani_dir = ani_dir_map.get(direction, "AniDir.FORWARD")

    return f"""local spr = app.activeSprite
if not spr then
	error("No active sprite")
end

if #spr.frames < {to_frame} then
	error("Frame range exceeds sprite frames")
end

app.transaction(function()
	local tag = spr:newTag({from_frame}, {to_frame})
	tag.name = "{escaped_name}"
	tag.aniDir = {ani_dir}
end)

spr:saveAs(spr.filename)
print("Tag created successfully")"""


def generate_delete_tag(tag_name: str) -> str:
    escaped_name = escape_string(tag_name)

    return f"""local spr = app.activeSprite
if not spr then
	error("No active sprite")
end

-- Find tag by name
local tag = nil
for i, t in ipairs(spr.tags) do
	if t.name == "{escaped_name}" then
		tag = t
		break
	end
end

if not tag then
	error("Tag not found: {escaped_name}")
end

app.transaction(function()
	spr:deleteTag(tag)
end)

spr:saveAs(spr.filename)
print("Tag deleted successfully")"""


def generate_duplicate_frame(source_frame: int, insert_after: int) -> str:
    if insert_after == 0:
        return f"""local spr = app.activeSprite
if not spr then
	error("No active sprite")
end

local srcFrame = spr.frames[{source_frame}]
if not srcFrame then
	error("Source frame not found: {source_frame}")
end

local newFrame
app.transaction(function()
	newFrame = spr:newFrame(srcFrame)
	newFrame.duration = srcFrame.duration
end)

spr:saveAs(spr.filename)
print(#spr.frames)"""

    return f"""local spr = app.activeSprite
if not spr then
	error("No active sprite")
end

local srcFrame = spr.frames[{source_frame}]
if not srcFrame then
	error("Source frame not found: {source_frame}")
end

if #spr.frames < {insert_after} then
	error("Insert position exceeds sprite frames")
end

local newFrame
app.transaction(function()
	newFrame = spr:newFrame({insert_after} + 1)
	newFrame.duration = srcFrame.duration

	-- Copy cels from source frame to new frame
	for _, layer in ipairs(spr.layers) do
		local srcCel = layer:cel(srcFrame)
		if srcCel then
			local newCel = spr:newCel(layer, newFrame, srcCel.image, srcCel.position)
		end
	end
end)

spr:saveAs(spr.filename)
print({insert_after} + 1)"""


def generate_link_cel(layer_name: str, source_frame: int, target_frame: int) -> str:
    escaped_name = escape_string(layer_name)
    return f"""local spr = app.activeSprite
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

local srcFrame = spr.frames[{source_frame}]
if not srcFrame then
	error("Source frame not found: {source_frame}")
end

local tgtFrame = spr.frames[{target_frame}]
if not tgtFrame then
	error("Target frame not found: {target_frame}")
end

local srcCel = layer:cel(srcFrame)
if not srcCel then
	error("Source cel not found in frame {source_frame}")
end

app.transaction(function()
	-- Create linked cel by copying with same image reference
	spr:newCel(layer, tgtFrame, srcCel.image, srcCel.position)
end)

spr:saveAs(spr.filename)
print("Cel linked successfully")"""

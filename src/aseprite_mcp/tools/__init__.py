from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from aseprite_mcp.client import AsepriteClient
from aseprite_mcp.config import Config

from aseprite_mcp.tools.canvas import register_canvas_tools
from aseprite_mcp.tools.drawing import register_drawing_tools
from aseprite_mcp.tools.animation import register_animation_tools
from aseprite_mcp.tools.selection import register_selection_tools
from aseprite_mcp.tools.palette import register_palette_tools
from aseprite_mcp.tools.export import register_export_tools
from aseprite_mcp.tools.inspection import register_inspection_tools
from aseprite_mcp.tools.analysis import register_analysis_tools
from aseprite_mcp.tools.dithering import register_dithering_tools
from aseprite_mcp.tools.quantization import register_quantization_tools
from aseprite_mcp.tools.auto_shading import register_auto_shading_tools
from aseprite_mcp.tools.antialiasing import register_antialiasing_tools
from aseprite_mcp.tools.transform import register_transform_tools
from aseprite_mcp.tools.batch import register_batch_tools
from aseprite_mcp.tools.pixelize import register_pixelize_tools
from aseprite_mcp.tools.plan import register_plan_tools


def register_all_tools(mcp: FastMCP, client: AsepriteClient, config: Config) -> None:
    register_canvas_tools(mcp, client, config)
    register_drawing_tools(mcp, client, config)
    register_animation_tools(mcp, client, config)
    register_selection_tools(mcp, client, config)
    register_palette_tools(mcp, client, config)
    register_export_tools(mcp, client, config)
    register_inspection_tools(mcp, client, config)
    register_analysis_tools(mcp, client, config)
    register_dithering_tools(mcp, client, config)
    register_quantization_tools(mcp, client, config)
    register_auto_shading_tools(mcp, client, config)
    register_antialiasing_tools(mcp, client, config)
    register_transform_tools(mcp, client, config)
    register_batch_tools(mcp, client, config)
    register_pixelize_tools(mcp, client, config)
    register_plan_tools(mcp, client, config)

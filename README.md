# Aseprite MCP Server

A Python MCP (Model Context Protocol) server that exposes Aseprite's pixel art and animation capabilities to AI assistants, enabling you to create and edit sprites using natural language.

Fork of [willibrandon/pixel-mcp](https://github.com/willibrandon/pixel-mcp), rewritten from Go to Python.

## Features

- **40+ MCP Tools** for complete pixel art control
- **Canvas & Layer Management**: RGB, Grayscale, Indexed color modes
- **Drawing Primitives**: Pixels, lines, rectangles, circles, polylines, flood fill
- **Selection Tools**: Rectangle, ellipse, copy, cut, paste
- **Professional Pixel Art**: Dithering (16 patterns), auto shading, antialiasing
- **Palette Management**: Set/get/sort palettes, analyze color harmonies
- **Animation**: Frame durations, tags, duplication, linked cels
- **Transform**: Flip, rotate, scale, crop, resize, outline
- **Export**: PNG, GIF, spritesheet with JSON metadata
- **Cross-platform**: Zero compilation, runs via `uv run`

## Requirements

- Python 3.10+
- Aseprite 1.3.0+ (1.3.10+ recommended)

## Quick Start

### 1. Install

```bash
git clone https://github.com/youmucz/aseprite-mcp.git
cd aseprite-mcp
uv sync
```

### 2. Configure

Create `~/.config/aseprite-mcp/config.json`:

```json
{
  "aseprite_path": "/path/to/aseprite",
  "temp_dir": "/tmp/aseprite-mcp",
  "timeout": 30,
  "log_level": "info"
}
```

Or set environment variable: `ASEPRITE_PATH=/path/to/aseprite`

Or use project `setting.json` (for astara-opencode integration):
```json
{
  "external_tools": {
    "aseprite": { "executable": "/path/to/aseprite" }
  }
}
```

### 3. Run

```bash
uv run -m aseprite_mcp
```

## Usage with OpenCode

Add to `opencode.json`:

```json
{
  "mcp": {
    "aseprite-mcp": {
      "type": "local",
      "enabled": true,
      "command": ["uv", "--directory", ".opencode/mcps/aseprite-mcp", "run", "-m", "aseprite_mcp"]
    }
  }
}
```

## Available Tools

### Canvas & Layer Management (7)
| Tool | Description |
|------|-------------|
| `create_canvas` | Create new sprite |
| `add_layer` | Add layer |
| `delete_layer` | Delete layer |
| `add_frame` | Add animation frame |
| `delete_frame` | Delete animation frame |
| `flatten_layers` | Flatten all layers |
| `get_sprite_info` | Get sprite metadata |

### Drawing & Painting (6)
| Tool | Description |
|------|-------------|
| `draw_pixels` | Draw individual pixels (batch) |
| `draw_line` | Draw line |
| `draw_contour` | Draw polyline/polygon |
| `draw_rectangle` | Draw rectangle |
| `draw_circle` | Draw circle/ellipse |
| `fill_area` | Flood fill |

### Selection & Clipboard (8)
| Tool | Description |
|------|-------------|
| `select_rectangle` | Rectangular selection |
| `select_ellipse` | Elliptical selection |
| `select_all` | Select all |
| `deselect` | Clear selection |
| `move_selection` | Move selection bounds |
| `cut_selection` | Cut to clipboard |
| `copy_selection` | Copy to clipboard |
| `paste_clipboard` | Paste from clipboard |

### Palette Management (7)
| Tool | Description |
|------|-------------|
| `get_palette` | Get current palette |
| `set_palette` | Set entire palette |
| `set_palette_color` | Set specific palette index |
| `add_palette_color` | Add new color |
| `sort_palette` | Sort palette |
| `apply_shading` | Apply palette-constrained shading |
| `analyze_palette_harmonies` | Analyze color harmonies |

### Transform (6)
| Tool | Description |
|------|-------------|
| `flip_sprite` | Flip H/V |
| `rotate_sprite` | Rotate 90/180/270 |
| `scale_sprite` | Scale with algorithm |
| `crop_sprite` | Crop to region |
| `resize_canvas` | Resize canvas |
| `apply_outline` | Apply outline effect |

### Animation (5)
| Tool | Description |
|------|-------------|
| `set_frame_duration` | Set frame duration |
| `create_tag` | Create animation tag |
| `delete_tag` | Delete tag |
| `duplicate_frame` | Duplicate frame |
| `link_cel` | Link cel |

### Export & Import (4)
| Tool | Description |
|------|-------------|
| `export_sprite` | Export to PNG/GIF/JPG/BMP |
| `export_spritesheet` | Export spritesheet |
| `import_image` | Import image as layer |
| `save_as` | Save to .aseprite |

### Professional Tools (6)
| Tool | Description |
|------|-------------|
| `analyze_reference` | Analyze reference image |
| `draw_with_dither` | Dithering patterns (16) |
| `quantize_palette` | Color quantization |
| `downsample_image` | Downsample to pixel art |
| `apply_auto_shading` | Auto shading |
| `suggest_antialiasing` | Antialiasing suggestions |

## Integration with Godot

Works alongside `godot-aseprite-wizard` MCP for a complete AI-driven game art pipeline:

1. `aseprite-mcp`: Create & animate sprites via AI → .ase files
2. `godot-aseprite-wizard`: Import .ase into Godot nodes
3. `godot-mcp`: Godot editor control

## License

MIT

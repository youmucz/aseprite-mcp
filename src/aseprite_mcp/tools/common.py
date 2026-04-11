from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ColorMode(Enum):
    RGB = "rgb"
    GRAYSCALE = "grayscale"
    INDEXED = "indexed"

    def to_lua(self) -> str:
        return {
            "rgb": "ColorMode.RGB",
            "grayscale": "ColorMode.GRAYSCALE",
            "indexed": "ColorMode.INDEXED",
        }[self.value]


@dataclass
class Color:
    r: int
    g: int
    b: int
    a: int = 255

    def to_hex(self) -> str:
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}{self.a:02x}"

    @classmethod
    def from_hex(cls, hex_str: str) -> "Color":
        hex_str = hex_str.lstrip("#")
        if len(hex_str) == 6:
            r, g, b = int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16)
            return cls(r, g, b, 255)
        elif len(hex_str) == 8:
            r, g, b, a = int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16), int(hex_str[6:8], 16)
            return cls(r, g, b, a)
        raise ValueError(f"Invalid hex color: {hex_str}")


@dataclass
class Point:
    x: int
    y: int


@dataclass
class Rectangle:
    x: int
    y: int
    width: int
    height: int


@dataclass
class Pixel:
    x: int
    y: int
    color: Color


@dataclass
class SpriteInfo:
    width: int
    height: int
    color_mode: str
    frame_count: int
    layer_count: int
    layers: list[str] = field(default_factory=list)


def parse_json_output(output: str) -> dict:
    output = output.strip()
    if not output:
        return {}
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        return {"raw": output}


def format_tool_result(data: dict | str) -> str:
    if isinstance(data, str):
        return data
    return json.dumps(data, indent=2)

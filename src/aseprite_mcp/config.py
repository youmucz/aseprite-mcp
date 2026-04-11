import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class Config:
    aseprite_path: str = ""
    temp_dir: str = ""
    timeout: int = 30
    log_level: str = "info"
    log_file: str = ""
    enable_timing: bool = False

    def __post_init__(self):
        if not self.temp_dir:
            self.temp_dir = str(Path(os.environ.get("TMPDIR", "/tmp")) / "aseprite-mcp")
        Path(self.temp_dir).mkdir(parents=True, exist_ok=True)


class ConfigError(Exception):
    pass


def get_config_dir() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "aseprite-mcp"


def get_config_file_path() -> Path:
    return get_config_dir() / "config.json"


def read_config_json() -> dict:
    config_path = get_config_file_path()
    if config_path.exists():
        with open(config_path, "r") as f:
            return json.load(f)
    return {}


def write_config_json(aseprite_path: str) -> None:
    config_dir = get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = get_config_file_path()
    existing = read_config_json()
    existing["aseprite_path"] = aseprite_path
    if "temp_dir" not in existing:
        existing["temp_dir"] = str(
            Path(os.environ.get("TMPDIR", "/tmp")) / "aseprite-mcp"
        )
    if "timeout" not in existing:
        existing["timeout"] = 30
    if "log_level" not in existing:
        existing["log_level"] = "info"
    with open(config_path, "w") as f:
        json.dump(existing, f, indent=2)


def find_setting_json() -> Optional[Path]:
    cwd = Path.cwd()
    for parent in [cwd] + list(cwd.parents):
        candidate = parent / "setting.json"
        if candidate.exists():
            return candidate
    return None


def read_setting_json() -> dict:
    setting_path = find_setting_json()
    if setting_path is None:
        return {}
    with open(setting_path, "r") as f:
        return json.load(f)


def load_aseprite_path() -> str:
    path = os.environ.get("ASEPRITE_PATH", "").strip()
    if path:
        return path

    config_data = read_config_json()
    path = config_data.get("aseprite_path", "").strip()
    if path:
        return path

    setting_data = read_setting_json()
    path = (
        setting_data.get("external_tools", {})
        .get("aseprite", {})
        .get("executable", "")
        .strip()
    )
    if path:
        return path

    raise ConfigError(
        "Aseprite path not found. Configure via one of:\n"
        "  1. Environment variable: ASEPRITE_PATH=/path/to/aseprite\n"
        f"  2. Config file: {get_config_file_path()} (set 'aseprite_path')\n"
        "  3. Project setting.json: external_tools.aseprite.executable"
    )


def load() -> Config:
    aseprite_path = load_aseprite_path()
    if not Path(aseprite_path).exists():
        raise ConfigError(f"Aseprite executable not found at: {aseprite_path}")

    config_data = read_config_json()
    return Config(
        aseprite_path=aseprite_path,
        temp_dir=config_data.get("temp_dir", ""),
        timeout=config_data.get("timeout", 30),
        log_level=config_data.get("log_level", "info"),
        log_file=config_data.get("log_file", ""),
        enable_timing=config_data.get("enable_timing", False),
    )

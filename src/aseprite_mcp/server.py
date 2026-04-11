import argparse
import asyncio
import json
import logging
import sys
from typing import Optional

from mcp.server.fastmcp import FastMCP

from aseprite_mcp.config import Config, load, ConfigError
from aseprite_mcp.client import AsepriteClient

logger = logging.getLogger("aseprite-mcp")

mcp = FastMCP("aseprite-mcp")

config: Optional[Config] = None
client: Optional[AsepriteClient] = None


def setup_logging(cfg: Config) -> None:
    level = getattr(logging, cfg.log_level.upper(), logging.INFO)
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stderr)]
    if cfg.log_file:
        handlers.append(logging.FileHandler(cfg.log_file))
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=handlers,
    )


def init_server() -> None:
    global config, client
    try:
        config = load()
    except ConfigError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)

    setup_logging(config)
    client = AsepriteClient(
        exec_path=config.aseprite_path,
        temp_dir=config.temp_dir,
        timeout=config.timeout,
    )

    from aseprite_mcp.tools import register_all_tools

    register_all_tools(mcp, client, config)


async def main() -> None:
    parser = argparse.ArgumentParser(description="Aseprite MCP Server")
    parser.add_argument("--version", action="store_true", help="Show version")
    parser.add_argument("--health", action="store_true", help="Health check")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    if args.version:
        from aseprite_mcp import __version__

        print(f"aseprite-mcp version {__version__}")
        return

    init_server()

    if args.health:
        try:
            ver = await client.get_version()
            print(f"OK: Aseprite {ver}")
        except Exception as e:
            print(f"FAIL: {e}")
            sys.exit(1)
        return

    await mcp.run_stdio_async()

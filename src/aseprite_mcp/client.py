import asyncio
import os
import tempfile
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("aseprite-mcp")


class AsepriteClient:
    def __init__(self, exec_path: str, temp_dir: str, timeout: int = 30):
        self.exec_path = exec_path
        self.temp_dir = temp_dir
        self.timeout = timeout
        Path(self.temp_dir).mkdir(parents=True, exist_ok=True)

    async def execute_command(self, args: list[str]) -> str:
        cmd = [self.exec_path] + args
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=self.timeout
            )
        except asyncio.TimeoutError:
            proc.kill()
            raise RuntimeError(f"Aseprite command timed out after {self.timeout}s")

        stdout_str = stdout.decode("utf-8", errors="replace")
        stderr_str = stderr.decode("utf-8", errors="replace")

        if proc.returncode != 0:
            raise RuntimeError(
                f"Aseprite command failed (exit {proc.returncode}):\n"
                f"stderr: {stderr_str}\nstdout: {stdout_str}"
            )
        return stdout_str

    async def execute_lua(self, script: str, sprite_path: str = "") -> str:
        script_path = self._create_temp_script(script)
        try:
            args = ["--batch"]
            if sprite_path:
                if not Path(sprite_path).exists():
                    raise FileNotFoundError(f"Sprite file not found: {sprite_path}")
                args.append(sprite_path)
            args.extend(["--script", script_path])
            return await self.execute_command(args)
        finally:
            try:
                os.remove(script_path)
            except OSError:
                pass

    async def get_version(self) -> str:
        output = await self.execute_command(["--version"])
        lines = output.strip().split("\n")
        return lines[0].strip() if lines else ""

    def _create_temp_script(self, script: str) -> str:
        fd, path = tempfile.mkstemp(suffix=".lua", prefix="script-", dir=self.temp_dir)
        with os.fdopen(fd, "w") as f:
            f.write(script)
        os.chmod(path, 0o600)
        return path

    def cleanup_old_temp_files(self, max_age_seconds: int = 3600) -> None:
        import time
        temp = Path(self.temp_dir)
        if not temp.exists():
            return
        now = time.time()
        for entry in temp.iterdir():
            if (
                entry.is_file()
                and entry.name.startswith("script-")
                and entry.name.endswith(".lua")
                and now - entry.stat().st_mtime > max_age_seconds
            ):
                try:
                    entry.unlink()
                except OSError:
                    pass

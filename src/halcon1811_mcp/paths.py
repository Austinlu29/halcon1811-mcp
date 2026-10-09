"""Keep generated programs outside the installed Python package."""
import os
from pathlib import Path


def data_directory() -> Path:
    override = os.environ.get("HALCON_MCP_DATA_DIR")
    if override:
        return Path(override).expanduser().resolve()
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local")))
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share")))
    return base / "halcon1811-mcp"

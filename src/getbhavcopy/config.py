"""
config.py — single source of truth for GetBhavCopy configuration.

All read/write operations for the app config file live here.
No other module should directly read or write SaveDirPath.json.
"""

import json
import os
from pathlib import Path
from typing import Any


def get_config_path() -> Path:
    appdata = os.getenv("APPDATA")
    base = Path(appdata) / "GetBhavCopy" if appdata else Path.home() / ".getbhavcopy"
    base.mkdir(parents=True, exist_ok=True)
    return base / "SaveDirPath.json"


def load_config() -> Any:
    path = get_config_path()
    if not path.exists():
        default: dict = {
            "DirPath": str(Path.cwd()),
            "theme": "system",
            "format": "TXT",
            "last_start": "",
            "last_end": "",
            "schedule_enabled": False,
            "schedule_time": "16:00",
            "autostart_enabled": False,
            "max_workers": 8,
        }
        path.write_text(json.dumps(default, indent=2))
        return default
    return json.loads(path.read_text())


def save_config(cfg: dict) -> None:
    path = get_config_path()
    path.write_text(json.dumps(cfg, indent=2))


def is_newer(latest: str, current: str) -> bool:
    """Return True if latest version is newer than current."""
    try:
        latest_parts = [int(x) for x in latest.strip().split(".")]
        current_parts = [int(x) for x in current.strip().split(".")]
        return latest_parts > current_parts
    except Exception:
        return False

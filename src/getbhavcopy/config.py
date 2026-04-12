"""
config.py — single source of truth for GetBhavCopy configuration.

All read/write operations for the app config file live here.
No other module should directly read or write SaveDirPath.json.
"""

import json
import os
from datetime import datetime as _dt
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
            "schedule_time": "17:30",
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


def get_failed_dates_path() -> Path:
    appdata = os.getenv("APPDATA")
    base = Path(appdata) / "GetBhavCopy" if appdata else Path.home() / ".getbhavcopy"
    base.mkdir(parents=True, exist_ok=True)
    return base / "failed_dates.json"


def load_failed_dates() -> set:
    """
    Return dates that failed more than 2 days ago.
    Dates that failed recently are still retried — handles late NSE publish.
    """
    path = get_failed_dates_path()
    if not path.exists():
        return set()
    try:
        from datetime import timedelta

        data = json.loads(path.read_text())
        retry_cutoff = (_dt.today() - timedelta(days=2)).strftime("%Y-%m-%d")
        if isinstance(data, dict):
            return {
                date for date, failed_on in data.items() if failed_on <= retry_cutoff
            }
        if isinstance(data, list):
            return set(data)
    except Exception:
        pass
    return set()


def add_failed_date(date_str: str) -> None:
    """Cache a date that failed — stores when it first failed."""
    path = get_failed_dates_path()
    try:
        from datetime import timedelta

        existing: dict = {}
        if path.exists():
            raw = json.loads(path.read_text())
            if isinstance(raw, dict):
                existing = raw
            elif isinstance(raw, list):
                today_str = _dt.today().strftime("%Y-%m-%d")
                existing = {d: today_str for d in raw}
        if date_str not in existing:
            existing[date_str] = _dt.today().strftime("%Y-%m-%d")
        cutoff = (_dt.today() - timedelta(days=60)).strftime("%Y-%m-%d")
        existing = {k: v for k, v in existing.items() if v >= cutoff}
        path.write_text(json.dumps(existing, indent=2))
    except Exception:
        pass

"""
scheduler.py — OS-level scheduler registration for GetBhavCopy.

Handles registering and removing scheduled tasks on:
  - Windows: Task Scheduler (schtasks)
  - Mac: LaunchAgent plist
  - Linux: crontab

The headless download itself runs via:
  python -m getbhavcopy --headless
"""

import logging
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger("getbhavcopy")


def register_os_scheduler(enabled: bool, schedule_time: str) -> None:
    """Register or remove the OS-level scheduled task."""
    try:
        if sys.platform == "win32":
            _register_windows(enabled, schedule_time)
        elif sys.platform == "darwin":
            _register_mac(enabled, schedule_time)
        else:
            _register_linux(enabled, schedule_time)
    except Exception as e:
        logger.warning(f"Could not register OS scheduler: {e}")


def register_autostart(enabled: bool) -> None:
    """Register or remove app autostart on login."""
    try:
        if sys.platform == "win32":
            _autostart_windows(enabled)
        elif sys.platform == "darwin":
            _autostart_mac(enabled)
        else:
            logger.info("Autostart not supported on Linux — use cron or systemd")
    except Exception as e:
        logger.warning(f"Could not set autostart: {e}")


# ── Windows ──────────────────────────────────────────────────────────────────


def _register_windows(enabled: bool, schedule_time: str) -> None:
    task_name = "GetBhavCopyScheduler"

    if not enabled:
        subprocess.call(
            ["schtasks", "/delete", "/tn", task_name, "/f"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        logger.info("Windows scheduled task removed")
        return

    hour, minute = schedule_time.split(":")
    exe = sys.executable
    cmd = [
        "schtasks",
        "/create",
        "/f",
        "/tn",
        task_name,
        "/tr",
        f'"{exe}" -m getbhavcopy --headless',
        "/sc",
        "daily",
        "/st",
        f"{hour}:{minute}",
        "/mo",
        "1",
    ]
    subprocess.call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    logger.info(f"Windows scheduled task created for {schedule_time} daily")


def _autostart_windows(enabled: bool) -> None:
    try:
        import winreg as wr

        app_name = "GetBhavCopy"
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        exe_path = sys.executable

        with wr.OpenKey(  # type: ignore[attr-defined]
            wr.HKEY_CURRENT_USER,  # type: ignore[attr-defined]
            key_path,
            0,
            wr.KEY_SET_VALUE,  # type: ignore[attr-defined]
        ) as key:
            if enabled:
                wr.SetValueEx(  # type: ignore[attr-defined]
                    key,
                    app_name,
                    0,
                    wr.REG_SZ,  # type: ignore[attr-defined]
                    f'"{exe_path}" -m getbhavcopy',
                )
                logger.info("Windows autostart registered")
            else:
                try:
                    wr.DeleteValue(key, app_name)  # type: ignore[attr-defined]
                    logger.info("Windows autostart removed")
                except FileNotFoundError:
                    pass
    except Exception as e:
        logger.warning(f"Windows autostart failed: {e}")


# ── Mac ───────────────────────────────────────────────────────────────────────

_MAC_PLIST_SCHEDULER = (
    Path.home()
    / "Library"
    / "LaunchAgents"
    / "com.arickaji.getbhavcopy.scheduler.plist"
)

_MAC_PLIST_AUTOSTART = (
    Path.home() / "Library" / "LaunchAgents" / "com.arickaji.getbhavcopy.plist"
)


def _register_mac(enabled: bool, schedule_time: str) -> None:
    plist_path = _MAC_PLIST_SCHEDULER

    if not enabled:
        if plist_path.exists():
            subprocess.call(
                ["launchctl", "unload", str(plist_path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            plist_path.unlink()
        logger.info("Mac LaunchAgent scheduler removed")
        return

    hour, minute = schedule_time.split(":")
    exe = sys.executable
    log_path = Path.home() / ".getbhavcopy" / "scheduler.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.arickaji.getbhavcopy.scheduler</string>
  <key>ProgramArguments</key>
  <array>
    <string>{exe}</string>
    <string>-m</string>
    <string>getbhavcopy</string>
    <string>--headless</string>
  </array>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Hour</key>
    <integer>{int(hour)}</integer>
    <key>Minute</key>
    <integer>{int(minute)}</integer>
  </dict>
  <key>StandardOutPath</key>
  <string>{log_path}</string>
  <key>StandardErrorPath</key>
  <string>{log_path}</string>
</dict>
</plist>"""

    plist_path.parent.mkdir(parents=True, exist_ok=True)
    plist_path.write_text(plist)

    subprocess.call(
        ["launchctl", "load", str(plist_path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    logger.info(f"Mac LaunchAgent scheduler created for {schedule_time} daily")


def _autostart_mac(enabled: bool) -> None:
    plist_path = _MAC_PLIST_AUTOSTART

    if not enabled:
        if plist_path.exists():
            subprocess.call(
                ["launchctl", "unload", str(plist_path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            plist_path.unlink()
        logger.info("Mac autostart removed")
        return

    exe = sys.executable
    plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.arickaji.getbhavcopy</string>
  <key>ProgramArguments</key>
  <array>
    <string>{exe}</string>
    <string>-m</string>
    <string>getbhavcopy</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
</dict>
</plist>"""

    plist_path.parent.mkdir(parents=True, exist_ok=True)
    plist_path.write_text(plist)

    subprocess.call(
        ["launchctl", "load", str(plist_path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    logger.info("Mac autostart registered")


# ── Linux ─────────────────────────────────────────────────────────────────────


def _register_linux(enabled: bool, schedule_time: str) -> None:
    exe = sys.executable
    marker = "# GetBhavCopy scheduler"
    minute, hour = schedule_time.split(":")[1], schedule_time.split(":")[0]
    job = f"{minute} {hour} * * 1-5 {exe} -m getbhavcopy --headless {marker}"

    result = subprocess.run(
        ["crontab", "-l"],
        capture_output=True,
        text=True,
    )
    existing = result.stdout if result.returncode == 0 else ""
    lines = [
        line
        for line in existing.splitlines()
        if marker not in line and "getbhavcopy --headless" not in line
    ]

    if enabled:
        lines.append(job)

    new_crontab = "\n".join(lines) + "\n"
    proc = subprocess.Popen(["crontab", "-"], stdin=subprocess.PIPE)
    proc.communicate(new_crontab.encode())

    logger.info(f"Linux cron job {'created' if enabled else 'removed'}")

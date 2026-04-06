"""
notifications.py — cross-platform desktop notification support.

Sends native notifications on Mac, Windows and Linux.
All methods are silent on failure — notifications are best-effort only.
"""

import logging
import subprocess
import sys

logger = logging.getLogger("getbhavcopy")


def send_notification(title: str, message: str) -> None:
    """Send a native desktop notification. Silent on failure."""
    try:
        if sys.platform == "darwin":
            _notify_mac(title, message)
        elif sys.platform == "win32":
            _notify_windows(title, message)
        else:
            _notify_linux(title, message)
    except Exception as e:
        logger.debug(f"Notification failed: {e}")


def _notify_mac(title: str, message: str) -> None:
    script = f'display notification "{message}" with title "{title}"'
    subprocess.call(
        ["osascript", "-e", script],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _notify_windows(title: str, message: str) -> None:
    try:
        from win10toast import ToastNotifier

        ToastNotifier().show_toast(title, message, duration=5, threaded=True)
    except Exception:
        pass


def _notify_linux(title: str, message: str) -> None:
    subprocess.call(
        ["notify-send", title, message],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

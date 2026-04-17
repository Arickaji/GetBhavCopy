"""
notifications.py — cross-platform desktop notification support.

Sends native notifications on Mac, Windows and Linux.
All methods are silent on failure — notifications are best-effort only.

Windows priority order:
  1. winotify  — modern Windows 10/11 native API, no admin required
  2. win10toast — legacy fallback
  3. PowerShell — last resort, always works
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
    # Try winotify first — modern, no admin, works on Win10/11
    try:
        from winotify import Notification, audio

        toast = Notification(
            app_id="GetBhavCopy",
            title=title,
            msg=message,
            duration="short",
        )
        toast.set_audio(audio.Default, loop=False)
        toast.show()
        return
    except Exception:
        pass

    # Fallback 1 — win10toast legacy
    try:
        from win10toast import ToastNotifier

        ToastNotifier().show_toast(title, message, duration=5, threaded=True)
        return
    except Exception:
        pass

    # Fallback 2 — PowerShell, always works on any Windows
    # Fallback 2 — PowerShell, always works on any Windows
    try:
        ns = "Windows.UI.Notifications"
        mgr = f"[{ns}.ToastNotificationManager, {ns}, ContentType=WindowsRuntime]"
        tmpl = f"[{ns}.ToastTemplateType]::ToastText02"
        notif = f"[{ns}.ToastNotification]"
        t0 = "$x.GetElementsByTagName('text')[0]"
        t1 = "$x.GetElementsByTagName('text')[1]"
        ps_script = (
            f"{mgr} | Out-Null; "
            f"$t = {tmpl}; "
            f"$x = [{ns}.ToastNotificationManager]::GetTemplateContent($t); "
            f"{t0}.AppendChild($x.CreateTextNode('{title}')) | Out-Null; "
            f"{t1}.AppendChild($x.CreateTextNode('{message}')) | Out-Null; "
            f"$n = {notif}::new($x); "
            f"[{ns}.ToastNotificationManager]"
            f"::CreateToastNotifier('GetBhavCopy').Show($n)"
        )
        subprocess.call(
            ["powershell", "-WindowStyle", "Hidden", "-Command", ps_script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass


def _notify_linux(title: str, message: str) -> None:
    subprocess.call(
        ["notify-send", title, message],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

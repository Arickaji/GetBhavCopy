"""
__main__.py — entry point for GetBhavCopy.

Two modes:
  python -m getbhavcopy           — launches the GUI
  python -m getbhavcopy --headless — runs a silent background download
                                     (used by OS scheduler)
"""

import sys


def main() -> None:
    if "--headless" in sys.argv:
        _run_headless()
    else:
        from getbhavcopy.ui import App

        app = App()
        app.run()


def _run_headless() -> None:
    """
    Silent download mode — no UI, no tkinter.
    Downloads today's bhavcopy using saved config, then exits.
    Called automatically by OS scheduler at the configured time.
    """
    import logging
    from datetime import datetime
    from pathlib import Path

    from getbhavcopy.config import load_config
    from getbhavcopy.core import GetBhavCopy
    from getbhavcopy.logging_config import setup_logging
    from getbhavcopy.notifications import send_notification

    setup_logging(debug=False)
    logger = logging.getLogger("getbhavcopy")

    try:
        cfg = load_config()

        if not cfg.get("schedule_enabled", False):
            logger.info("Scheduler disabled — exiting headless mode")
            return

        save_dir = cfg.get("DirPath", str(Path.cwd()))
        fmt = cfg.get("format", "TXT")
        today = datetime.today().strftime("%Y-%m-%d")

        logger.info(f"Headless download starting for {today}")

        downloader = GetBhavCopy(
            today,
            today,
            save_dir,
            fmt,
        )
        downloader.get_bhavcopy()

        failed = len(getattr(downloader, "failed_dates", []))
        if failed:
            msg = f"Download complete for {today} — {failed} dates skipped"
        else:
            msg = f"Bhavcopy downloaded successfully for {today}"

        send_notification("GetBhavCopy", msg)
        logger.info(f"Headless download complete: {msg}")

    except Exception as e:
        logger.error(f"Headless download failed: {e}")
        send_notification("GetBhavCopy", f"Download failed: {e}")


if __name__ == "__main__":
    main()

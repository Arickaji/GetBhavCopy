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
    - Checks last 7 trading days for missing files
    - Includes today if market has closed (after 17:30 IST)
    - Skips known failed dates (holidays, NSE offline)
    - Caches newly failed dates to prevent infinite retry
    """
    import logging
    from datetime import datetime, timedelta
    from pathlib import Path
    from zoneinfo import ZoneInfo

    from getbhavcopy.config import (
        add_failed_date,
        load_config,
        load_failed_dates,
    )
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
        ext = "csv" if fmt == "CSV" else "txt"

        # Use IST timezone for market close check
        ist = ZoneInfo("Asia/Kolkata")
        now_ist = datetime.now(ist)
        today_ist = now_ist.date()

        # Market closes at 15:30 IST, data available ~17:30 IST
        market_data_available = now_ist.hour > 17 or (
            now_ist.hour == 17 and now_ist.minute >= 30
        )

        failed_cache = load_failed_dates()
        missing: list[str] = []

        for i in range(8):  # check last 7 days + today
            day = today_ist - timedelta(days=i)

            # Skip today if market data not yet available
            if i == 0 and not market_data_available:
                continue

            # Skip weekends
            if day.weekday() >= 5:
                continue

            date_str = day.strftime("%Y-%m-%d")

            # Skip known failures (holidays etc)
            if date_str in failed_cache:
                logger.debug(f"Skipping known failed date: {date_str}")
                continue

            filename = f"{date_str}-NSE-EQ.{ext}"
            if not (Path(save_dir) / filename).exists():
                missing.append(date_str)

        if not missing:
            logger.info("Headless check complete — all recent files present")
            return

        logger.info(
            f"Headless catch-up — {len(missing)} missing day(s): "
            f"{', '.join(sorted(missing))}"
        )

        missing_sorted = sorted(missing)
        start_date = missing_sorted[0]
        end_date = missing_sorted[-1]

        downloader = GetBhavCopy(start_date, end_date, save_dir, fmt)
        downloader.get_bhavcopy()

        # Cache failed dates — prevents retrying holidays every day
        for fd in getattr(downloader, "failed_dates", []):
            add_failed_date(fd)
            logger.info(f"Cached failed date: {fd} (holiday or NSE offline)")

        failed = len(getattr(downloader, "failed_dates", []))
        downloaded = len(missing) - failed

        if downloaded > 0 and failed == 0:
            msg = (
                f"Downloaded {downloaded} day(s) of bhavcopy data"
                if downloaded > 1
                else f"Bhavcopy downloaded successfully for {end_date}"
            )
        elif downloaded > 0 and failed > 0:
            msg = (
                f"Downloaded {downloaded} day(s) — "
                f"{failed} unavailable (holiday or NSE offline)"
            )
        else:
            msg = "Download failed — NSE may be unavailable"

        send_notification("GetBhavCopy", msg)
        logger.info(f"Headless catch-up complete: {msg}")

    except Exception as e:
        logger.error(f"Headless download failed: {e}")
        send_notification("GetBhavCopy", f"Download failed: {e}")


if __name__ == "__main__":
    main()

"""
holidays.py — NSE trading holiday calendar for GetBhavCopy.

Fetches the official NSE holiday list and caches it locally.
Refreshed monthly. Used to proactively skip holidays before
any download attempt.

NSE holiday API:
  https://www.nseindia.com/api/holiday-master?type=trading
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("getbhavcopy")

# NSE holiday API endpoint
_NSE_HOLIDAY_URL = "https://www.nseindia.com/api/holiday-master?type=trading"

# Cache refresh interval — 30 days
_REFRESH_DAYS = 30


def get_holidays_path() -> Path:
    """Path to the local holiday cache file."""
    appdata = os.getenv("APPDATA")
    base = Path(appdata) / "GetBhavCopy" if appdata else Path.home() / ".getbhavcopy"
    base.mkdir(parents=True, exist_ok=True)
    return base / "nse_holidays.json"


def _fetch_from_nse() -> list[str]:
    """
    Fetch trading holidays from NSE API.
    Returns list of date strings in YYYY-MM-DD format.
    Returns empty list on failure — caller falls back to failed dates cache.
    """
    try:
        import requests

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.nseindia.com",
            "Accept": "application/json",
        }

        # NSE requires a session cookie — get it first
        session = requests.Session()
        session.headers.update(headers)

        # Visit main page to get cookies
        session.get("https://www.nseindia.com", timeout=10)

        # Now fetch holiday list
        resp = session.get(_NSE_HOLIDAY_URL, timeout=10)

        if resp.status_code != 200:
            logger.debug(f"NSE holiday API returned {resp.status_code}")
            return []

        data = resp.json()

        holidays: list[str] = []

        # NSE returns CM (capital markets) holidays
        cm_holidays = data.get("CM", [])

        for entry in cm_holidays:
            # NSE date format is like "18-Apr-2026" or "18-APR-2026"
            raw_date = entry.get("tradingDate", "")
            if not raw_date:
                continue
            try:
                parsed = datetime.strptime(raw_date.strip(), "%d-%b-%Y")
                holidays.append(parsed.strftime("%Y-%m-%d"))
            except ValueError:
                try:
                    parsed = datetime.strptime(raw_date.strip(), "%d-%B-%Y")
                    holidays.append(parsed.strftime("%Y-%m-%d"))
                except ValueError:
                    logger.debug(f"Could not parse holiday date: {raw_date}")
                    continue

        logger.info(f"Fetched {len(holidays)} NSE trading holidays from API")
        return holidays

    except Exception as e:
        logger.debug(f"NSE holiday fetch failed: {e}")
        return []


def _load_cache() -> dict:
    """Load the local holiday cache."""
    path = get_holidays_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def _save_cache(holidays: list[str]) -> None:
    """Save holidays to local cache with refresh timestamp."""
    path = get_holidays_path()
    try:
        cache = {
            "fetched_on": datetime.today().strftime("%Y-%m-%d"),
            "holidays": sorted(holidays),
        }
        path.write_text(json.dumps(cache, indent=2))
    except Exception as e:
        logger.debug(f"Could not save holiday cache: {e}")


def _cache_is_fresh(cache: dict) -> bool:
    """Return True if cache was fetched within the last 30 days."""
    fetched_on = cache.get("fetched_on", "")
    if not fetched_on:
        return False
    try:
        fetched_date = datetime.strptime(fetched_on, "%Y-%m-%d")
        return (datetime.today() - fetched_date).days < _REFRESH_DAYS
    except ValueError:
        return False


def get_nse_holidays(force_refresh: bool = False) -> set[str]:
    """
    Return the set of NSE trading holidays as YYYY-MM-DD strings.

    Uses local cache if fresh (< 30 days old).
    Fetches from NSE API if cache is stale or missing.
    Returns empty set on failure — system falls back to failed dates cache.
    """
    cache = _load_cache()

    if not force_refresh and _cache_is_fresh(cache):
        holidays = cache.get("holidays", [])
        logger.debug(f"Using cached NSE holidays ({len(holidays)} dates)")
        return set(holidays)

    # Cache is stale or missing — fetch from NSE
    logger.info("Refreshing NSE holiday calendar...")
    fetched = _fetch_from_nse()

    if fetched:
        _save_cache(fetched)
        return set(fetched)

    # Fetch failed — use stale cache if available
    stale = cache.get("holidays", [])
    if stale:
        logger.warning(
            "NSE holiday fetch failed — using stale cache "
            f"({len(stale)} dates from {cache.get('fetched_on', 'unknown')})"
        )
        return set(stale)

    # No cache at all — return empty set, fallback to failed dates cache
    logger.warning(
        "NSE holiday calendar unavailable — "
        "holidays will be detected reactively via failed dates cache"
    )
    return set()


def is_nse_holiday(date_str: str) -> bool:
    """Return True if the given YYYY-MM-DD date is an NSE trading holiday."""
    holidays = get_nse_holidays()
    return date_str in holidays


def refresh_holidays_if_needed() -> None:
    """
    Silently refresh the holiday cache in the background if stale.
    Called on app startup — does nothing if cache is fresh.
    """
    cache = _load_cache()
    if not _cache_is_fresh(cache):
        import threading

        thread = threading.Thread(target=_background_refresh, daemon=True)
        thread.start()


def _background_refresh() -> None:
    """Fetch and cache holidays in a background thread."""
    try:
        fetched = _fetch_from_nse()
        if fetched:
            _save_cache(fetched)
            logger.info(
                f"Holiday calendar refreshed — {len(fetched)} trading holidays cached"
            )
    except Exception as e:
        logger.debug(f"Background holiday refresh failed: {e}")

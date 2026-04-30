"""
tests/test_getbhavcopy.py — full test suite for GetBhavCopy.

Covers:
  - core download engine
  - config read/write
  - scheduler registration
  - headless mode
  - symbol mapping
  - notifications
  - holiday calendar
  - failed dates cache
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from getbhavcopy.core import GetBhavCopy

# ── Helpers ───────────────────────────────────────────────────────────────────

EQUITY_CSV = (
    "SYMBOL,OPEN_PRICE,HIGH_PRICE,LOW_PRICE,CLOSE_PRICE,TTL_TRD_QNTY\n"
    "RELIANCE,100,110,90,105,1000\n"
    "INFY,1500,1550,1480,1520,500\n"
)

INDICES_CSV = (
    "INDEX NAME,INDEX DATE,OPEN INDEX VALUE,HIGH INDEX VALUE,"
    "LOW INDEX VALUE,CLOSING INDEX VALUE,VOLUME\n"
    "Nifty 50,13-02-2026,20000,20200,19800,20100,5000\n"
)


class FakeResp:
    def __init__(self, text: str, status_code: int = 200) -> None:
        self.text = text
        self.status_code = status_code


def fake_session_get(url: str, timeout: int = 15) -> FakeResp:
    if "sec_bhavdata_full" in url:
        return FakeResp(EQUITY_CSV)
    if "ind_close_all" in url:
        return FakeResp(INDICES_CSV)
    return FakeResp("", 404)


# ── Core — date validation ────────────────────────────────────────────────────


def test_start_date_after_end_date_raises() -> None:
    b = GetBhavCopy("2026-02-10", "2026-02-01", "DATA", "TXT", None, None)
    with pytest.raises(ValueError):
        b.get_bhavcopy()


def test_same_start_end_date_valid(tmp_path: Path) -> None:
    with patch(
        "getbhavcopy.core.requests.Session.get",
        side_effect=fake_session_get,
    ):
        b = GetBhavCopy("2026-02-13", "2026-02-13", str(tmp_path), "TXT", None, None)
        b.get_bhavcopy()
        assert b.failed_dates == []


# ── Core — file creation ──────────────────────────────────────────────────────


@patch("getbhavcopy.core.requests.Session.get", side_effect=fake_session_get)
@patch(
    "getbhavcopy.core.load_config",
    return_value={
        "split_eq_idx": True,
        "filename_pattern": "",
        "idx_filename_pattern": "",
    },
)
def test_split_creates_two_files(
    _cfg: MagicMock, _mock: MagicMock, tmp_path: Path
) -> None:
    b = GetBhavCopy("2026-02-13", "2026-02-13", str(tmp_path), "TXT", None, None)
    b.get_bhavcopy()
    files = list(tmp_path.glob("*.txt"))
    assert len(files) == 2
    names = {f.name for f in files}
    assert "2026-02-13-NSE-EQ.txt" in names
    assert "2026-02-13-NSE-IDX.txt" in names


@patch("getbhavcopy.core.requests.Session.get", side_effect=fake_session_get)
@patch(
    "getbhavcopy.core.load_config",
    return_value={
        "split_eq_idx": False,
        "filename_pattern": "",
        "idx_filename_pattern": "",
    },
)
def test_txt_file_created_on_success(
    _cfg: MagicMock, _mock: MagicMock, tmp_path: Path
) -> None:
    b = GetBhavCopy("2026-02-13", "2026-02-13", str(tmp_path), "TXT", None, None)
    b.get_bhavcopy()
    files = list(tmp_path.glob("*.txt"))
    assert len(files) == 1
    assert "2026-02-13" in files[0].name


@patch("getbhavcopy.core.requests.Session.get", side_effect=fake_session_get)
@patch(
    "getbhavcopy.core.load_config",
    return_value={
        "split_eq_idx": False,
        "filename_pattern": "",
        "idx_filename_pattern": "",
    },
)
def test_csv_file_created_on_success(
    _cfg: MagicMock, _mock: MagicMock, tmp_path: Path
) -> None:
    b = GetBhavCopy("2026-02-13", "2026-02-13", str(tmp_path), "CSV", None, None)
    b.get_bhavcopy()
    files = list(tmp_path.glob("*.csv"))
    assert len(files) == 1


@patch("getbhavcopy.core.requests.Session.get", side_effect=fake_session_get)
def test_file_content_has_correct_columns(_mock: MagicMock, tmp_path: Path) -> None:
    b = GetBhavCopy("2026-02-13", "2026-02-13", str(tmp_path), "TXT", None, None)
    b.get_bhavcopy()
    files = list(tmp_path.glob("*.txt"))
    content = files[0].read_text()
    first_line = content.strip().splitlines()[0]
    parts = first_line.split(",")
    assert len(parts) == 7


# ── Core — skip existing ──────────────────────────────────────────────────────


@patch("getbhavcopy.core.requests.Session.get", side_effect=fake_session_get)
@patch(
    "getbhavcopy.core.load_config",
    return_value={
        "split_eq_idx": False,
        "filename_pattern": "",
        "idx_filename_pattern": "",
    },
)
def test_existing_file_is_skipped(
    _cfg: MagicMock, _mock: MagicMock, tmp_path: Path
) -> None:
    existing = tmp_path / "2026-02-13-NSE-EQ.txt"
    existing.write_text("already exists")
    b = GetBhavCopy("2026-02-13", "2026-02-13", str(tmp_path), "TXT", None, None)
    b.get_bhavcopy()
    assert existing.read_text() == "already exists"


# ── Core — failed dates ───────────────────────────────────────────────────────


@patch("getbhavcopy.core.requests.Session.get", return_value=FakeResp("", 404))
def test_404_recorded_in_failed_dates(_mock: MagicMock, tmp_path: Path) -> None:
    b = GetBhavCopy("2026-02-13", "2026-02-13", str(tmp_path), "TXT", None, None)
    b.get_bhavcopy()
    assert "2026-02-13" in b.failed_dates


@patch("getbhavcopy.core.requests.Session.get", return_value=FakeResp("", 404))
def test_404_does_not_create_file(_mock: MagicMock, tmp_path: Path) -> None:
    b = GetBhavCopy("2026-02-13", "2026-02-13", str(tmp_path), "TXT", None, None)
    b.get_bhavcopy()
    assert list(tmp_path.glob("*.txt")) == []


# ── Core — weekends skipped ───────────────────────────────────────────────────


@patch("getbhavcopy.core.requests.Session.get", side_effect=fake_session_get)
def test_weekend_dates_skipped(_mock: MagicMock, tmp_path: Path) -> None:
    b = GetBhavCopy("2026-02-14", "2026-02-15", str(tmp_path), "TXT", None, None)
    b.get_bhavcopy()
    assert list(tmp_path.glob("*.txt")) == []


# ── Core — symbol mapping ─────────────────────────────────────────────────────


@patch("getbhavcopy.core.requests.Session.get", side_effect=fake_session_get)
@patch(
    "getbhavcopy.core.load_config",
    return_value={
        "split_eq_idx": False,
        "filename_pattern": "",
        "idx_filename_pattern": "",
    },
)
def test_symbol_mapping_applied(
    _cfg: MagicMock, _mock: MagicMock, tmp_path: Path
) -> None:
    b = GetBhavCopy("2026-02-13", "2026-02-13", str(tmp_path), "TXT", None, None)
    b._symbol_mapping = {"RELIANCE": "REL"}
    b.get_bhavcopy()
    files = list(tmp_path.glob("*.txt"))
    content = files[0].read_text()
    assert "REL," in content
    assert "RELIANCE," not in content


# ── Config ────────────────────────────────────────────────────────────────────


def test_load_config_creates_default(tmp_path: Path) -> None:
    from getbhavcopy import config as cfg_module

    fake_path = tmp_path / "SaveDirPath.json"
    with patch.object(cfg_module, "get_config_path", return_value=fake_path):
        result = cfg_module.load_config()
    assert "DirPath" in result
    assert "theme" in result
    assert "format" in result
    assert "schedule_enabled" in result
    assert fake_path.exists()


def test_save_and_reload_config(tmp_path: Path) -> None:
    from getbhavcopy import config as cfg_module

    fake_path = tmp_path / "SaveDirPath.json"
    with patch.object(cfg_module, "get_config_path", return_value=fake_path):
        cfg_module.save_config({"theme": "dark", "format": "CSV"})
        result = cfg_module.load_config()
    assert result["theme"] == "dark"
    assert result["format"] == "CSV"


def test_config_path_uses_appdata_on_windows(tmp_path: Path) -> None:
    from getbhavcopy import config as cfg_module

    with patch.dict("os.environ", {"APPDATA": str(tmp_path)}):
        with patch("sys.platform", "win32"):
            path = cfg_module.get_config_path()
    assert "GetBhavCopy" in str(path)


def test_config_path_uses_home_on_mac(tmp_path: Path) -> None:
    from getbhavcopy import config as cfg_module

    with patch.dict("os.environ", {}, clear=True):
        with patch("pathlib.Path.home", return_value=tmp_path):
            path = cfg_module.get_config_path()
    assert ".getbhavcopy" in str(path)


# ── Symbol mapping ────────────────────────────────────────────────────────────


def test_load_symbol_mapping_empty(tmp_path: Path) -> None:
    from getbhavcopy import settings_windows as sw

    with patch.object(sw, "get_mapping_path", return_value=tmp_path / "x.json"):
        result = sw.load_symbol_mapping()
    assert result == {}


def test_save_and_load_symbol_mapping(tmp_path: Path) -> None:
    from getbhavcopy import settings_windows as sw

    fake_path = tmp_path / "symbol_mapping.json"
    with patch.object(sw, "get_mapping_path", return_value=fake_path):
        sw.save_symbol_mapping({"NIFTY 50": "NIFTY50", "reliance": "REL"})
        result = sw.load_symbol_mapping()

    assert result["NIFTY 50"] == "NIFTY50"
    assert result["RELIANCE"] == "REL"


def test_symbol_mapping_ignores_empty_values(tmp_path: Path) -> None:
    from getbhavcopy import settings_windows as sw

    fake_path = tmp_path / "symbol_mapping.json"
    fake_path.write_text(json.dumps({"NIFTY 50": "NIFTY50", "": "empty", "INFY": ""}))
    with patch.object(sw, "get_mapping_path", return_value=fake_path):
        result = sw.load_symbol_mapping()
    assert "" not in result
    assert "INFY" not in result


# ── Scheduler ─────────────────────────────────────────────────────────────────


def test_register_os_scheduler_mac_creates_plist(tmp_path: Path) -> None:
    from getbhavcopy import scheduler

    plist_path = tmp_path / "test.plist"
    with patch.object(scheduler, "_MAC_PLIST_SCHEDULER", plist_path):
        with patch("subprocess.call"):
            scheduler._register_mac(True, "16:00")
    assert plist_path.exists()
    content = plist_path.read_text()
    assert "<integer>16</integer>" in content
    assert "<integer>0</integer>" in content
    assert "--headless" in content


def test_register_os_scheduler_mac_removes_plist(tmp_path: Path) -> None:
    from getbhavcopy import scheduler

    plist_path = tmp_path / "test.plist"
    plist_path.write_text("dummy")
    with patch.object(scheduler, "_MAC_PLIST_SCHEDULER", plist_path):
        with patch("subprocess.call"):
            scheduler._register_mac(False, "16:00")
    assert not plist_path.exists()


def test_register_linux_cron_enabled(tmp_path: Path) -> None:
    from getbhavcopy import scheduler

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="")
        with patch("subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_popen.return_value = mock_proc
            scheduler._register_linux(True, "16:00")
            written = mock_proc.communicate.call_args[0][0].decode()
            assert "getbhavcopy --headless" in written
            assert "16" in written


def test_register_linux_cron_disabled(tmp_path: Path) -> None:
    from getbhavcopy import scheduler

    existing = "0 16 * * 1-5 python -m getbhavcopy --headless # GetBhavCopy scheduler\n"
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout=existing)
        with patch("subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_popen.return_value = mock_proc
            scheduler._register_linux(False, "16:00")
            written = mock_proc.communicate.call_args[0][0].decode()
            assert "getbhavcopy --headless" not in written


# ── Notifications ─────────────────────────────────────────────────────────────


def test_send_notification_mac_calls_osascript() -> None:
    from getbhavcopy import notifications

    with patch("subprocess.call") as mock_call:
        with patch("sys.platform", "darwin"):
            notifications._notify_mac("Title", "Message")
        mock_call.assert_called_once()
        args = mock_call.call_args[0][0]
        assert "osascript" in args
        assert "Message" in args[2]


def test_send_notification_linux_calls_notify_send() -> None:
    from getbhavcopy import notifications

    with patch("subprocess.call") as mock_call:
        notifications._notify_linux("Title", "Message")
        mock_call.assert_called_once()
        args = mock_call.call_args[0][0]
        assert "notify-send" in args


def test_send_notification_silent_on_failure() -> None:
    from getbhavcopy import notifications

    with patch("subprocess.call", side_effect=Exception("no subprocess")):
        notifications.send_notification("Title", "Message")


# ── Headless mode ─────────────────────────────────────────────────────────────


def test_headless_exits_when_scheduler_disabled(tmp_path: Path) -> None:
    from getbhavcopy import __main__ as main_module

    with patch(
        "getbhavcopy.config.load_config",
        return_value={"schedule_enabled": False},
    ):
        main_module._run_headless()


def test_headless_downloads_when_enabled(tmp_path: Path) -> None:
    from getbhavcopy import __main__ as main_module

    cfg = {
        "schedule_enabled": True,
        "DirPath": str(tmp_path),
        "format": "TXT",
    }
    with patch("getbhavcopy.config.load_config", return_value=cfg):
        with patch("getbhavcopy.config.load_failed_dates", return_value=set()):
            with patch("getbhavcopy.holidays.get_nse_holidays", return_value=set()):
                with patch("getbhavcopy.core.GetBhavCopy") as mock_downloader:
                    mock_instance = MagicMock()
                    mock_instance.failed_dates = []
                    mock_downloader.return_value = mock_instance
                    with patch("getbhavcopy.notifications.send_notification"):
                        main_module._run_headless()
                    mock_instance.get_bhavcopy.assert_called_once()


def test_headless_skips_when_all_files_present(tmp_path: Path) -> None:
    from datetime import datetime, timedelta

    from getbhavcopy import __main__ as main_module

    today = datetime.today()
    for i in range(8):
        day = today - timedelta(days=i)
        if day.weekday() >= 5:
            continue
        (tmp_path / f"{day.strftime('%Y-%m-%d')}-NSE-EQ.txt").write_text("x")

    cfg = {
        "schedule_enabled": True,
        "DirPath": str(tmp_path),
        "format": "TXT",
    }
    with patch("getbhavcopy.config.load_config", return_value=cfg):
        with patch("getbhavcopy.config.load_failed_dates", return_value=set()):
            with patch("getbhavcopy.holidays.get_nse_holidays", return_value=set()):
                with patch("getbhavcopy.core.GetBhavCopy") as mock_dl:
                    with patch("getbhavcopy.notifications.send_notification"):
                        main_module._run_headless()
                    mock_dl.assert_not_called()


def test_headless_skips_known_failed_dates(tmp_path: Path) -> None:
    from datetime import datetime, timedelta

    from getbhavcopy import __main__ as main_module
    from getbhavcopy import config as cfg_module

    cfg = {
        "schedule_enabled": True,
        "DirPath": str(tmp_path),
        "format": "TXT",
    }
    failed: set[str] = set()
    today = datetime.today()
    for i in range(8):
        day = today - timedelta(days=i)
        if day.weekday() < 5:
            failed.add(day.strftime("%Y-%m-%d"))

    with patch("getbhavcopy.config.load_config", return_value=cfg):
        with patch.object(cfg_module, "load_failed_dates", return_value=failed):
            with patch("getbhavcopy.holidays.get_nse_holidays", return_value=set()):
                with patch("getbhavcopy.core.GetBhavCopy") as mock_dl:
                    with patch("getbhavcopy.notifications.send_notification"):
                        main_module._run_headless()
                    mock_dl.assert_not_called()


def test_headless_skips_nse_holidays(tmp_path: Path) -> None:
    from datetime import datetime, timedelta

    from getbhavcopy import __main__ as main_module

    cfg = {
        "schedule_enabled": True,
        "DirPath": str(tmp_path),
        "format": "TXT",
    }
    holidays: set[str] = set()
    today = datetime.today()
    for i in range(8):
        day = today - timedelta(days=i)
        if day.weekday() < 5:
            holidays.add(day.strftime("%Y-%m-%d"))

    with patch("getbhavcopy.config.load_config", return_value=cfg):
        with patch("getbhavcopy.config.load_failed_dates", return_value=set()):
            with patch("getbhavcopy.holidays.get_nse_holidays", return_value=holidays):
                with patch("getbhavcopy.core.GetBhavCopy") as mock_dl:
                    with patch("getbhavcopy.notifications.send_notification"):
                        main_module._run_headless()
                    mock_dl.assert_not_called()


# ── is_newer version check ────────────────────────────────────────────────────


def test_is_newer_returns_true_for_newer_version() -> None:
    from getbhavcopy.config import is_newer as _is_newer

    assert _is_newer("1.0.10", "1.0.9") is True
    assert _is_newer("2.0.0", "1.9.9") is True
    assert _is_newer("1.0.9.1", "1.0.9") is True


def test_is_newer_returns_false_for_same_version() -> None:
    from getbhavcopy.config import is_newer as _is_newer

    assert _is_newer("1.0.9", "1.0.9") is False


def test_is_newer_returns_false_for_older_version() -> None:
    from getbhavcopy.config import is_newer as _is_newer

    assert _is_newer("1.0.8", "1.0.9") is False
    assert _is_newer("1.0.9", "1.0.9.1") is False


def test_is_newer_handles_bad_input() -> None:
    from getbhavcopy.config import is_newer as _is_newer

    assert _is_newer("", "1.0.9") is False
    assert _is_newer("not-a-version", "1.0.9") is False


# ── Failed dates cache ────────────────────────────────────────────────────────


def test_failed_dates_cache_empty_when_no_file(tmp_path: Path) -> None:
    from getbhavcopy import config as cfg_module

    fake_path = tmp_path / "failed_dates.json"
    with patch.object(cfg_module, "get_failed_dates_path", return_value=fake_path):
        result = cfg_module.load_failed_dates()
    assert result == set()


def test_failed_dates_older_than_2_days_are_returned(tmp_path: Path) -> None:
    from datetime import datetime, timedelta

    from getbhavcopy import config as cfg_module

    fake_path = tmp_path / "failed_dates.json"
    old_date = (datetime.today() - timedelta(days=3)).strftime("%Y-%m-%d")
    failed_on = old_date
    fake_path.write_text(json.dumps({old_date: failed_on}))

    with patch.object(cfg_module, "get_failed_dates_path", return_value=fake_path):
        result = cfg_module.load_failed_dates()
    assert old_date in result


def test_recent_failed_dates_not_returned(tmp_path: Path) -> None:
    from datetime import datetime

    from getbhavcopy import config as cfg_module

    fake_path = tmp_path / "failed_dates.json"
    today = datetime.today().strftime("%Y-%m-%d")
    fake_path.write_text(json.dumps({today: today}))

    with patch.object(cfg_module, "get_failed_dates_path", return_value=fake_path):
        result = cfg_module.load_failed_dates()
    # Today's failure is within 2-day retry window — should NOT be returned
    assert today not in result


# ── Holiday calendar ──────────────────────────────────────────────────────────


def test_get_nse_holidays_returns_empty_on_fetch_failure(tmp_path: Path) -> None:
    from getbhavcopy import holidays as hol

    fake_path = tmp_path / "nse_holidays.json"

    with patch.object(hol, "get_holidays_path", return_value=fake_path):
        with patch.object(hol, "_fetch_from_nse", return_value=[]):
            result = hol.get_nse_holidays()

    assert result == set()


def test_is_nse_holiday_returns_true_for_holiday() -> None:
    from getbhavcopy import holidays as hol

    with patch.object(hol, "get_nse_holidays", return_value={"2026-04-03"}):
        assert hol.is_nse_holiday("2026-04-03") is True


def test_is_nse_holiday_returns_false_for_trading_day() -> None:
    from getbhavcopy import holidays as hol

    with patch.object(hol, "get_nse_holidays", return_value={"2026-04-03"}):
        assert hol.is_nse_holiday("2026-04-07") is False


def test_holiday_cache_saved_on_successful_fetch(tmp_path: Path) -> None:
    from getbhavcopy import holidays as hol

    fake_path = tmp_path / "nse_holidays.json"
    holidays_list = ["2026-04-03", "2026-04-14"]

    with patch.object(hol, "get_holidays_path", return_value=fake_path):
        with patch.object(hol, "_fetch_from_nse", return_value=holidays_list):
            result = hol.get_nse_holidays(force_refresh=True)

    assert "2026-04-03" in result
    assert "2026-04-14" in result
    assert fake_path.exists()
    cached = json.loads(fake_path.read_text())
    assert "2026-04-03" in cached["holidays"]

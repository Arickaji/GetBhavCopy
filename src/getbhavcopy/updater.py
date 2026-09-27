"""
updater.py — one-click auto update for GetBhavCopy.

Update scripts live in getbhavcopy/scripts/:
  mac_update.sh       — replaces .app bundle and restarts (Mac)
  windows_update.bat  — replaces .exe and restarts (Windows)

Flow:
  1. Find the correct download asset for this platform
  2. Download it to a temp dir with progress reporting
  3. Extract (Mac) or place (Windows) in temp dir
  4. Read the script template from scripts/
  5. Fill runtime placeholders (paths, PID)
  6. Write filled script to temp dir
  7. Launch script fully detached
  8. Exit current process — script takes over
"""

import logging
import os
import platform
import subprocess
import sys
import tempfile
from pathlib import Path

import requests

logger = logging.getLogger("getbhavcopy")

GITHUB_RELEASES_URL = (
    "https://api.github.com/repos/AricKaji/GetBhavCopy/releases/latest"
)
RELEASES_PAGE = "https://github.com/AricKaji/GetBhavCopy/releases/latest"

# Scripts folder — sits next to this file inside the package
_SCRIPTS_DIR = Path(__file__).parent / "scripts"


# ── Internal helpers ──────────────────────────────────────────────────────────


def _read_script(name: str) -> str:
    """Read a script template from scripts/. Raises if missing."""
    path = _SCRIPTS_DIR / name
    if not path.exists():
        raise FileNotFoundError(
            f"Update script not found: {path}\nExpected it at: {_SCRIPTS_DIR}"
        )
    return path.read_text(encoding="utf-8")


def _fill(template: str, **kwargs: str) -> str:
    """Replace {{KEY}} placeholders in template with values."""
    result = template
    for key, value in kwargs.items():
        result = result.replace(f"{{{{{key}}}}}", value)
    return result


def _download_with_progress(
    url: str,
    dest: Path,
    progress_callback: object = None,
) -> None:
    """
    Download url → dest.
    Calls progress_callback(pct: int) every 5% if provided.
    """
    import certifi

    session = requests.Session()
    session.verify = certifi.where()

    with session.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        downloaded = 0
        last_reported = -1

        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=65536):
                if not chunk:
                    continue
                f.write(chunk)
                downloaded += len(chunk)
                if total:
                    pct = int(downloaded / total * 100)
                    if pct >= last_reported + 5:
                        last_reported = pct
                        logger.info(f"Downloading update... {pct}%")
                        if callable(progress_callback):
                            progress_callback(pct)


def _find_app_bundle() -> Path | None:
    """
    Walk up from sys.executable to find the enclosing .app bundle.
    Returns None when running from source (no .app in path).

    Example (bundled):
      sys.executable = /Applications/GetBhavCopy.app/Contents/MacOS/GetBhavCopy
      → returns Path('/Applications/GetBhavCopy.app')

    Example (source):
      sys.executable = /Users/aric/miniconda3/envs/.../python
      → returns None
    """
    current = Path(sys.executable).resolve()
    for candidate in [current, *current.parents]:
        if candidate.suffix == ".app":
            return candidate
    return None


# ── Public API ────────────────────────────────────────────────────────────────


def get_latest_release() -> dict:
    """Fetch latest release metadata from GitHub API."""
    try:
        import certifi

        r = requests.get(
            GITHUB_RELEASES_URL,
            timeout=10,
            verify=certifi.where(),
        )
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        logger.debug(f"Update check failed: {e}")
    return {}


def get_download_url(release: dict) -> str | None:
    system = platform.system().lower()
    for asset in release.get("assets", []):
        name = asset.get("name", "").lower()
        url = asset.get("browser_download_url", "")
        if not url:
            continue
        if (
            system == "windows"
            and ("win" in name or "windows" in name)
            and name not in ("source code (zip)", "source code (tar.gz)")
        ):
            return url
        if system == "darwin" and ("mac" in name or "macos" in name):
            return url
    return None


def apply_update_mac(
    download_url: str,
    new_version: str,
    progress_callback: object = None,
) -> None:
    """
    Mac update — opens GitHub releases page.
    Full auto-update for Mac planned for a future release.
    """
    logger.info(
        f"Mac auto-update coming soon — opening releases page for v{new_version}"
    )
    open_releases_page()


def apply_update_windows(
    download_url: str,
    new_version: str,
    progress_callback: object = None,
) -> None:
    """
    Windows update:
      1. Download new exe to temp dir with progress
      2. Fill windows_update.bat template
      3. Write bat to temp dir
      4. Launch bat via cmd.exe (hidden window)
      5. sys.exit — bat waits for PID then replaces exe and relaunches
    """
    current_exe = Path(sys.executable)
    logger.info(f"Current exe: {current_exe}")
    tmp_dir = Path(tempfile.mkdtemp(prefix="getbhavcopy_update_"))
    zip_path = tmp_dir / "GetBhavCopy-windows.zip"
    new_exe = tmp_dir / "GetBhavCopy_new.exe"

    logger.info(f"Downloading GetBhavCopy v{new_version}...")
    _download_with_progress(download_url, zip_path, progress_callback)
    logger.info("Download complete — extracting...")

    # Extract exe from zip
    import zipfile

    with zipfile.ZipFile(zip_path, "r") as z:
        # Find the .exe inside the zip
        exe_names = [n for n in z.namelist() if n.lower().endswith(".exe")]
        if not exe_names:
            logger.error("No .exe found inside downloaded zip")
            open_releases_page()
            return
        z.extract(exe_names[0], tmp_dir)
        extracted_exe = tmp_dir / exe_names[0]
        extracted_exe.rename(new_exe)
    zip_path.unlink(missing_ok=True)
    logger.info(f"Extracted: {new_exe}")

    template = _read_script("windows_update.bat")
    script = _fill(
        template,
        NEW_EXE=str(new_exe),
        CURRENT_EXE=str(current_exe),
        PID=str(os.getpid()),
        TMP_DIR=str(tmp_dir),
    )

    bat_path = tmp_dir / "update.bat"
    bat_path.write_text(script, encoding="utf-8")

    logger.info("Launching update script...")

    subprocess.Popen(
        ["cmd.exe", "/c", str(bat_path)],
        creationflags=subprocess.CREATE_NO_WINDOW,  # type: ignore[attr-defined]
        close_fds=True,
    )

    logger.info("Closing GetBhavCopy — new version will open automatically...")
    sys.exit(0)


def open_releases_page() -> None:
    """Fallback — open GitHub releases page in the default browser."""
    import webbrowser

    webbrowser.open(RELEASES_PAGE)

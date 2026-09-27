# =============================================================================
# GetBhavCopy.spec — PyInstaller build spec
#
# Usage:
#   Mac:     pyinstaller GetBhavCopy.spec
#   Windows: pyinstaller GetBhavCopy.spec
#
# Output:
#   Mac:     dist/GetBhavCopy.app
#   Windows: dist/GetBhavCopy.exe
#
# Notes:
#   - scripts/ folder is bundled so updater.py can find mac_update.sh
#     and windows_update.bat at runtime via Path(__file__).parent / "scripts"
#   - certifi CA bundle is bundled explicitly so SSL works on all systems
#   - customtkinter assets (themes, fonts) are bundled explicitly
# =============================================================================

import sys
from pathlib import Path
import certifi
import customtkinter

# ── Paths ─────────────────────────────────────────────────────────────────────
SRC = Path("src/getbhavcopy")
SCRIPTS = SRC / "scripts"
CTK_PATH = Path(customtkinter.__file__).parent
CERTIFI_CA = Path(certifi.where())

# ── Data files to bundle ──────────────────────────────────────────────────────
datas = [
    # Update scripts — required by updater.py at runtime
    (str(SCRIPTS / "mac_update.sh"),      "getbhavcopy/scripts"),
    (str(SCRIPTS / "windows_update.bat"), "getbhavcopy/scripts"),

    # customtkinter UI assets (themes, fonts, images)
    (str(CTK_PATH), "customtkinter"),

    # certifi CA bundle — ensures SSL works without system cert store
    (str(CERTIFI_CA), "certifi"),
]

# ── Hidden imports ────────────────────────────────────────────────────────────
# Packages that PyInstaller misses because they are imported dynamically
hiddenimports = [
    # numpy — pandas depends on this, PyInstaller misses it
    "numpy",
    "numpy.core",
    "numpy.core._multiarray_umath",
    "numpy.core._multiarray_tests",
    "numpy.core.multiarray",
    "numpy.core.numeric",
    "numpy.core.umath",
    "numpy.lib",
    "numpy.lib.stride_tricks",
    "numpy.linalg",
    "numpy.fft",
    "numpy.random",
    "numpy.random._common",
    "numpy.random._bounded_integers",
    "numpy.random._generator",
    "numpy.random._mt19937",
    "numpy.random._pcg64",
    "numpy.random.mtrand",

    # pandas
    "pandas",
    "pandas._libs",
    "pandas._libs.tslibs",
    "pandas._libs.tslibs.base",
    "pandas._libs.tslibs.nattype",
    "pandas._libs.tslibs.np_datetime",
    "pandas._libs.tslibs.timedeltas",
    "pandas._libs.tslibs.timestamps",
    "pandas._libs.tslibs.timezones",
    "pandas._libs.tslibs.parsing",
    "pandas._libs.tslibs.offsets",
    "pandas._libs.tslibs.strptime",
    "pandas._libs.tslibs.period",
    "pandas._libs.tslibs.dtypes",
    "pandas._libs.tslibs.vectorized",
    "pandas._libs.hashtable",
    "pandas._libs.index",
    "pandas._libs.lib",
    "pandas._libs.missing",
    "pandas._libs.internals",
    "pandas._libs.join",
    "pandas._libs.interval",
    "pandas._libs.reduction",
    "pandas._libs.testing",
    "pandas._libs.writers",
    "pandas._libs.sparse",
    "pandas._libs.ops",
    "pandas._libs.parsers",
    "pandas.core.arrays.masked",
    "pandas.core.arrays.numeric",
    "pandas.io.formats.style",

    # UI and app
    "customtkinter",
    "darkdetect",
    "PIL",
    "PIL._tkinter_finder",
    "PIL.Image",
    "PIL.ImageTk",

    # network
    "requests",
    "certifi",
    "urllib3",
    "charset_normalizer",
    "idna",

    # stdlib
    "zoneinfo",
    "zoneinfo.tzdata",
    "tkinter",
    "tkinter.ttk",
    "tkinter.filedialog",
    "tkinter.messagebox",

    # getbhavcopy modules
    "getbhavcopy",
    "getbhavcopy.config",
    "getbhavcopy.core",
    "getbhavcopy.holidays",
    "getbhavcopy.logging_config",
    "getbhavcopy.notifications",
    "getbhavcopy.scheduler",
    "getbhavcopy.settings_windows",
    "getbhavcopy.ui",
    "getbhavcopy.updater",
]

# ── Analysis ──────────────────────────────────────────────────────────────────
a = Analysis(
    ["src/getbhavcopy/__main__.py"],
    pathex=["src"],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "matplotlib",
        "scipy",
        "IPython",
        "jupyter",
        "notebook",
        "pytest",
        "mypy",
        "ruff",
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

# ── Platform-specific build ───────────────────────────────────────────────────

if sys.platform == "darwin":
    # ── Mac — produce a proper .app bundle ───────────────────────────────────
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name="GetBhavCopy",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        console=False,       # windowed — no terminal window
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,    # universal2 handled by CI
        codesign_identity=None,
        entitlements_file=None,
        icon="assets/icon.icns" if Path("assets/icon.icns").exists() else None,
    )

    coll = COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=False,
        upx_exclude=[],
        name="GetBhavCopy",
    )

    app = BUNDLE(
        coll,
        name="GetBhavCopy.app",
        icon="assets/icon.icns" if Path("assets/icon.icns").exists() else None,
        bundle_identifier="com.arickaji.getbhavcopy",
        info_plist={
            "CFBundleName": "GetBhavCopy",
            "CFBundleDisplayName": "GetBhavCopy",
            "CFBundleShortVersionString": "1.3.0",
            "CFBundleVersion": "1.3.0",
            "NSHighResolutionCapable": True,
            "NSRequiresAquaSystemAppearance": False,  # supports dark mode
            "LSMinimumSystemVersion": "11.0",
        },
    )

else:
    # ── Windows — produce a single .exe ──────────────────────────────────────
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        [],
        name="GetBhavCopy",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,       # windowed — no terminal window
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon="assets/icon.ico" if Path("assets/icon.ico").exists() else None,
        onefile=True,
    )

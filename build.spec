# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['src/getbhavcopy/__main__.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'customtkinter',
        'darkdetect',
        'pandas',
        'requests',
        'tkinter',
        'tkinter.ttk',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='GetBhavCopy',
    debug=False,
    strip=False,
    upx=True,
    console=False,
    icon=None,
)

app = BUNDLE(
    exe,
    name='GetBhavCopy.app',
    icon=None,
    bundle_identifier='com.arickaji.getbhavcopy',
)

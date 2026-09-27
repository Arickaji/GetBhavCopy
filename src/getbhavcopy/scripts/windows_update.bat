@echo off
:: =============================================================================
:: GetBhavCopy — Windows Auto-Updater
:: Generated at runtime by updater.py — do not edit manually.
::
:: Placeholders (filled by updater.py before this script runs):
::   {{NEW_EXE}}     — path to the newly downloaded exe in temp dir
::   {{CURRENT_EXE}} — path to the currently installed exe
::   {{PID}}         — PID of the running GetBhavCopy process to wait for
::   {{TMP_DIR}}     — temp dir to clean up after update completes
::
:: Flow:
::   1. Wait for running process to exit (PID-based loop)
::   2. Copy new exe over old exe
::   3. Launch new exe
::   4. Clean up temp files
::   5. Delete this script
:: =============================================================================

setlocal EnableDelayedExpansion

set "NEW_EXE={{NEW_EXE}}"
set "CURRENT_EXE={{CURRENT_EXE}}"
set "PID={{PID}}"
set "TMP_DIR={{TMP_DIR}}"

echo [GetBhavCopy updater] Starting update process...

:: ── 1. Wait for the running process to exit ──────────────────────────────────
echo [GetBhavCopy updater] Waiting for GetBhavCopy (PID %PID%) to exit...

set /a MAX_WAIT=60
set /a ELAPSED=0

:wait_loop
tasklist /FI "PID eq %PID%" /NH 2>nul | find /I "%PID%" >nul 2>&1
if errorlevel 1 goto process_exited

set /a ELAPSED+=1
if %ELAPSED% GEQ %MAX_WAIT% (
    echo [GetBhavCopy updater] Timeout — forcing process termination...
    taskkill /F /PID %PID% >nul 2>&1
    goto process_exited
)

timeout /t 1 /nobreak >nul
goto wait_loop

:process_exited
echo [GetBhavCopy updater] Process exited. Installing update...

:: Extra buffer
timeout /t 2 /nobreak >nul

:: ── 2. Verify new exe exists ─────────────────────────────────────────────────
if not exist "%NEW_EXE%" (
    echo [GetBhavCopy updater] ERROR: New exe not found at %NEW_EXE%
    msg * "GetBhavCopy Update Failed: downloaded file not found. Please download manually from github.com/AricKaji/GetBhavCopy/releases"
    exit /b 1
)

:: ── 3. Copy new exe over old exe ─────────────────────────────────────────────
echo [GetBhavCopy updater] Replacing old exe...
copy /Y "%NEW_EXE%" "%CURRENT_EXE%"

if errorlevel 1 (
    echo [GetBhavCopy updater] ERROR: Could not replace exe. Try running as administrator.
    msg * "GetBhavCopy Update Failed: could not replace the executable. Try running as administrator, or download manually from github.com/AricKaji/GetBhavCopy/releases"
    exit /b 1
)

echo [GetBhavCopy updater] Update installed successfully.

:: ── 4. Launch new version ────────────────────────────────────────────────────
echo [GetBhavCopy updater] Launching new version...
start "" "%CURRENT_EXE%"

:: ── 5. Clean up temp files ───────────────────────────────────────────────────
echo [GetBhavCopy updater] Cleaning up...
if exist "%NEW_EXE%" del /F /Q "%NEW_EXE%"
if exist "%TMP_DIR%" rmdir /S /Q "%TMP_DIR%"

echo [GetBhavCopy updater] Update complete.

:: Self-delete this script
(goto) 2>nul & del "%~f0"

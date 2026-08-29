@echo off
title StealthClip - Setup
echo ==========================================
echo  StealthClip Setup  (one-time install)
echo ==========================================
echo.

rem --- Python check ---
where python >nul 2>nul
if errorlevel 1 (
    echo [X] Python is NOT installed or not in PATH.
    echo     Download it from https://python.org/downloads/
    echo     IMPORTANT: during install tick "Add python.exe to PATH".
    pause
    exit /b 1
)
for /f "delims=" %%i in ('where python') do set "PYEXE=%%i"
echo [OK] Python found: %PYEXE%

rem --- opencode CLI check ---
where opencode >nul 2>nul
if errorlevel 1 (
    echo.
    echo [!] OpenCode is NOT installed yet.
    echo     This AI agent is required. The easiest way on Windows:
    echo       1. Install Node.js from https://nodejs.org
    echo       2. Open a command prompt and run:  npm i -g opencode-ai@latest
    echo       3. Run:  opencode  once, pick your AI provider, and close it.
    echo     (Or use winget:  winget install SST.opencode )
    echo.
    echo Installing now with npm (needs Node.js present)...
    call npm i -g opencode-ai@latest
)

rem --- Python packages ---
echo [..] Installing needed Python packages (pyperclip, pynput)...
"%PYEXE%" -m pip install --upgrade pip >nul
"%PYEXE%" -m pip install -r "%~dp0requirements.txt"
if errorlevel 1 (
    echo [X] pip install failed. Check internet and try again.
    pause
    exit /b 1
)
echo [OK] Python packages installed.

echo.
echo ------------------------------------------
echo  DONE. To start the tool, double-click
echo  "start_hidden.vbs"  - it runs invisibly.
echo  Hotkey: Ctrl + Alt + A
echo ------------------------------------------
pause
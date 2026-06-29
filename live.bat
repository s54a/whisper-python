@echo off
:: live.bat — Start live microphone transcription
:: Run: live.bat
:: Run: live.bat --output notes.txt
:: Run: live.bat --model tiny         (fastest)
:: Run: live.bat --list-devices       (see mic options)

setlocal

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo.
echo  whisper-tools live transcription
echo  Press Ctrl+C to stop
echo.

uv run python live.py %*

echo.
pause

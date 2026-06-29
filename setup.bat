@echo off
:: setup.bat — First-time setup. Run this once.

setlocal
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo.
echo  whisper-tools setup
echo  -------------------

:: Check uv
where uv >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] uv not found. Install it from https://docs.astral.sh/uv/
    pause
    exit /b 1
)

:: Check ffmpeg
where ffmpeg >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] ffmpeg not found. Install it and add to PATH.
    echo  Download: https://ffmpeg.org/download.html
    pause
    exit /b 1
)

echo  uv    found
echo  ffmpeg found

echo.
echo  Installing Python dependencies...
uv sync

echo.
echo  Downloading Whisper small model (first run only, ~250MB)...
uv run python -c "from faster_whisper import WhisperModel; WhisperModel('small', device='cpu', compute_type='int8', download_root='models')"

echo.
echo  [DONE] Setup complete.
echo.
echo  Usage:
echo    - Drag an MP4 onto subtitles.bat to generate subtitles
echo    - Double-click live.bat to start live transcription
echo    - Or use bash: uv run python subtitles.py video.mp4
echo.
pause

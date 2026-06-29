@echo off
:: subtitles.bat — Drag and drop an MP4 onto this file to generate subtitles
:: Or run: subtitles.bat "C:\path\to\video.mp4"
::
:: Requirements: uv installed, run setup.bat first

setlocal

set "SCRIPT_DIR=%~dp0"

if "%~1"=="" (
    echo.
    echo  whisper-tools subtitle generator
    echo  ---------------------------------
    echo  Drag a video file onto this .bat file,
    echo  or run: subtitles.bat "path\to\video.mp4"
    echo.
    pause
    exit /b 1
)

echo.
echo  Generating subtitles for: %~nx1
echo.

cd /d "%SCRIPT_DIR%"
uv run python subtitles.py %1 %2 %3 %4

echo.
pause

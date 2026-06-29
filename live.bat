@echo off
:: live.bat — Start live microphone transcription
::
:: USAGE:
::   live.bat                           Start live transcription (default settings)
::   live.bat --output notes.txt        Save transcript to file
::   live.bat --model tiny              Use faster model (tiny, base, small, medium, large-v3)
::   live.bat --language en             Specify language (skip auto-detect for speed)
::   live.bat --device 2                Use specific microphone (see --list-devices)
::   live.bat --list-devices            Show available microphones and exit
::   live.bat --help                    Show this help message
::
:: EXAMPLES:
::   live.bat --output meeting.txt --model base
::   live.bat --language hi --model small
::   live.bat --list-devices
::
:: CONTROLS:
::   Ctrl+C  → Stop transcription and save

setlocal

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

:: Check for help flag
if /i "%~1"=="--help" goto :show_help
if /i "%~1"=="-h" goto :show_help
if /i "%~1"=="/?" goto :show_help

echo.
echo  [bold cyan]whisper-tools[/bold cyan] live transcription
echo  Press Ctrl+C to stop
echo.

uv run python live.py %*

echo.
pause
exit /b 0

:show_help
echo.
echo  whisper-tools Live Transcription
echo  ================================
echo.
echo  USAGE:
echo    live.bat [OPTIONS]
echo.
echo  OPTIONS:
echo    --output FILE         Save transcript to FILE (e.g. notes.txt)
echo    --model MODEL         Whisper model to use:
echo                          tiny     (fastest, least accurate)
echo                          base     (fast)
echo                          small    (balanced, default)
echo                          medium   (slower, more accurate)
echo                          large-v3 (slowest, most accurate)
echo    --language CODE       Language code (e.g. en, hi, es, fr)
echo                          Omit for auto-detect (slower but automatic)
echo    --device INDEX        Use specific microphone by index number
echo    --list-devices        List all available microphones and exit
echo    --help, -h, /?        Show this help message
echo.
echo  EXAMPLES:
echo    live.bat                              # Default: small model, auto-detect
echo    live.bat --output meeting.txt         # Save to meeting.txt
echo    live.bat --model tiny --language en   # Fastest, English only
echo    live.bat --model medium --output interview.txt
echo    live.bat --list-devices               # Find your microphone index
echo    live.bat --device 2 --model base      # Use mic #2 with base model
echo.
echo  CONTROLS:
echo    Ctrl+C  → Stop transcription and save
echo.
pause
exit /b 0

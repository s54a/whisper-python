@echo off
:: subtitles.bat — Drag and drop an MP4 onto this file to generate subtitles
:: Or run:
::   subtitles.bat "C:\path\to\video.mp4"
::   subtitles.bat --folder "C:\path\to\folder"
::   subtitles.bat --folder "C:\path\to\folder" --model medium --language en
::
:: Requirements: uv installed, run setup.bat first

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"

if "%~1"=="" (
    echo.
    echo  whisper-tools subtitle generator
    echo  ---------------------------------
    echo  Single file:
    echo    Drag a video file onto this .bat file,
    echo    or run: subtitles.bat "path\to\video.mp4"
    echo.
    echo  Batch folder:
    echo    subtitles.bat --folder "path\to\folder"
    echo    subtitles.bat --folder "path\to\folder" --model medium --language en
    echo.
    echo  Supported video formats: .mp4, .mkv, .avi, .mov, .webm
    echo.
    pause
    exit /b 1
)

echo.

:: Check if first argument is --folder flag
if /i "%~1"=="--folder" (
    if "%~2"=="" (
        echo [ERROR] --folder requires a folder path
        pause
        exit /b 1
    )

    set "FOLDER_PATH=%~2"
    set "SHIFT_ARGS=2"

    :: Collect remaining arguments (--model, --language, etc.)
    set "EXTRA_ARGS="
    for /l %%i in (3,1,9) do (
        if not "!%%i!"=="" (
            set "EXTRA_ARGS=!EXTRA_ARGS! !%%i!"
        )
    )

    if not exist "!FOLDER_PATH!\" (
        echo [ERROR] Folder not found: !FOLDER_PATH!
        pause
        exit /b 1
    )

    echo  Batch processing folder: !FOLDER_PATH!
    echo.

    cd /d "%SCRIPT_DIR%"

    :: Process all video files in the folder
    set "PROCESSED=0"
    set "SKIPPED=0"

    for %%f in ("!FOLDER_PATH!\*.mp4" "!FOLDER_PATH!\*.mkv" "!FOLDER_PATH!\*.avi" "!FOLDER_PATH!\*.mov" "!FOLDER_PATH!\*.webm") do (
        if exist "%%f" (
            set "SRT_FILE=%%~dpnf.srt"
            if exist "!SRT_FILE!" (
                echo  [SKIP] SRT already exists: %%~nxf
                set /a SKIPPED+=1
            ) else (
                echo  [PROCESSING] %%~nxf ...
                uv run python subtitles.py "%%f" !EXTRA_ARGS!
                if !errorlevel! equ 0 (
                    set /a PROCESSED+=1
                ) else (
                    echo  [ERROR] Failed: %%~nxf
                )
                echo.
            )
        )
    )

    echo  ----------------------------------------
    echo  Batch complete: !PROCESSED! processed, !SKIPPED! skipped ^(SRT already exists^)
    echo.
    pause
    exit /b 0
) else (
    :: Single file mode (original behavior)
    echo  Generating subtitles for: %~nx1
    echo.

    cd /d "%SCRIPT_DIR%"
    uv run python subtitles.py %1 %2 %3 %4 %5 %6 %7 %8 %9

    echo.
    pause
)

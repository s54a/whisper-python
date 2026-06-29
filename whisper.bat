@echo off
:: subtitles.bat — Generate subtitles for video files using Whisper
::
:: USAGE - Single file:
::   subtitles.bat "C:\path\to\video.mp4"              Generate subtitles for one video
::   subtitles.bat "video.mp4" --model medium          Use medium model for better accuracy
::   subtitles.bat "video.mp4" --language en           Specify language (faster)
::   subtitles.bat "video.mp4" --output custom.srt     Custom output filename
::
:: USAGE - Batch folder:
::   subtitles.bat --folder "C:\path\to\folder"        Process all videos in folder
::   subtitles.bat --folder "folder" --model medium    Use medium model for all
::   subtitles.bat --folder "folder" --language en     English only (faster)
::   subtitles.bat --folder "folder" --skip-existing   Skip if SRT already exists
::
:: USAGE - Help:
::   subtitles.bat --help                              Show this help
::   subtitles.bat -h                                  Show this help
::   subtitles.bat /?                                  Show this help
::
:: EXAMPLES:
::   subtitles.bat "C:\Videos\movie.mp4"
::   subtitles.bat "movie.mp4" --model medium --language en
::   subtitles.bat --folder "C:\Videos" --model base --language en
::   subtitles.bat --folder "Videos" --skip-existing
::
:: SUPPORTED FORMATS:
::   .mp4, .mkv, .avi, .mov, .webm
::
:: MODEL OPTIONS (speed vs accuracy):
::   tiny     → Fastest, least accurate
::   base     → Fast
::   small    → Balanced (default)
::   medium   → Slower, more accurate
::   large-v3 → Slowest, most accurate
::
:: TIPS:
::   • Use --language CODE to speed up processing (e.g., --language en)
::   • Use --model tiny for quick drafts, medium/large for final subtitles
::   • SRT files are saved in the same folder as the video
::   • Batch mode skips videos that already have SRT files (use --skip-existing to change)

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"

:: Check for help flags
if /i "%~1"=="--help" goto :show_help
if /i "%~1"=="-h" goto :show_help
if /i "%~1"=="/?" goto :show_help

if "%~1"=="" (
    echo.
    echo  [bold yellow]whisper-tools subtitle generator[/bold yellow]
    echo  ============================================
    echo.
    echo  [dim]No input provided. See help below:[/dim]
    echo.
    goto :show_help
)

echo.

:: Check if first argument is --folder flag
if /i "%~1"=="--folder" (
    if "%~2"=="" (
        echo [ERROR] --folder requires a folder path
        echo.
        echo Example: subtitles.bat --folder "C:\path\to\folder"
        echo.
        pause
        exit /b 1
    )

    set "FOLDER_PATH=%~2"
    set "SHIFT_ARGS=2"
    set "SKIP_EXISTING=1"

    :: Collect remaining arguments
    set "EXTRA_ARGS="
    set "ARG_COUNT=0"
    for %%a in (%*) do (
        set /a ARG_COUNT+=1
        if !ARG_COUNT! gtr 2 (
            if /i not "%%a"=="--skip-existing" (
                set "EXTRA_ARGS=!EXTRA_ARGS! %%a"
            ) else (
                set "SKIP_EXISTING=0"
            )
        )
    )

    if not exist "!FOLDER_PATH!\" (
        echo [ERROR] Folder not found: !FOLDER_PATH!
        pause
        exit /b 1
    )

    echo  [bold cyan]whisper-tools[/bold cyan] — Batch subtitle generation
    echo  ============================================
    echo  Folder: !FOLDER_PATH!
    if !SKIP_EXISTING! equ 1 (
        echo  Mode  : Skip existing SRT files
    ) else (
        echo  Mode  : Regenerate all (overwrite existing SRT)
    )
    echo  Extra args: !EXTRA_ARGS!
    echo.

    cd /d "%SCRIPT_DIR%"

    :: Process all video files in the folder
    set "PROCESSED=0"
    set "SKIPPED=0"
    set "FAILED=0"

    for %%f in ("!FOLDER_PATH!\*.mp4" "!FOLDER_PATH!\*.mkv" "!FOLDER_PATH!\*.avi" "!FOLDER_PATH!\*.mov" "!FOLDER_PATH!\*.webm") do (
        if exist "%%f" (
            set "SRT_FILE=%%~dpnf.srt"
            if !SKIP_EXISTING! equ 1 if exist "!SRT_FILE!" (
                echo  [SKIP] SRT already exists: %%~nxf
                set /a SKIPPED+=1
            ) else (
                echo  [PROCESSING] %%~nxf ...
                uv run python subtitles.py "%%f" !EXTRA_ARGS!
                if !errorlevel! equ 0 (
                    set /a PROCESSED+=1
                    echo  [OK] Completed: %%~nxf
                ) else (
                    set /a FAILED+=1
                    echo  [ERROR] Failed: %%~nxf
                )
                echo.
            )
        )
    )

    echo  ----------------------------------------
    echo  [bold]Batch complete:[/bold]
    echo    Processed: !PROCESSED!
    echo    Skipped  : !SKIPPED! ^(SRT already exists^)
    if !FAILED! gtr 0 echo    Failed   : !FAILED!
    echo.
    pause
    exit /b 0
) else (
    :: Single file mode
    echo  [bold cyan]whisper-tools[/bold cyan] — Subtitle generation
    echo  ============================================
    echo  File: %~nx1
    echo  Args: %2 %3 %4 %5 %6 %7 %8 %9
    echo.

    cd /d "%SCRIPT_DIR%"
    uv run python subtitles.py %1 %2 %3 %4 %5 %6 %7 %8 %9

    if !errorlevel! equ 0 (
        echo.
        echo  [OK] Subtitles generated successfully!
    ) else (
        echo.
        echo  [ERROR] Failed to generate subtitles
    )
    echo.
    pause
)
exit /b 0

:show_help
echo.
echo  [bold cyan]whisper-tools[/bold cyan] — Subtitle Generator
echo  ============================================
echo  Generate subtitles for video files using OpenAI Whisper
echo.
echo  [bold]USAGE:[/bold]
echo    subtitles.bat [OPTIONS] [VIDEO_FILE]
echo    subtitles.bat --folder [FOLDER] [OPTIONS]
echo.
echo  [bold]SINGLE FILE MODE:[/bold]
echo    subtitles.bat "video.mp4"                Generate subtitles for one video
echo    subtitles.bat "video.mp4" --model medium Use specific model
echo    subtitles.bat "video.mp4" --language en  Specify language (faster)
echo.
echo  [bold]BATCH FOLDER MODE:[/bold]
echo    subtitles.bat --folder "C:\Videos"       Process all videos in folder
echo    subtitles.bat --folder "Videos" --model base --language en
echo    subtitles.bat --folder "Videos" --skip-existing  Regenerate all SRTs
echo.
echo  [bold]OPTIONS:[/bold]
echo    --model MODEL       Whisper model to use:
echo                        [dim]tiny     [/dim]→ Fastest, least accurate
echo                        [dim]base     [/dim]→ Fast
echo                        [dim]small    [/dim]→ Balanced [yellow](default)[/yellow]
echo                        [dim]medium   [/dim]→ Slower, more accurate
echo                        [dim]large-v3 [/dim]→ Slowest, most accurate
echo.
echo    --language CODE     Language code (e.g., en, hi, es, fr, ja)
echo                        Omit for auto-detect (slower but automatic)
echo.
echo    --output FILE       Custom SRT output filename [single file only]
echo                        Default: same name as video in same folder
echo.
echo    --skip-existing     In batch mode: regenerate all SRTs even if exist
echo                        Default: skip videos that already have SRT files
echo.
echo    --help, -h, /?      Show this help message
echo.
echo  [bold]SUPPORTED FORMATS:[/bold]
echo    .mp4, .mkv, .avi, .mov, .webm
echo.
echo  [bold]EXAMPLES:[/bold]
echo    [cyan]# Basic usage[/cyan]
echo    subtitles.bat "C:\Videos\movie.mp4"
echo.
echo    [cyan]# Use medium model for better accuracy[/cyan]
echo    subtitles.bat "interview.mp4" --model medium
echo.
echo    [cyan]# English only for faster processing[/cyan]
echo    subtitles.bat "video.mp4" --language en --model base
echo.
echo    [cyan]# Batch process entire folder[/cyan]
echo    subtitles.bat --folder "C:\Videos\Lectures"
echo.
echo    [cyan]# Batch with specific settings[/cyan]
echo    subtitles.bat --folder "Videos" --model medium --language en
echo.
echo    [cyan]# Regenerate all subtitles (overwrite existing)[/cyan]
echo    subtitles.bat --folder "Videos" --skip-existing
echo.
echo  [bold]TIPS:[/bold]
echo    • Use [cyan]--language CODE[/cyan] to speed up processing significantly
echo    • Use [cyan]--model tiny[/cyan] for quick drafts or testing
echo    • Use [cyan]--model medium[/cyan] or [cyan]large-v3[/cyan] for final production
echo    • SRT files are saved in the same folder as the video
echo    • Batch mode automatically skips existing SRT files by default
echo    • Drag and drop a video file onto subtitles.bat for quick processing
echo.
pause
exit /b 0

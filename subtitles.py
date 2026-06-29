#!/usr/bin/env python3
"""
subtitles.py — MP4 → SRT subtitle generator
Usage:
  python subtitles.py video.mp4
  python subtitles.py video.mp4 --model small
  python subtitles.py video.mp4 --model medium --language hi
  python subtitles.py --folder /path/to/folder
  python subtitles.py --folder /path/to/folder --model medium --language en
"""

import argparse
import subprocess
import sys
import os
import tempfile
from pathlib import Path

from faster_whisper import WhisperModel
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

console = Console()

MODELS_DIR = Path(__file__).parent / "models"
MODELS_DIR.mkdir(exist_ok=True)

VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.mov', '.webm', '.flv', '.wmv'}


def extract_audio(video_path: Path, audio_path: Path) -> None:
    """Extract audio from video using ffmpeg."""
    cmd = [
        "ffmpeg",
        "-i", str(video_path),
        "-vn",                    # no video
        "-acodec", "pcm_s16le",   # WAV format
        "-ar", "16000",           # 16kHz — whisper's native rate
        "-ac", "1",               # mono
        "-y",                     # overwrite if exists
        str(audio_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        console.print(f"[red]ffmpeg error:[/red] {result.stderr}")
        sys.exit(1)


def format_timestamp(seconds: float) -> str:
    """Convert seconds to SRT timestamp format: HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def segments_to_srt(segments) -> str:
    """Convert whisper segments to SRT format string."""
    lines = []
    for i, segment in enumerate(segments, start=1):
        start = format_timestamp(segment.start)
        end = format_timestamp(segment.end)
        text = segment.text.strip()
        lines.append(f"{i}\n{start} --> {end}\n{text}\n")
    return "\n".join(lines)


def get_video_files(folder_path: Path) -> list[Path]:
    """Get all video files in a folder (non-recursive)."""
    video_files = []
    for ext in VIDEO_EXTENSIONS:
        video_files.extend(folder_path.glob(f"*{ext}"))
    return sorted(video_files)


def generate_subtitles(
    video_path: Path,
    model_name: str = "small",
    language: str | None = None,
) -> Path:
    video_path = Path(video_path).resolve()

    if not video_path.exists():
        console.print(f"[red]File not found:[/red] {video_path}")
        sys.exit(1)

    srt_path = video_path.with_suffix(".srt")

    # Skip if SRT already exists
    if srt_path.exists():
        console.print(f"[yellow]⊘ SRT already exists, skipping:[/yellow] {video_path.name}")
        return srt_path

    console.print(f"\n[bold cyan]whisper-tools[/bold cyan] subtitle generator")
    console.print(f"  Video   : {video_path.name}")
    console.print(f"  Model   : {model_name}")
    console.print(f"  Language: {language or 'auto-detect'}")
    console.print(f"  Output  : {srt_path.name}\n")

    # Step 1: Extract audio
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Extracting audio via ffmpeg...", total=None)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            audio_path = Path(tmp.name)

        extract_audio(video_path, audio_path)
        progress.update(task, description="[green]✓ Audio extracted")

        # Step 2: Load model (downloads on first run, cached in ./models)
        progress.add_task(f"Loading whisper [{model_name}] model...", total=None)
        model = WhisperModel(
            model_name,
            device="cpu",
            compute_type="int8",       # fastest on CPU, minimal accuracy loss
            download_root=str(MODELS_DIR),
        )

        # Step 3: Transcribe
        task2 = progress.add_task("Transcribing... (this takes a while on CPU)", total=None)
        segments, info = model.transcribe(
            str(audio_path),
            language=language,
            beam_size=5,
            vad_filter=True,           # skip silence — faster + cleaner output
            vad_parameters=dict(min_silence_duration_ms=500),
        )

        # Consume the generator and collect segments
        all_segments = list(segments)
        progress.update(task2, description=f"[green]✓ Transcribed ({len(all_segments)} segments, detected: {info.language})")

    # Step 4: Write SRT
    srt_content = segments_to_srt(all_segments)
    srt_path.write_text(srt_content, encoding="utf-8")

    # Cleanup temp audio
    audio_path.unlink(missing_ok=True)

    console.print(f"\n[bold green]Done![/bold green] SRT saved to:")
    console.print(f"  [cyan]{srt_path}[/cyan]")
    console.print("\n[dim]VLC will auto-load this if it's in the same folder as the video.[/dim]\n")

    return srt_path


def batch_process_folder(
    folder_path: Path,
    model_name: str = "small",
    language: str | None = None,
) -> None:
    """Process all video files in a folder."""
    folder_path = Path(folder_path).resolve()

    if not folder_path.exists() or not folder_path.is_dir():
        console.print(f"[red]Folder not found:[/red] {folder_path}")
        sys.exit(1)

    video_files = get_video_files(folder_path)

    if not video_files:
        console.print(f"[yellow]No video files found in:[/yellow] {folder_path}")
        console.print(f"[dim]Supported formats: {', '.join(VIDEO_EXTENSIONS)}[/dim]")
        return

    console.print(f"\n[bold cyan]Batch Processing[/bold cyan]")
    console.print(f"  Folder  : {folder_path}")
    console.print(f"  Files   : {len(video_files)} video(s) found")
    console.print(f"  Model   : {model_name}")
    console.print(f"  Language: {language or 'auto-detect'}\n")

    processed = 0
    skipped = 0
    failed = 0

    for i, video_file in enumerate(video_files, 1):
        console.print(f"[bold]━━━ [{i}/{len(video_files)}] Processing: {video_file.name} ━━━[/bold]")

        try:
            srt_path = video_file.with_suffix(".srt")
            if srt_path.exists():
                console.print(f"[yellow]  ⊘ Skipping: SRT already exists[/yellow]")
                skipped += 1
                continue

            generate_subtitles(
                video_path=video_file,
                model_name=model_name,
                language=language,
            )
            processed += 1

        except KeyboardInterrupt:
            console.print("\n[yellow]Batch processing interrupted by user[/yellow]")
            break
        except Exception as e:
            console.print(f"[red]  ✗ Failed: {e}[/red]")
            failed += 1

    # Summary
    console.print(f"\n[bold]{'═' * 60}[/bold]")
    console.print(f"[bold green]Batch Complete![/bold green]")
    console.print(f"  ✓ Processed : {processed}")
    console.print(f"  ⊘ Skipped   : {skipped} (SRT already exists)")
    if failed:
        console.print(f"  ✗ Failed    : {failed}")
    console.print(f"[bold]{'═' * 60}[/bold]\n")


def main():
    parser = argparse.ArgumentParser(
        description="Generate SRT subtitles from a video file or batch process a folder"
    )
    parser.add_argument(
        "video",
        nargs="?",
        help="Path to MP4 (or any video) file",
    )
    parser.add_argument(
        "--folder",
        default=None,
        help="Batch process all videos in a folder",
    )
    parser.add_argument(
        "--model",
        default="small",
        choices=["tiny", "base", "small", "medium", "large-v3"],
        help="Whisper model size (default: small). medium is more accurate but slower.",
    )
    parser.add_argument(
        "--language",
        default=None,
        help="Language code e.g. 'en', 'hi'. Omit for auto-detect.",
    )
    args = parser.parse_args()

    # Batch folder mode
    if args.folder:
        batch_process_folder(
            folder_path=args.folder,
            model_name=args.model,
            language=args.language,
        )
        return

    # Single file mode
    if not args.video:
        parser.error("Either provide a video file or use --folder for batch processing")

    generate_subtitles(
        video_path=args.video,
        model_name=args.model,
        language=args.language,
    )


if __name__ == "__main__":
    main()

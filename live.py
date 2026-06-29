#!/usr/bin/env python3
"""
live.py — Real-time microphone transcription

USAGE:
  python live.py                        # transcribe to terminal
  python live.py --output notes.txt     # also save to file
  python live.py --model medium         # more accurate, slower
  python live.py --language en          # skip auto-detect (faster)
  python live.py --list-devices         # show available microphones
  python live.py --device 2             # use specific microphone

OPTIONS:
  --model MODEL      Whisper model: tiny, base, small (default), medium, large-v3
  --language CODE    Language code (e.g., en, hi, es, fr). Omit for auto-detect.
  --output FILE      Save transcript to FILE
  --device INDEX     Use specific microphone by index number
  --list-devices     List available audio input devices and exit
  --help, -h         Show this help message

CONTROLS:
  Ctrl+C  → Stop transcription and save

EXAMPLES:
  python live.py --model tiny --language en
  python live.py --output interview.txt --model medium
  python live.py --list-devices
  python live.py --device 2

REQUIREMENTS:
  sounddevice, faster-whisper, numpy, rich
"""

import argparse
import queue
import sys
import threading
import time
import tempfile
from datetime import datetime
from pathlib import Path

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

console = Console()

MODELS_DIR = Path(__file__).parent / "models"
MODELS_DIR.mkdir(exist_ok=True)

SAMPLE_RATE = 16000       # whisper's native rate
CHUNK_SECONDS = 3         # how many seconds of audio to transcribe at once
OVERLAP_SECONDS = 0.5     # overlap between chunks to avoid cutting words
SILENCE_THRESHOLD = 0.005  # RMS below this = silence, skip transcription


def rms(audio: np.ndarray) -> float:
    return float(np.sqrt(np.mean(audio**2)))


def list_devices():
    """Print available audio input devices."""
    console.print("\n[bold]Available input devices:[/bold]")
    console.print("[dim]Use --device INDEX to select one[/dim]\n")
    devices = sd.query_devices()
    for i, dev in enumerate(devices):
        if dev["max_input_channels"] > 0:
            console.print(f"  [{i}] {dev['name']}")
    console.print()


def show_help():
    """Display help information."""
    help_text = """
[bold cyan]whisper-tools Live Transcription[/bold cyan]
[dim]Real-time microphone transcription using Whisper[/dim]

[bold]USAGE:[/bold]
  python live.py [OPTIONS]

[bold]OPTIONS:[/bold]
  [cyan]--model MODEL[/cyan]      Whisper model to use:
                     tiny     (fastest, least accurate)
                     base     (fast)
                     small    (balanced, [yellow]default[/yellow])
                     medium   (slower, more accurate)
                     large-v3 (slowest, most accurate)

  [cyan]--language CODE[/cyan]     Language code (e.g., en, hi, es, fr)
                     Omit for auto-detect (slower but automatic)

  [cyan]--output FILE[/cyan]       Save transcript to FILE (e.g., notes.txt)

  [cyan]--device INDEX[/cyan]      Use specific microphone by index number

  [cyan]--list-devices[/cyan]      List all available microphones and exit

  [cyan]--help, -h[/cyan]          Show this help message

[bold]CONTROLS:[/bold]
   [yellow]Ctrl+C[/yellow]  → Stop transcription and save

[bold]EXAMPLES:[/bold]
  # Default settings (small model, auto-detect)
  python live.py

  # Save transcript to file
  python live.py --output meeting.txt

  # Fastest configuration (tiny model, English only)
  python live.py --model tiny --language en

  # More accurate transcription
  python live.py --model medium --output interview.txt

  # Find your microphone
  python live.py --list-devices

  # Use specific microphone
  python live.py --device 2 --model base

[bold]TIPS:[/bold]
  • Use [cyan]--model tiny[/cyan] for near-realtime transcription
  • Use [cyan]--language CODE[/cyan] to speed up processing
  • Increase model size for better accuracy ([cyan]medium[/cyan], [cyan]large-v3[/cyan])
  • Run [cyan]--list-devices[/cyan] to identify your microphone
  • Press [yellow]Ctrl+C[/yellow] to stop and save
"""
    console.print(help_text)


class LiveTranscriber:
    def __init__(
        self,
        model_name: str = "small",
        language: str | None = None,
        output_file: Path | None = None,
        device: int | None = None,
    ):
        self.model_name = model_name
        self.language = language
        self.output_file = output_file
        self.device = device

        self.audio_queue: queue.Queue = queue.Queue()
        self.transcript_lines: list[str] = []
        self.running = False
        self.model: WhisperModel | None = None

        # Rolling buffer for overlap
        self.overlap_samples = int(OVERLAP_SECONDS * SAMPLE_RATE)
        self.prev_tail = np.zeros(self.overlap_samples, dtype=np.float32)

    def load_model(self):
        console.print(f"Loading whisper [{self.model_name}] model...", end=" ")
        self.model = WhisperModel(
            self.model_name,
            device="cpu",
            compute_type="int8",
            download_root=str(MODELS_DIR),
        )
        console.print("[green]ready[/green]")

    def audio_callback(self, indata, frames, time_info, status):
        """Called by sounddevice on each audio chunk."""
        if status:
            pass  # ignore overflow warnings in live mode
        # Store as flat float32 array
        self.audio_queue.put(indata[:, 0].copy())

    def transcribe_chunk(self, audio: np.ndarray) -> str | None:
        """Transcribe a numpy audio array. Returns text or None if silence."""
        if rms(audio) < SILENCE_THRESHOLD:
            return None  # silence — skip API call

        # Write to temp WAV via scipy-free approach using sounddevice's write
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            tmp_path = f.name

        # Manual WAV write (avoids scipy dependency)
        import wave, struct
        with wave.open(tmp_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(SAMPLE_RATE)
            pcm = (audio * 32767).astype(np.int16)
            wf.writeframes(pcm.tobytes())

        try:
            segments, _ = self.model.transcribe(
                tmp_path,
                language=self.language,
                beam_size=3,          # lower beam = faster for live
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=300),
            )
            text = " ".join(s.text.strip() for s in segments).strip()
            return text if text else None
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def transcription_worker(self, display_lines: list, lock: threading.Lock):
        """Background thread: pulls audio from queue, transcribes, updates display."""
        chunk_samples = int(CHUNK_SECONDS * SAMPLE_RATE)
        buffer = np.zeros(0, dtype=np.float32)

        while self.running:
            try:
                chunk = self.audio_queue.get(timeout=0.1)
                buffer = np.concatenate([buffer, chunk])

                if len(buffer) >= chunk_samples:
                    # Prepend overlap from previous chunk
                    audio_to_transcribe = np.concatenate([self.prev_tail, buffer[:chunk_samples]])
                    self.prev_tail = buffer[chunk_samples - self.overlap_samples : chunk_samples]
                    buffer = buffer[chunk_samples:]

                    text = self.transcribe_chunk(audio_to_transcribe)
                    if text:
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        line = f"[{timestamp}] {text}"

                        with lock:
                            display_lines.append(line)
                            # Keep only last 20 lines in display
                            if len(display_lines) > 20:
                                display_lines.pop(0)

                        self.transcript_lines.append(line)

                        if self.output_file:
                            with open(self.output_file, "a", encoding="utf-8") as f:
                                f.write(line + "\n")

            except queue.Empty:
                continue

    def run(self):
        self.load_model()

        display_lines: list[str] = []
        lock = threading.Lock()

        # Start transcription worker thread
        self.running = True
        worker = threading.Thread(
            target=self.transcription_worker,
            args=(display_lines, lock),
            daemon=True,
        )
        worker.start()

        if self.output_file:
            self.output_file.write_text(
                f"# Transcription started {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n",
                encoding="utf-8",
            )

        console.print(f"\n[bold cyan]whisper-tools[/bold cyan] live transcription")
        console.print(f"  Model    : {self.model_name}")
        console.print(f"  Language : {self.language or 'auto-detect'}")
        console.print(f"  Chunk    : {CHUNK_SECONDS}s")
        if self.output_file:
            console.print(f"  Saving to: {self.output_file}")
        console.print(f"\n[dim]Speak into your mic. Press Ctrl+C to stop.[/dim]\n")

        try:
            with sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype="float32",
                blocksize=int(0.1 * SAMPLE_RATE),  # 100ms blocks
                callback=self.audio_callback,
                device=self.device,
            ):
                with Live(console=console, refresh_per_second=4) as live:
                    while True:
                        with lock:
                            lines_copy = list(display_lines)

                        if lines_copy:
                            content = Text("\n".join(lines_copy))
                        else:
                            content = Text("Listening... (waiting for speech)", style="dim")

                        live.update(
                            Panel(
                                content,
                                title="[bold green]● LIVE[/bold green]",
                                border_style="green",
                                padding=(0, 1),
                            )
                        )
                        time.sleep(0.25)

        except KeyboardInterrupt:
            self.running = False
            console.print("\n\n[yellow]Stopped.[/yellow]")

            if self.transcript_lines:
                console.print(f"\n[bold]Full transcript ({len(self.transcript_lines)} chunks):[/bold]")
                for line in self.transcript_lines:
                    console.print(f"  {line}")

            if self.output_file and self.output_file.exists():
                console.print(f"\n[green]Saved to:[/green] {self.output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Live microphone transcription using Whisper",
        add_help=False,  # We'll handle help manually for better formatting
    )
    parser.add_argument(
        "--model",
        default="small",
        choices=["tiny", "base", "small", "medium", "large-v3"],
        help="Whisper model (default: small). tiny is fastest for live use.",
    )
    parser.add_argument(
        "--language",
        default=None,
        help="Language code e.g. 'en', 'hi'. Omit for auto-detect (slower).",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Save transcript to this file (e.g. notes.txt)",
    )
    parser.add_argument(
        "--device",
        type=int,
        default=None,
        help="Audio input device index. Run with --list-devices to see options.",
    )
    parser.add_argument(
        "--list-devices",
        action="store_true",
        help="List available audio input devices and exit.",
    )
    parser.add_argument(
        "--help", "-h",
        action="store_true",
        help="Show this help message and exit.",
    )
    args = parser.parse_args()

    if args.help:
        show_help()
        return

    if args.list_devices:
        list_devices()
        return

    output_path = Path(args.output) if args.output else None

    transcriber = LiveTranscriber(
        model_name=args.model,
        language=args.language,
        output_file=output_path,
        device=args.device,
    )
    transcriber.run()


if __name__ == "__main__":
    main()

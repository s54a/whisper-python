# whisper-tools

Local Whisper-powered subtitle generator and live transcription tool.
No PyTorch. No 5GB installs. CPU-friendly.

## Stack

- [`faster-whisper`](https://github.com/SYSTRAN/faster-whisper) — CTranslate2-based Whisper, runs on CPU with `int8` quantization
- `sounddevice` — mic input for live transcription
- `rich` — terminal UI
- `uv` — Python environment management

## Setup (first time only)

```bash
# Windows
setup.bat

# Git Bash / WSL
uv sync
uv run python -c "from faster_whisper import WhisperModel; WhisperModel('small', device='cpu', compute_type='int8', download_root='models')"
```

Requirements: `uv`, `ffmpeg` both on PATH.

---

## 1. Subtitle Generator — `subtitles.py`

Converts any video file to an SRT subtitle file. VLC auto-loads it.

```bash
# Basic
uv run python subtitles.py video.mp4

# More accurate (slower)
uv run python subtitles.py video.mp4 --model medium

# Specific language (skip auto-detect, faster)
uv run python subtitles.py video.mp4 --language en
uv run python subtitles.py video.mp4 --language hi

# Windows: just drag the MP4 onto subtitles.bat
```

Output: `video.srt` next to your video file. VLC picks it up automatically.

### Models

| Model     | Size  | Speed (CPU) | Accuracy           |
| --------- | ----- | ----------- | ------------------ |
| tiny      | 75MB  | Very fast   | Low                |
| base      | 145MB | Fast        | OK                 |
| **small** | 250MB | **Medium**  | **Good ← default** |
| medium    | 750MB | Slow        | Better             |
| large-v3  | 1.5GB | Very slow   | Best               |

Models download on first use and cache in `./models/`.

---

## 2. Live Transcription — `live.py`

Real-time mic → text in terminal. Also saves to file for note-taking.

```bash
# Basic (terminal only)
uv run python live.py

# Save transcript to file
uv run python live.py --output notes.txt

# Faster (tiny model, lower accuracy)
uv run python live.py --model tiny

# Specific language (faster)
uv run python live.py --language en

# List available microphones
uv run python live.py --list-devices

# Use specific mic (use device index from --list-devices)
uv run python live.py --device 2

# Windows: double-click live.bat
```

Press `Ctrl+C` to stop. Full transcript is printed at the end.

### Tuning for latency vs accuracy

Edit the constants at the top of `live.py`:

```python
CHUNK_SECONDS = 5       # lower = more responsive, less accurate
SILENCE_THRESHOLD = 0.01  # raise if background noise triggers transcription
```

---

## Roadmap

- [ ] System audio loopback capture (WASAPI on Windows)
- [ ] Floating overlay window (tkinter)
- [ ] Cloudflare tunnel to expose to phone
- [ ] WebSocket server for remote clients

---

## Troubleshooting

**`sounddevice` can't find mic on Windows**
Run `uv run python live.py --list-devices` and pass the correct `--device` index.

**Subtitles are off-sync**
Try `--model medium` — small can hallucinate on fast speech.

**ffmpeg not found**
Add ffmpeg to your Windows PATH. [Download here](https://ffmpeg.org/download.html).# whisper-tools

Local Whisper-powered subtitle generator and live transcription tool.
No PyTorch. No 5GB installs. CPU-friendly.

## Stack

- [`faster-whisper`](https://github.com/SYSTRAN/faster-whisper) — CTranslate2-based Whisper, runs on CPU with `int8` quantization
- `sounddevice` — mic input for live transcription
- `rich` — terminal UI
- `uv` — Python environment management

## Setup (first time only)

```bash
# Windows
setup.bat

# Git Bash / WSL
uv sync
uv run python -c "from faster_whisper import WhisperModel; WhisperModel('small', device='cpu', compute_type='int8', download_root='models')"
```

Requirements: `uv`, `ffmpeg` both on PATH.

---

## 1. Subtitle Generator — `subtitles.py`

Converts any video file to an SRT subtitle file. VLC auto-loads it.

```bash
# Basic
uv run python subtitles.py video.mp4

# More accurate (slower)
uv run python subtitles.py video.mp4 --model medium

# Specific language (skip auto-detect, faster)
uv run python subtitles.py video.mp4 --language en
uv run python subtitles.py video.mp4 --language hi

# Windows: just drag the MP4 onto subtitles.bat
```

Output: `video.srt` next to your video file. VLC picks it up automatically.

### Models

| Model     | Size  | Speed (CPU) | Accuracy           |
| --------- | ----- | ----------- | ------------------ |
| tiny      | 75MB  | Very fast   | Low                |
| base      | 145MB | Fast        | OK                 |
| **small** | 250MB | **Medium**  | **Good ← default** |
| medium    | 750MB | Slow        | Better             |
| large-v3  | 1.5GB | Very slow   | Best               |

Models download on first use and cache in `./models/`.

---

## 2. Live Transcription — `live.py`

Real-time mic → text in terminal. Also saves to file for note-taking.

```bash
# Basic (terminal only)
uv run python live.py

# Save transcript to file
uv run python live.py --output notes.txt

# Faster (tiny model, lower accuracy)
uv run python live.py --model tiny

# Specific language (faster)
uv run python live.py --language en

# List available microphones
uv run python live.py --list-devices

# Use specific mic (use device index from --list-devices)
uv run python live.py --device 2

# Windows: double-click live.bat
```

Press `Ctrl+C` to stop. Full transcript is printed at the end.

### Tuning for latency vs accuracy

Edit the constants at the top of `live.py`:

```python
CHUNK_SECONDS = 5       # lower = more responsive, less accurate
SILENCE_THRESHOLD = 0.01  # raise if background noise triggers transcription
```

---

## Roadmap

- [ ] System audio loopback capture (WASAPI on Windows)
- [ ] Floating overlay window (tkinter)
- [ ] Cloudflare tunnel to expose to phone
- [ ] WebSocket server for remote clients

---

## Troubleshooting

**`sounddevice` can't find mic on Windows**
Run `uv run python live.py --list-devices` and pass the correct `--device` index.

**Subtitles are off-sync**
Try `--model medium` — small can hallucinate on fast speech.

**ffmpeg not found**
Add ffmpeg to your Windows PATH. [Download here](https://ffmpeg.org/download.html).

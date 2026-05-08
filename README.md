# YouTube Shorts Bot

Automatically generates YouTube Shorts videos from fact/psychology/science scripts.
Each video is ~35 seconds with:
- Neural AI voiceover (Microsoft Edge TTS)
- Cinematic background video from Pexels
- Karaoke-style synced yellow captions (Montserrat ExtraBold)
- Mood-matched background music (auto-downloaded)
- Ken Burns zoom effect + dark overlay

---

## Prerequisites

- Python 3.11 or higher
- ffmpeg
- A free Pexels API key — get one at https://www.pexels.com/api/

---

## Setup (New Machine)

### 1. Install ffmpeg

**Mac:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt-get install ffmpeg
```

**Windows:**
Download from https://ffmpeg.org/download.html and add to PATH.

---

### 2. Copy the project files

Copy these files to your machine:
```
shorts_bot_new.py
scripts.txt
```

Do NOT copy the `venv/` folder — it must be recreated per machine.

---

### 3. Create a virtual environment and install packages

```bash
python3 -m venv venv
source venv/bin/activate        # Mac/Linux
# OR
venv\Scripts\activate           # Windows

pip install "moviepy==2.1.1" edge-tts gtts requests numpy imageio imageio-ffmpeg decorator faster-whisper Pillow
```

---

### 4. Add your Pexels API key

Open `shorts_bot_new.py` and set your key near the top:

```python
PEXELS_API_KEY = "your_key_here"
```

---

### 5. Run it

```bash
source venv/bin/activate
python3 shorts_bot_new.py
```

The first run will automatically:
- Download the Montserrat ExtraBold font into `./fonts/`
- Download mood-matched background music into `./music/cache/`
- Generate the video into `./output/`

---

## Adding Scripts

`scripts.txt` contains 25 ready-to-use fact scripts.
Copy the `SCRIPTS = [...]` block from it and paste it into `shorts_bot_new.py`, replacing the existing `SCRIPTS` list.

Each script follows this format:

```python
{
    "title": "Short punchy title",
    "hook": "Opening sentence that grabs attention.",
    "story": "3-4 sentences of rich factual detail. ~60-70 words.",
    "outro": "Closing line with call to action. Follow for more.",
    "tags": ["#psychology", "#brainfacts"],
    "hashtags": "#psychology #brainfacts #shorts #fyp",
    "keywords": ["cinematic search term for Pexels video"],
},
```

---

## Config Options

All settings are at the top of `shorts_bot_new.py`:

| Setting | Default | Description |
|---|---|---|
| `PEXELS_API_KEY` | `"YOUR_KEY_HERE"` | Free Pexels API key |
| `SHORTS_PER_DAY` | `1` | Videos to generate per run |
| `OUTPUT_DIR` | `./output` | Where MP4 files are saved |
| `MUSIC_DIR` | `./music` | Music cache folder |
| `FONT_PATH` | `./fonts/Montserrat-ExtraBold.ttf` | Caption font |
| `VIDEO_W / VIDEO_H` | `1080 x 1920` | 9:16 portrait for Shorts |
| `FPS` | `30` | Frames per second |

---

## Background Music

Music is selected automatically based on the script's topic:

| Mood | Triggers on keywords |
|---|---|
| `ambient` | psychology, brain, science, emotion, mind |
| `mysterious` | history, mystery, ancient, secret, dark |
| `cinematic` | story, dramatic, epic, inspiring |
| `upbeat` | motivation, success, fitness, energy |
| `lofi` | focus, study, calm, relax, sleep |

Each mood downloads once and is cached in `./music/cache/`.
To use your own music, drop MP3 files named `ambient.mp3`, `mysterious.mp3`, `cinematic.mp3`, `upbeat.mp3`, or `lofi.mp3` into `./music/cache/`.

---

## Folder Structure

```
shorts_bot/
├── shorts_bot_new.py              # Main bot
├── scripts.txt                    # Script library
├── README.md                      # This file
├── fonts/
│   └── Montserrat-ExtraBold.ttf  # Auto-downloaded on first run
├── music/
│   └── cache/
│       ├── ambient.mp3            # Auto-downloaded on first run
│       ├── mysterious.mp3
│       ├── cinematic.mp3
│       ├── upbeat.mp3
│       └── lofi.mp3
└── output/
    └── 20260508_01_Title.mp4      # Generated videos
```

---

## Daily Schedule (Optional)

**Mac/Linux** — runs at 9am every day:
```bash
crontab -e
```
Add this line (update the path):
```
0 9 * * * /path/to/shorts_bot/venv/bin/python3 /path/to/shorts_bot/shorts_bot_new.py
```

**Windows** — use Task Scheduler:
1. Open Task Scheduler → Create Basic Task
2. Trigger: Daily at 9:00 AM
3. Action: Start a program → `python` → Arguments: `C:\path\to\shorts_bot_new.py`

---

## Troubleshooting

**`ModuleNotFoundError`** — Activate the venv first:
```bash
source venv/bin/activate
```

**No background video** — Check your Pexels API key is set correctly in `shorts_bot_new.py`.

**Font falls back to Arial** — Montserrat auto-downloads on first run. If it fails, the bot continues with Arial Bold — no action needed.

**No background music** — Music auto-downloads on first run. If your network blocks the source, manually place MP3 files in `./music/cache/` named by mood (see above).

**Video generation is slow** — Normal. Compositing a 1080x1920 video with captions takes 1-3 minutes per Short depending on your machine.

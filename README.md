# YouTube Shorts Bot — Setup Guide

## What this does
Runs once a day and creates a complete YouTube Short:
- Writes the script automatically (8 scripts built in, cycles daily)
- Generates AI voiceover (free, no account needed)
- Downloads a matching background video from Pexels (free API)
- Burns in animated captions
- Exports a 1080x1920 MP4 ready to upload

## Setup (one time, ~5 minutes)

### Step 1 — Install Python
Download from https://python.org (version 3.9 or newer)

### Step 2 — Install libraries
Open Terminal (Mac/Linux) or Command Prompt (Windows) and run:
```
pip install moviepy gtts requests Pillow numpy
```

### Step 3 — Get your free Pexels API key
1. Go to https://www.pexels.com/api/
2. Sign up (free, takes 1 minute)
3. Copy your API key

### Step 4 — Paste your key
Open `shorts_bot.py` in any text editor.
Find this line near the top:
```python
PEXELS_API_KEY = "YOUR_KEY_HERE"
```
Replace `YOUR_KEY_HERE` with your actual key. Save the file.

### Step 5 — Run it
```
python shorts_bot.py
```
The MP4 will appear in the `output/` folder after 2-3 minutes.

---

## Run it automatically every day

### Mac / Linux (cron)
```
crontab -e
```
Add this line (runs at 9am daily):
```
0 9 * * * /usr/bin/python3 /full/path/to/shorts_bot.py
```

### Windows (Task Scheduler)
1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Daily at 9:00 AM
4. Action: Start a program → `python` → Arguments: `C:\path\to\shorts_bot.py`

---

## Customise

### Add your own scripts
In `shorts_bot.py`, add to the `SCRIPTS` list:
```python
{
    "title":    "Your video title",
    "hook":     "The first sentence — make it shocking or surprising.",
    "story":    "The explanation. Keep it under 20 seconds when read aloud.",
    "outro":    "Follow for more [topic].",
    "tags":     ["#yourtag", "#anothertag"],
    "keywords": ["pexels search term 1", "pexels search term 2"],
},
```

### Make more per day
Change `SHORTS_PER_DAY = 1` to `2` or `3`.

### Change caption style
Adjust `CAPTION_WORDS = 5` (words per caption line) and `FONT_SIZE` in the config.

---

## Troubleshooting

**"No module named moviepy"** → run `pip install moviepy` again

**"ffmpeg not found"** → install ffmpeg:
- Mac: `brew install ffmpeg`
- Ubuntu: `sudo apt install ffmpeg`
- Windows: download from https://ffmpeg.org and add to PATH

**Videos use color background** → paste your Pexels API key (Step 4)

**Voice sounds robotic** → gTTS uses Google's free TTS. It is natural enough for Shorts.

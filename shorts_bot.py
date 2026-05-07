"""
YouTube Shorts Automation Bot
==============================
Generates a fact/story Short every day — fully automatic.
- Script: built-in curated scripts (no API key needed)
- Voice: edge-tts (Microsoft Neural, free, no key needed — sounds very natural)
- Video: Pexels free API (free key at pexels.com/api)
- Output: Clean MP4 (voice + background video) ready to upload to YouTube Shorts

SETUP (one time, ~2 minutes):
  1. pip3 install moviepy==1.0.3 edge-tts gtts requests Pillow==9.5.0 numpy
  2. Get free Pexels key at: https://www.pexels.com/api/
  3. Paste key below where it says PEXELS_API_KEY = "YOUR_KEY_HERE"
  4. Run: python shorts_bot.py

DAILY SCHEDULE (optional, Mac/Linux):
  crontab -e
  Add line: 0 9 * * * /usr/bin/python3 /path/to/shorts_bot.py

DAILY SCHEDULE (Windows Task Scheduler):
  Action: python C:\\path\\to\\shorts_bot.py
  Trigger: Daily at 9:00 AM
"""

import os
import random
import textwrap
import requests
from datetime import datetime
from pathlib import Path
from typing import Optional

# ─────────────────────────────────────────────
# CONFIG — only edit this section
# ─────────────────────────────────────────────
PEXELS_API_KEY  = "KY21Mu9InDEsNCN2fGbyYvzepG6TpjD8uJi3YQb2Fda2h7Yjrzo5yn7Z"   # free at pexels.com/api
OUTPUT_DIR      = "./output"         # folder where MP4s are saved
SHORTS_PER_DAY  = 1                 # how many Shorts to make per run
VIDEO_W         = 1080
VIDEO_H         = 1920
FPS             = 30
# ─────────────────────────────────────────────


SCRIPTS = [
    {
    "title":    "Scent changes attraction instantly",
    "hook":     "A person’s natural scent can subconsciously increase sexual attraction within seconds.",
    "story":    "Humans constantly pick up chemical cues through scent, even without realizing it. During attraction, the brain links smell with memory, comfort, and arousal — which is why someone’s scent can become deeply addictive and emotionally charged.",
    "outro":    "Sometimes chemistry is literal. Follow for more.",
    "tags":     ["#psychology", "#desire", "#adultfacts", "#science"],
    "keywords": ["perfume closeup", "dark luxury room", "sensual shadows", "golden cinematic lighting"],
}
]


def get_pexels_video(keywords: list, duration_needed: float) -> Optional[str]:
    """Search Pexels for a portrait video matching keywords. Returns local path or None."""
    if PEXELS_API_KEY == "YOUR_KEY_HERE":
        return None

    headers = {"Authorization": PEXELS_API_KEY}
    random.shuffle(keywords)

    for keyword in keywords:
        print(f"  Searching Pexels: '{keyword}'")
        url = (f"https://api.pexels.com/videos/search"
               f"?query={requests.utils.quote(keyword)}&per_page=15&orientation=portrait")
        try:
            r = requests.get(url, headers=headers, timeout=15)
            r.raise_for_status()
            videos = r.json().get("videos", [])
        except Exception as e:
            print(f"  Pexels error: {e}")
            continue

        random.shuffle(videos)
        for v in videos:
            if v.get("duration", 0) < max(10, duration_needed - 5):
                continue
            files = sorted(v.get("video_files", []),
                           key=lambda f: f.get("height", 0), reverse=True)
            for f in files:
                if f.get("height", 0) >= 720:
                    dl_url = f["link"]
                    out = os.path.join(OUTPUT_DIR, "_tmp_bg.mp4")
                    print(f"  Downloading background video...")
                    try:
                        with requests.get(dl_url, stream=True, timeout=90) as resp:
                            resp.raise_for_status()
                            with open(out, "wb") as fh:
                                for chunk in resp.iter_content(65536):
                                    fh.write(chunk)
                        print(f"  Video downloaded.")
                        return out
                    except Exception as e:
                        print(f"  Download failed: {e}")
                        break
    return None


def generate_voice(text: str, out_path: str):
    """Neural TTS via edge-tts (Microsoft, free, sounds very natural).
    Falls back to gTTS if edge-tts is not installed."""
    import asyncio

    async def _edge(txt, path):
        import edge_tts
        voices = [
            "en-US-AriaNeural",
            "en-US-GuyNeural",
            "en-GB-SoniaNeural",
            "en-AU-NatashaNeural",
        ]
        voice = random.choice(voices)
        print(f"  Generating voiceover with {voice}...")
        communicate = edge_tts.Communicate(txt, voice=voice, rate="+8%")
        await communicate.save(path)

    try:
        asyncio.run(_edge(text, out_path))
        print("  Voice ready.")
        return
    except ImportError:
        print("  edge-tts not installed. Run: pip3 install edge-tts")
        print("  Falling back to gTTS...")
    except Exception as e:
        print(f"  edge-tts failed ({e}), falling back to gTTS...")

    from gtts import gTTS
    print("  Generating voiceover (gTTS fallback)...")
    gTTS(text=text, lang="en", slow=False).save(out_path)
    print("  Voice ready.")



def make_short(script: dict, index: int) -> str:
    """Build one complete YouTube Short and return the output path."""
    from moviepy.editor import (
        VideoFileClip, AudioFileClip, CompositeVideoClip,
        ColorClip, concatenate_videoclips, ImageClip
    )
    import numpy as np

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    safe = "".join(c if c.isalnum() or c in " _-" else "" for c in script["title"])[:38]
    date_str = datetime.now().strftime("%Y%m%d")
    out_path = os.path.join(OUTPUT_DIR, f"{date_str}_{index+1:02d}_{safe}.mp4")

    print(f"\n{'='*52}")
    print(f"  Short {index+1}: {script['title']}")
    print(f"{'='*52}")

    # ── Voice ──
    voice_path = os.path.join(OUTPUT_DIR, "_tmp_voice.mp3")
    full_text = f"{script['hook']}  {script['story']}  {script['outro']}"
    generate_voice(full_text, voice_path)
    audio = AudioFileClip(voice_path)
    duration = audio.duration + 1.0

    # ── Background video ──
    bg_path = get_pexels_video(script["keywords"], duration)
    fallback_colors = [(10, 4, 30), (8, 20, 12), (22, 8, 4), (4, 8, 25)]

    if bg_path and os.path.exists(bg_path):
        print("  Preparing background video...")
        raw = VideoFileClip(bg_path, audio=False)

        # Loop to fill duration
        if raw.duration < duration:
            n = int(duration / raw.duration) + 1
            raw = concatenate_videoclips([raw] * n)
        raw = raw.subclip(0, duration)

        # Crop to 9:16
        r = raw.w / raw.h
        t = VIDEO_W / VIDEO_H
        if r > t:
            nw = int(raw.h * t)
            raw = raw.crop(x1=(raw.w - nw) // 2, x2=(raw.w - nw) // 2 + nw)
        else:
            nh = int(raw.w / t)
            raw = raw.crop(y1=(raw.h - nh) // 2, y2=(raw.h - nh) // 2 + nh)

        bg = raw.resize((VIDEO_W, VIDEO_H))
        base = bg
    else:
        print("  Using color background (add Pexels key for real video)...")
        base = ColorClip((VIDEO_W, VIDEO_H),
                         color=fallback_colors[index % len(fallback_colors)]
                         ).set_duration(duration)

    layers = [base]

    # ── Compose & export ──
    print("  Compositing and exporting (this takes 1-3 min)...")
    final = (CompositeVideoClip(layers, size=(VIDEO_W, VIDEO_H))
             .set_audio(audio.set_start(0.4)))

    final.write_videofile(
        out_path,
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        threads=4,
        preset="fast",
        logger=None,
    )

    # Cleanup
    for tmp in ["_tmp_voice.mp3", "_tmp_bg.mp4"]:
        p = os.path.join(OUTPUT_DIR, tmp)
        if os.path.exists(p):
            os.remove(p)

    print(f"\n  Saved: {os.path.abspath(out_path)}")
    return out_path


def main():
    print("\n" + "="*52)
    print("  YouTube Shorts Bot")
    print("="*52)

    if PEXELS_API_KEY == "YOUR_KEY_HERE":
        print("\n  NOTE: No Pexels key found.")
        print("  Get one FREE at: https://www.pexels.com/api/")
        print("  Videos will use color backgrounds for now.\n")

    # Rotate scripts based on day of year so each day = fresh video
    day = datetime.now().timetuple().tm_yday
    made = []
    for i in range(SHORTS_PER_DAY):
        script = SCRIPTS[(day - 1 + i) % len(SCRIPTS)]
        try:
            path = make_short(script, i)
            made.append(path)
        except Exception as e:
            print(f"\n  ERROR on Short {i+1}: {e}")
            import traceback; traceback.print_exc()

    print(f"\n{'='*52}")
    print(f"  COMPLETE — {len(made)} Short(s) ready!")
    print(f"  Folder: {os.path.abspath(OUTPUT_DIR)}")
    print(f"  Upload to YouTube Shorts and you're done.")
    print(f"{'='*52}\n")


if __name__ == "__main__":
    main()
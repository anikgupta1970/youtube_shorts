"""
YouTube Shorts Automation Bot — Improved
==========================================
Generates a fact/story Short every day — fully automatic.
- Script: built-in curated scripts (no API key needed)
- Voice: edge-tts (Microsoft Neural, free — sounds very natural)
- Video: Pexels free API (free key at pexels.com/api)
- Output: Clean MP4 with text overlays, dark vignette, Ken Burns zoom

SETUP (one time, ~2 minutes):
  1. pip3 install --index-url https://pypi.org/simple/ "moviepy==2.1.1" edge-tts gtts requests numpy imageio imageio-ffmpeg decorator
  2. brew install ffmpeg   (Mac) — or install ffmpeg for your OS
  3. Get free Pexels key at: https://www.pexels.com/api/
  4. Paste key below where it says PEXELS_API_KEY = "YOUR_KEY_HERE"
  5. Run: python3 shorts_bot.py

DAILY SCHEDULE (Mac/Linux):
  crontab -e
  Add line: 0 9 * * * /usr/bin/python3 /path/to/shorts_bot.py
"""

import os
import random
import requests
import numpy as np
from datetime import datetime
from typing import Optional

# ─────────────────────────────────────────────
# CONFIG — only edit this section
# ─────────────────────────────────────────────
PEXELS_API_KEY  = "KY21Mu9InDEsNCN2fGbyYvzepG6TpjD8uJi3YQb2Fda2h7Yjrzo5yn7Z"    # free at pexels.com/api
OUTPUT_DIR      = "./output"
SHORTS_PER_DAY  = 1
VIDEO_W         = 1080
VIDEO_H         = 1920
FPS             = 30
# ─────────────────────────────────────────────


SCRIPTS = [
    
    {
    "title": "Your subconscious notices fake smiles instantly",
    "hook": "Humans can subconsciously detect when a smile isn't genuine.",
    "story": "Real smiles activate tiny muscles around the eyes called Duchenne markers. Fake smiles usually involve only the mouth, and the brain notices the inconsistency almost immediately.",
    "outro": "Your brain notices fake emotions faster than you think. Follow for more psychology facts.",
    "tags": ["#psychology", "#bodylanguage", "#brainfacts", "#humanbehavior"],
    "hashtags": "#psychology #bodylanguage #brainfacts #humanbehavior #mindblown #shorts #fyp",
    "keywords": ["smile closeup cinematic", "fake smile portrait", "dramatic face lighting", "human emotion aesthetic"],
}
]


# ─────────────────────────────────────────────
# BEST NEURAL VOICES — authoritative & clear
# ─────────────────────────────────────────────
VOICES = [
    "en-US-AndrewNeural",   # deep, confident male — best for facts/psychology
    "en-US-BrianNeural",    # calm, storytelling tone
    "en-US-EmmaNeural",     # warm, engaging female
    "en-GB-RyanNeural",     # British male — sounds premium/authoritative
    "en-GB-SoniaNeural",    # British female — very clear
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
    """Neural TTS via edge-tts. Falls back to gTTS if unavailable."""
    import asyncio

    async def _edge(txt, path):
        import edge_tts
        voice = random.choice(VOICES)
        print(f"  Generating voiceover with {voice}...")
        communicate = edge_tts.Communicate(txt, voice=voice, rate="+2%", pitch="-2Hz")
        await communicate.save(path)

    try:
        asyncio.run(_edge(text, out_path))
        print("  Voice ready.")
        return
    except ImportError:
        print("  edge-tts not installed. Falling back to gTTS...")
    except Exception as e:
        print(f"  edge-tts failed ({e}), falling back to gTTS...")

    from gtts import gTTS
    print("  Generating voiceover (gTTS fallback)...")
    gTTS(text=text, lang="en", slow=False).save(out_path)
    print("  Voice ready.")


def zoom_effect(clip, zoom_ratio=0.04):
    """Ken Burns slow zoom-in effect — makes static footage feel cinematic."""
    from PIL import Image

    def effect(get_frame, t):
        img = get_frame(t)
        scale = 1 + zoom_ratio * (t / clip.duration)
        h, w = img.shape[:2]
        new_h, new_w = int(h * scale), int(w * scale)
        pil = Image.fromarray(img).resize((new_w, new_h), Image.LANCZOS)
        y1 = (new_h - h) // 2
        x1 = (new_w - w) // 2
        return np.array(pil)[y1:y1 + h, x1:x1 + w]

    return clip.transform(effect)


def make_text_clips(audio_path: str):
    """
    Perfectly synced subtitles using faster-whisper word timestamps.
    """

    from faster_whisper import WhisperModel
    from moviepy import TextClip

    print("  Loading Whisper model...")

    model = WhisperModel(
        "tiny",          # use "base" for better accuracy
        compute_type="int8"
    )

    print("  Transcribing audio...")

    segments, _ = model.transcribe(
        audio_path,
        word_timestamps=True
    )

    clips = []

    for segment in segments:
        for word in segment.words:

            text = word.word.strip()

            if not text:
                continue

            start = float(word.start)
            end   = float(word.end)

            duration = max(0.10, (end - start) - 0.03)

            try:
                txt = (
                    TextClip(
                        text=text.upper(),
                        font_size=82,
                        color="white",
                        stroke_color="black",
                        stroke_width=4,
                        font="/System/Library/Fonts/Supplemental/Arial Bold.ttf",
                        method="label",
                    )
                    .with_start(start + 0.4)
                    .with_duration(duration + 0.05)
                    .with_position(("center", 1450))
                )

                clips.append(txt)

            except Exception as e:
                print(f"  Subtitle error: {e}")

    print(f"  {len(clips)} synced subtitle clips created.")

    return clips
def make_short(script: dict, index: int) -> str:
    """Build one complete YouTube Short and return the output path."""
    from moviepy import (
        VideoFileClip, AudioFileClip, CompositeVideoClip,
        ColorClip, concatenate_videoclips,
    )

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    safe     = "".join(c if c.isalnum() or c in " _-" else "" for c in script["title"])[:38]
    date_str = datetime.now().strftime("%Y%m%d")
    out_path = os.path.join(OUTPUT_DIR, f"{date_str}_{index + 1:02d}_{safe}.mp4")

    print(f"\n{'=' * 52}")
    print(f"  Short {index + 1}: {script['title']}")
    print(f"{'=' * 52}")

    # ── Voice ──
    voice_path = os.path.join(OUTPUT_DIR, "_tmp_voice.mp3")
    full_text  = f"{script['hook']}  {script['story']}  {script['outro']}"
    generate_voice(full_text, voice_path)
    audio    = AudioFileClip(voice_path)
    duration = audio.duration + 1.0

    # ── Background video ──
    bg_path         = get_pexels_video(script["keywords"], duration)
    fallback_colors = [(10, 4, 30), (8, 20, 12), (22, 8, 4), (4, 8, 25)]

    if bg_path and os.path.exists(bg_path):
        print("  Preparing background video...")
        raw = VideoFileClip(bg_path, audio=False)

        # Loop to fill duration
        if raw.duration < duration:
            n   = int(duration / raw.duration) + 1
            raw = concatenate_videoclips([raw] * n)
        raw = raw.subclipped(0, duration)

        # Crop to 9:16
        r = raw.w / raw.h
        t = VIDEO_W / VIDEO_H
        if r > t:
            nw  = int(raw.h * t)
            raw = raw.cropped(x1=(raw.w - nw) // 2, x2=(raw.w - nw) // 2 + nw)
        else:
            nh  = int(raw.w / t)
            raw = raw.cropped(y1=(raw.h - nh) // 2, y2=(raw.h - nh) // 2 + nh)

        base = zoom_effect(raw.resized((VIDEO_W, VIDEO_H)))
        print("  Ken Burns zoom applied.")
    else:
        print("  Using color background (add Pexels key for real video)...")
        base = ColorClip(
            (VIDEO_W, VIDEO_H),
            color=fallback_colors[index % len(fallback_colors)]
        ).with_duration(duration)

    # ── Dark overlay for text readability ──
    dark_overlay = (
        ColorClip((VIDEO_W, VIDEO_H), color=(0, 0, 0))
        .with_duration(duration)
        .with_opacity(0.45)
    )

    # ── Karaoke captions ──
    print("  Generating text overlays...")
    text_clips = make_text_clips(voice_path)
    print(f"  {len(text_clips)} caption chunks created.")

    # ── Compose & export ──
    layers = [base, dark_overlay] + text_clips
    print("  Compositing and exporting (this takes 1-3 min)...")
    final = (
        CompositeVideoClip(layers, size=(VIDEO_W, VIDEO_H))
        .with_audio(audio.with_start(0.4))
    )

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
    print("\n" + "=" * 52)
    print("  YouTube Shorts Bot — Enhanced")
    print("=" * 52)

    if PEXELS_API_KEY == "YOUR_KEY_HERE":
        print("\n  NOTE: No Pexels key found.")
        print("  Get one FREE at: https://www.pexels.com/api/")
        print("  Videos will use colour backgrounds for now.\n")

    day  = datetime.now().timetuple().tm_yday
    made = []

    for i in range(SHORTS_PER_DAY):
        script = SCRIPTS[(day - 1 + i) % len(SCRIPTS)]
        try:
            path = make_short(script, i)
            made.append(path)
        except Exception as e:
            print(f"\n  ERROR on Short {i + 1}: {e}")
            import traceback; traceback.print_exc()

    print(f"\n{'=' * 52}")
    print(f"  COMPLETE — {len(made)} Short(s) ready!")
    print(f"  Folder: {os.path.abspath(OUTPUT_DIR)}")
    print(f"  Upload to YouTube Shorts and you're done.")
    print(f"{'=' * 52}\n")


if __name__ == "__main__":
    main()

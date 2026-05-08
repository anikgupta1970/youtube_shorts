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
MUSIC_DIR       = "./music"       # auto-downloaded tracks cached here by mood
FONT_PATH       = "./fonts/Montserrat-ExtraBold.ttf"
SHORTS_PER_DAY  = 1
VIDEO_W         = 1080
VIDEO_H         = 1920
FPS             = 30
# ─────────────────────────────────────────────


SCRIPTS = [
    
   {
        "title": "You yawn because of mirror neurons",
        "hook": "Yawning is contagious — and the biological reason behind it reveals something remarkable about how humans are wired for empathy.",
        "story": "Your brain contains mirror neurons that fire when you observe someone else performing an action, creating an internal simulation of that action in yourself. Contagious yawning is a direct result of this system. Studies show it is strongest between people who are emotionally close. The more empathy you naturally feel toward others, the more easily their yawn will trigger yours. Sociopaths almost never catch yawns.",
        "outro": "Even reading the word yawn right now might be making you yawn. Follow for more brain science.",
        "tags": ["#brainfacts", "#empathy", "#neuroscience", "#humanbehavior"],
        "hashtags": "#brainfacts #empathy #neuroscience #humanbehavior #shorts #fyp",
        "keywords": ["person yawning closeup", "tired face dramatic lighting", "social connection cinematic", "human emotion portrait"],
        "music": "lofi",
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


# Valid music moods — set "music" field in each script to one of these
MOOD_MAP = {
    "ambient",       # calm, spacious, neutral — psychology/science topics
    "mysterious",    # dark, tense, suspenseful — secrets/history/unknown
    "cinematic",     # epic, soaring, powerful — inspiring/world-changing facts
    "upbeat",        # bright, energetic, happy — motivation/fitness/success
    "lofi",          # chill, nostalgic, soft — sleep/focus/anxiety/study
    "dramatic",      # intense, emotional — shocking facts/social issues
    "dark",          # heavy, ominous — disturbing truths/conspiracy
    "happy",         # cheerful, warm — feel-good facts/kindness
    "sad",           # melancholic, reflective — loss/memory/loneliness
    "energetic",     # fast, driving — action/sports/adrenaline
    "peaceful",      # serene, gentle — nature/meditation/mindfulness
    "tense",         # anxious, gripping — danger/survival/fear
    "inspirational", # uplifting, hopeful — growth/achievement/purpose
}


def detect_mood(script: dict) -> str:
    """Read mood directly from the script's 'music' field.
    Valid values: ambient | mysterious | cinematic | upbeat | lofi |
                  dramatic | dark | happy | sad | energetic | peaceful |
                  tense | inspirational
    Defaults to 'ambient' if the field is missing or invalid.
    """
    mood = script.get("music", "").strip().lower()
    if mood in MOOD_MAP:
        return mood
    if mood:
        print(f"  WARNING: unknown music value '{mood}', defaulting to 'ambient'.")
    return "ambient"


def fetch_music(mood: str) -> Optional[str]:
    """
    Download a real CC-licensed music track from ccMixter (no API key needed).
    Falls back to SoundHelix royalty-free tracks if ccMixter is unreachable.
    Always fetches a fresh track at runtime — no caching.
    """
    cache_dir = os.path.join(MUSIC_DIR, "cache")
    os.makedirs(cache_dir, exist_ok=True)
    cache_file = os.path.join(cache_dir, f"{mood}.mp3")

    # ccMixter search tags per mood
    MOOD_TAGS = {
        "ambient":       "ambient",
        "mysterious":    "dark",
        "cinematic":     "epic",
        "upbeat":        "upbeat",
        "lofi":          "chill",
        "dramatic":      "dramatic",
        "dark":          "dark",
        "happy":         "happy",
        "sad":           "sad",
        "energetic":     "energetic",
        "peaceful":      "peaceful",
        "tense":         "tense",
        "inspirational": "inspirational",
    }

    # SoundHelix fallback — real royalty-free tracks, always available
    SOUNDHELIX_FALLBACK = {
        "ambient":       "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
        "mysterious":    "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-11.mp3",
        "cinematic":     "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-9.mp3",
        "upbeat":        "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3",
        "lofi":          "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-6.mp3",
        "dramatic":      "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-8.mp3",
        "dark":          "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-13.mp3",
        "happy":         "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-4.mp3",
        "sad":           "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-12.mp3",
        "energetic":     "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-5.mp3",
        "peaceful":      "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-7.mp3",
        "tense":         "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-14.mp3",
        "inspirational": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-15.mp3",
    }

    tag = MOOD_TAGS.get(mood, "ambient")

    # ── Try ccMixter first ──
    print(f"  Fetching '{mood}' music from ccMixter...")
    try:
        search_url = f"http://ccmixter.org/api/query?f=json&tags={tag}&limit=10"
        r = requests.get(search_url, timeout=12)
        r.raise_for_status()
        tracks = r.json()
        random.shuffle(tracks)
        for track in tracks:
            for f in track.get("files", []):
                dl_url = f.get("download_url", "")
                if not dl_url.endswith(".mp3"):
                    continue
                dl_url = dl_url.replace("https://ccmixter.org/", "http://ccmixter.org/")
                try:
                    with requests.get(dl_url, stream=True, timeout=60) as resp:
                        resp.raise_for_status()
                        with open(cache_file, "wb") as fh:
                            for chunk in resp.iter_content(65536):
                                fh.write(chunk)
                    print(f"  Music ready: {track.get('upload_name', dl_url)}")
                    return cache_file
                except Exception:
                    continue
    except Exception as e:
        print(f"  ccMixter unavailable ({e}), trying fallback...")

    # ── SoundHelix fallback ──
    fallback_url = SOUNDHELIX_FALLBACK.get(mood, SOUNDHELIX_FALLBACK["ambient"])
    print(f"  Downloading fallback track...")
    try:
        with requests.get(fallback_url, stream=True, timeout=30) as resp:
            resp.raise_for_status()
            with open(cache_file, "wb") as fh:
                for chunk in resp.iter_content(65536):
                    fh.write(chunk)
        print(f"  Fallback music ready.")
        return cache_file
    except Exception as e:
        print(f"  Music download failed ({e}). Proceeding without music.")

    return None


def setup_font():
    """Download Montserrat ExtraBold if not already present."""
    if os.path.exists(FONT_PATH):
        return
    os.makedirs(os.path.dirname(FONT_PATH), exist_ok=True)
    print("  Downloading Montserrat ExtraBold font...")
    url = "https://github.com/JulietaUla/Montserrat/raw/master/fonts/ttf/Montserrat-ExtraBold.ttf"
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        with open(FONT_PATH, "wb") as f:
            f.write(r.content)
        print("  Font ready.")
    except Exception as e:
        print(f"  Font download failed ({e}), falling back to Arial Bold.")


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

            font = FONT_PATH if os.path.exists(FONT_PATH) else "/System/Library/Fonts/Supplemental/Arial Bold.ttf"

            try:
                txt = (
                    TextClip(
                        text=text.upper(),
                        font_size=88,
                        color="#FFE600",
                        stroke_color="black",
                        stroke_width=5,
                        font=font,
                        method="label",
                        bg_color=(20, 20, 20),
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
        ColorClip, concatenate_videoclips, CompositeAudioClip, TextClip,
    )

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    safe     = "".join(c if c.isalnum() or c in " _-" else "" for c in script["title"])[:38]
    date_str = datetime.now().strftime("%Y%m%d")
    out_path = os.path.join(OUTPUT_DIR, f"{date_str}_{index + 1:02d}_{safe}.mp4")

    print(f"\n{'=' * 52}")
    print(f"  Short {index + 1}: {script['title']}")
    print(f"{'=' * 52}")

    # ── Voice ──
    title_duration = 1.5   # must match the title card duration below
    voice_path = os.path.join(OUTPUT_DIR, "_tmp_voice.mp3")
    full_text  = f"{script['hook']}  {script['story']}  {script['outro']}"
    generate_voice(full_text, voice_path)
    audio    = AudioFileClip(voice_path)
    duration = audio.duration + 1.0 + title_duration

    # ── Background music (auto-selected by mood) ──
    mood       = detect_mood(script)
    music_path = fetch_music(mood)
    if music_path:
        print(f"  Adding '{mood}' background music...")
        music = AudioFileClip(music_path)
        if music.duration < duration:
            loops = int(duration / music.duration) + 1
            from moviepy import concatenate_audioclips
            music = concatenate_audioclips([music] * loops)
        music = music.subclipped(0, duration).with_volume_scaled(0.12)
        final_audio = CompositeAudioClip([audio.with_start(title_duration), music])
        print(f"  Background music mixed in at 12% volume. Duration: {duration:.1f}s")
    else:
        print("  No background music found — proceeding without music.")
        final_audio = audio.with_start(title_duration)

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
        .with_opacity(0.25)
    )

    # ── Title card (first frame = cover photo) ──
    font = FONT_PATH if os.path.exists(FONT_PATH) else "/System/Library/Fonts/Supplemental/Arial Bold.ttf"

    title_bg = (
        ColorClip((VIDEO_W, VIDEO_H), color=(0, 0, 0))
        .with_duration(title_duration)
        .with_opacity(0.55)
    )
    title_clip = (
        TextClip(
            text=script["title"].upper(),
            font_size=72,
            color="white",
            stroke_color="black",
            stroke_width=4,
            font=font,
            method="caption",
            size=(VIDEO_W - 140, None),
        )
        .with_start(0)
        .with_duration(title_duration)
        .with_position("center")
    )

    # ── Karaoke captions ──
    print("  Generating text overlays...")
    text_clips = make_text_clips(voice_path)
    # Offset captions so they start after the title card finishes
    text_clips = [c.with_start(c.start + title_duration) for c in text_clips]
    print(f"  {len(text_clips)} caption chunks created.")

    # ── Compose & export ──
    layers = [base, dark_overlay, title_bg, title_clip] + text_clips
    print("  Compositing and exporting (this takes 1-3 min)...")
    final = (
        CompositeVideoClip(layers, size=(VIDEO_W, VIDEO_H))
        .with_audio(final_audio)
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

    setup_font()

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

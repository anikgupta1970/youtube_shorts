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
"title": "Some phobias are far stranger than you think",
"hook": "Your brain can turn almost anything into a fear.",
"story": "Claustrophobia is the fear of enclosed spaces. Cynophobia is the fear of dogs.Somniphobia is the fear of falling asleep. And yes — some people even have chromophobia, the fear of certain colors. Phobias happen when the brain links something harmless with danger so strongly that the fear becomes automatic.",
"outro": "To one brain it’s ordinary. To another, it feels like survival. Follow for more.",
"tags": ["#phobias", "#psychology", "#brainfacts", "#neuroscience"],
"hashtags": "#phobias #psychology #brainfacts #fear #mind #neuroscience #shorts #fyp",
"keywords": ["surreal fear aesthetic", "claustrophobia tunnel cinematic", "dark psychology visuals", "phobia montage cinematic"],
"music": "suspense"
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
    "suspense",      # building tension — phobias/thrillers/mysteries
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
        "suspense":      "dark",
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
        "suspense":      "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-13.mp3",
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


def get_pexels_videos(keywords: list, count: int = 3) -> list:
    """
    Fetch up to `count` distinct portrait clips from Pexels, one per keyword.
    Returns a list of local file paths (may be shorter than `count` if some
    keywords yield no usable result).
    """
    if PEXELS_API_KEY == "YOUR_KEY_HERE":
        return []

    headers  = {"Authorization": PEXELS_API_KEY}
    keywords = list(keywords)          # don't mutate the script dict
    random.shuffle(keywords)
    paths    = []
    used_ids = set()                   # avoid downloading the same video twice

    for keyword in keywords:
        if len(paths) >= count:
            break
        print(f"  Searching Pexels [{len(paths)+1}/{count}]: '{keyword}'")
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
            if v.get("id") in used_ids:
                continue
            if v.get("duration", 0) < 8:
                continue
            files = sorted(v.get("video_files", []),
                           key=lambda f: f.get("height", 0), reverse=True)
            for f in files:
                if f.get("height", 0) >= 720:
                    dl_url = f["link"]
                    out    = os.path.join(OUTPUT_DIR, f"_tmp_bg_{len(paths)}.mp4")
                    print(f"  Downloading clip {len(paths)+1}...")
                    try:
                        with requests.get(dl_url, stream=True, timeout=90) as resp:
                            resp.raise_for_status()
                            with open(out, "wb") as fh:
                                for chunk in resp.iter_content(65536):
                                    fh.write(chunk)
                        used_ids.add(v["id"])
                        paths.append(out)
                        print(f"  Clip {len(paths)} ready.")
                        break
                    except Exception as e:
                        print(f"  Download failed: {e}")
                        break
            if len(paths) >= count:
                break

    return paths


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


def _apply_zoom(clip, start_scale=1.0, end_scale=1.08):
    """Smooth zoom between start_scale and end_scale over the clip's duration."""
    from PIL import Image

    def effect(get_frame, t):
        img = get_frame(t)
        progress = t / max(clip.duration, 0.001)
        scale = start_scale + (end_scale - start_scale) * progress
        h, w = img.shape[:2]
        new_h, new_w = int(h * scale), int(w * scale)
        pil = Image.fromarray(img).resize((new_w, new_h), Image.LANCZOS)
        y1 = (new_h - h) // 2
        x1 = (new_w - w) // 2
        return np.array(pil)[y1:y1 + h, x1:x1 + w]

    return clip.transform(effect)


def _apply_pan(clip, direction="left", amount=0.06):
    """Horizontal pan — slides a cropped window left or right, then resizes back."""
    from PIL import Image

    def effect(get_frame, t):
        img = get_frame(t)
        progress = t / max(clip.duration, 0.001)
        h, w = img.shape[:2]
        crop_w = int(w * (1 - amount))
        max_offset = w - crop_w
        x1 = int(max_offset * progress) if direction == "left" else int(max_offset * (1 - progress))
        cropped = img[:, x1:x1 + crop_w, :]
        pil = Image.fromarray(cropped).resize((w, h), Image.LANCZOS)
        return np.array(pil)

    return clip.transform(effect)


def dynamic_bg(clip, seg_min=2.0, seg_max=3.0):
    """
    Splits the clip into 2–3 s segments and applies a random camera move
    (zoom in / zoom out / pan left / pan right) to each one.
    Concatenating them creates visible cuts that sustain viewer attention.
    """
    from moviepy import concatenate_videoclips

    EFFECTS = ["zoom_in", "zoom_out", "pan_left", "pan_right"]
    total    = clip.duration
    segments = []
    t        = 0.0

    while t < total:
        seg_dur = random.uniform(seg_min, seg_max)
        seg_dur = min(seg_dur, total - t)
        if seg_dur < 0.5:
            break

        seg    = clip.subclipped(t, t + seg_dur)
        effect = random.choice(EFFECTS)

        if effect == "zoom_in":
            seg = _apply_zoom(seg, start_scale=1.0, end_scale=1.08)
        elif effect == "zoom_out":
            seg = _apply_zoom(seg, start_scale=1.08, end_scale=1.0)
        elif effect == "pan_left":
            seg = _apply_pan(seg, direction="left")
        else:
            seg = _apply_pan(seg, direction="right")

        segments.append(seg)
        t += seg_dur

    return concatenate_videoclips(segments) if segments else clip


def crossfade_concat(clips, transition=0.4):
    """
    Concatenate clips with a smooth dissolve between each scene.
    Adjacent clips overlap by `transition` seconds; pixel values are
    linearly blended so the cut feels like a professional dissolve rather
    than a hard jump.
    """
    from moviepy import VideoClip as VC

    if len(clips) == 1:
        return clips[0]

    # Place each clip so it starts `transition` seconds before the previous one ends
    starts = []
    t = 0.0
    for i, clip in enumerate(clips):
        starts.append(t)
        t += clip.duration - (transition if i < len(clips) - 1 else 0)
    total_duration = t

    def make_frame(t_abs):
        active = []
        for clip, start in zip(clips, starts):
            local_t = t_abs - start
            if 0.0 <= local_t < clip.duration:
                active.append((clip, local_t))

        if not active:
            return np.zeros((VIDEO_H, VIDEO_W, 3), dtype=np.uint8)
        if len(active) == 1:
            return active[0][0].get_frame(active[0][1])

        # Two clips overlap — dissolve outgoing → incoming
        clip_out, t_out = active[0]
        clip_in,  t_in  = active[1]
        alpha     = min(1.0, t_in / transition)
        frame_out = clip_out.get_frame(t_out).astype(np.float32)
        frame_in  = clip_in.get_frame(t_in).astype(np.float32)
        return ((1 - alpha) * frame_out + alpha * frame_in).astype(np.uint8)

    return VC(frame_function=make_frame, duration=total_duration)


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
        FADE_OUT = 1.5  # seconds to fade music out at the end
        from moviepy.audio.fx import AudioFadeOut
        music = (
            music.subclipped(0, duration)
            .with_volume_scaled(0.12)
            .with_effects([AudioFadeOut(FADE_OUT)])
        )
        final_audio = CompositeAudioClip([audio.with_start(title_duration), music])
        print(f"  Background music mixed in at 12% volume, fades out over last {FADE_OUT}s. Duration: {duration:.1f}s")
    else:
        print("  No background music found — proceeding without music.")
        final_audio = audio.with_start(title_duration)

    # ── Background video ──
    bg_paths        = get_pexels_videos(script["keywords"], count=4)
    fallback_colors = [(10, 4, 30), (8, 20, 12), (22, 8, 4), (4, 8, 25)]
    TRANSITION      = 0.4  # crossfade duration between scenes (seconds)

    def _crop_and_process(path: str, seg_duration: float):
        """Load one clip, loop/trim to seg_duration, crop to 9:16, apply dynamic moves."""
        raw = VideoFileClip(path, audio=False)
        if raw.duration < seg_duration:
            n   = int(seg_duration / raw.duration) + 1
            raw = concatenate_videoclips([raw] * n)
        raw = raw.subclipped(0, seg_duration)
        r   = raw.w / raw.h
        t   = VIDEO_W / VIDEO_H
        if r > t:
            nw  = int(raw.h * t)
            raw = raw.cropped(x1=(raw.w - nw) // 2, x2=(raw.w - nw) // 2 + nw)
        else:
            nh  = int(raw.w / t)
            raw = raw.cropped(y1=(raw.h - nh) // 2, y2=(raw.h - nh) // 2 + nh)
        return dynamic_bg(raw.resized((VIDEO_W, VIDEO_H)))

    if bg_paths:
        n         = len(bg_paths)
        # Each clip is slightly longer than its share so overlapping transitions
        # don't shorten the total — total = n*seg_dur - (n-1)*TRANSITION = duration
        seg_dur   = (duration + (n - 1) * TRANSITION) / n
        print(f"  Building background from {n} distinct clip(s) ({seg_dur:.1f}s each, {TRANSITION}s dissolves)...")
        segments  = [_crop_and_process(p, seg_dur) for p in bg_paths]
        base      = crossfade_concat(segments, TRANSITION)
        print(f"  {n} scenes assembled with crossfade transitions.")
    else:
        print("  Using color background (add Pexels key for real video)...")
        base = ColorClip(
            (VIDEO_W, VIDEO_H),
            color=fallback_colors[index % len(fallback_colors)]
        ).with_duration(duration)

    # ── Overlays ──
    # Light overlay for the whole video — just enough for caption readability
    dark_overlay = (
        ColorClip((VIDEO_W, VIDEO_H), color=(0, 0, 0))
        .with_duration(duration)
        .with_opacity(0.10)
    )
    # Heavy overlay only during title card — creates visible brightness jump when it ends
    title_bg = (
        ColorClip((VIDEO_W, VIDEO_H), color=(0, 0, 0))
        .with_duration(title_duration)
        .with_opacity(0.50)
    )

    # ── Title card (first frame = cover photo) ──
    font = FONT_PATH if os.path.exists(FONT_PATH) else "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
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

    # ── Watermark ──
    _wm = TextClip(
        text="@did.u.knoww",
        font_size=36,
        color="white",
        stroke_color="black",
        stroke_width=2,
        font=font,
        method="label",
    )
    watermark = (
        _wm
        .with_duration(duration)
        .with_position((VIDEO_W - _wm.w - 40, int(VIDEO_H * 0.25)))
        .with_opacity(0.6)
    )

    # ── Compose & export ──
    layers = [base, dark_overlay, title_bg, title_clip] + text_clips + [watermark]
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
        bitrate="1500k",
        threads=4,
        preset="fast",
        logger=None,
    )

    # Cleanup
    for tmp in ["_tmp_voice.mp3"] + [f"_tmp_bg_{i}.mp4" for i in range(4)]:
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

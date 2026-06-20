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
  2. Install ffmpeg: Mac → brew install ffmpeg | Windows → winget install ffmpeg | Linux → sudo apt install ffmpeg
  3. Get free Pexels key at: https://www.pexels.com/api/
  4. Paste key below where it says PEXELS_API_KEY = "YOUR_KEY_HERE"
  5. Run: python3 shorts_bot.py

"""

import os
import random
import threading
import requests
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
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
"title": "The snake that builds a living shield",
"hook": "Some snakes have evolved armor-like defenses against predators.",
"story": "Not every snake relies on venom or speed to survive. Some species use powerful muscles, thick scales, camouflage, and defensive behaviors to protect themselves. When threatened, they may flatten their bodies, imitate dangerous species, or disappear into their surroundings. Over millions of years, snakes have developed countless strategies to avoid becoming prey. Their survival is not just about hunting — it is about mastering the art of staying alive.",
"outro": "Every creature carries millions of years of survival secrets. Follow for more.",
"tags": ["#wildlife", "#snakes", "#nature", "#reptiles", "#shorts"],
"hashtags": "#wildlife #snakes #nature #animals #reptiles #shorts",
"keywords": [
"snake in forest",
"snake in forest","snake in forest","snake in forest","snake in forest","snake in forest","snake in forest","snake in forest"
],
"music": "dramatic"
}

]


# ─────────────────────────────────────────────
# BEST NEURAL VOICES — authoritative & clear
# ─────────────────────────────────────────────
VOICES = [
    #"en-US-AndrewNeural",   # deep, confident male — best for facts/psychology
    #"en-US-BrianNeural",    # calm, storytelling tone
    "en-US-EmmaNeural",     # warm, engaging female
    #"en-GB-RyanNeural",     # British male — sounds premium/authoritative
    #"en-GB-SoniaNeural",    # British female — very clear
    #"en-IN-NeerjaNeural",      # Indian female — warm, clear, very natural
    #"en-IN-PrabhatNeural",     # Indian male — confident, authoritative
    #"en-IN-NeerjaExpressiveNeural",  # Indian female — more expressive/emotional
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

    if os.path.exists(cache_file) and os.path.getsize(cache_file) > 10_000:
        print(f"  Using cached '{mood}' music.")
        return cache_file

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


def get_pexels_videos(keywords: list, count: int = 8, shuffle: bool = False) -> list:
    """
    Fetch one clip per keyword slot (up to `count` slots) in parallel.
    Returns a list where position[i] corresponds to keyword[i].
    """
    slots = list(keywords[:count])
    if PEXELS_API_KEY == "YOUR_KEY_HERE":
        return [None] * len(slots)

    if shuffle:
        random.shuffle(slots)

    headers  = {"Authorization": PEXELS_API_KEY}
    used_ids: set = set()
    used_lock     = threading.Lock()
    paths         = [None] * len(slots)

    def _fetch_slot(i: int, keyword: str):
        print(f"  Searching Pexels [{i + 1}/{len(slots)}]: '{keyword}'")
        url = (f"https://api.pexels.com/videos/search"
               f"?query={requests.utils.quote(keyword)}&per_page=15&orientation=portrait")
        try:
            r = requests.get(url, headers=headers, timeout=15)
            r.raise_for_status()
            videos = r.json().get("videos", [])
        except Exception as e:
            print(f"  Pexels error for slot {i + 1}: {e}")
            return i, None

        random.shuffle(videos)
        for v in videos:
            vid_id = v.get("id")
            with used_lock:
                if vid_id in used_ids or v.get("duration", 0) < 8:
                    continue
            files = sorted(v.get("video_files", []),
                           key=lambda f: f.get("height", 0), reverse=True)
            for f in files:
                if f.get("height", 0) >= 720:
                    out = os.path.join(OUTPUT_DIR, f"_tmp_bg_{i}.mp4")
                    try:
                        with requests.get(f["link"], stream=True, timeout=90) as resp:
                            resp.raise_for_status()
                            with open(out, "wb") as fh:
                                for chunk in resp.iter_content(65536):
                                    fh.write(chunk)
                        with used_lock:
                            used_ids.add(vid_id)
                        print(f"  Clip {i + 1} ready.")
                        return i, out
                    except Exception as e:
                        print(f"  Download failed (slot {i + 1}): {e}")
                        break

        print(f"  No result for slot {i + 1} ('{keyword}') — colour fallback will be used.")
        return i, None

    print(f"  Downloading {len(slots)} Pexels clips in parallel...")
    with ThreadPoolExecutor(max_workers=min(8, len(slots))) as executor:
        futures = {executor.submit(_fetch_slot, i, kw): i for i, kw in enumerate(slots)}
        for future in as_completed(futures):
            i, path = future.result()
            paths[i] = path

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


def _fast_resize(img: np.ndarray, w: int, h: int) -> np.ndarray:
    """Resize using cv2 (fast) with PIL BILINEAR as fallback."""
    try:
        import cv2
        return cv2.resize(img, (w, h), interpolation=cv2.INTER_LINEAR)
    except ImportError:
        from PIL import Image
        return np.array(Image.fromarray(img).resize((w, h), Image.BILINEAR))


def _detect_encoder() -> str:
    """Return the best available hardware H.264 encoder, falling back to libx264."""
    import subprocess
    # Preference order: Apple → NVIDIA → AMD → Intel → software
    HW_ENCODERS = ['h264_videotoolbox', 'h264_nvenc', 'h264_amf', 'h264_qsv']
    try:
        r = subprocess.run(['ffmpeg', '-hide_banner', '-encoders'],
                           capture_output=True, text=True, timeout=5)
        for enc in HW_ENCODERS:
            if enc in r.stdout:
                return enc
    except Exception:
        pass
    return 'libx264'


def _fallback_font() -> str:
    """Return a bold system font path that exists on the current OS."""
    import platform
    system = platform.system()
    candidates = {
        'Darwin':  '/System/Library/Fonts/Supplemental/Arial Bold.ttf',
        'Windows': 'C:/Windows/Fonts/arialbd.ttf',
        'Linux':   '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
    }
    path = candidates.get(system, '')
    if path and os.path.exists(path):
        return path
    # Last-resort: let moviepy/ImageMagick pick any available font
    return 'Arial-Bold'


def _apply_zoom(clip, start_scale=1.0, end_scale=1.08):
    """Smooth zoom between start_scale and end_scale over the clip's duration."""

    def effect(get_frame, t):
        img = get_frame(t)
        progress = t / max(clip.duration, 0.001)
        scale = start_scale + (end_scale - start_scale) * progress
        h, w = img.shape[:2]
        new_h, new_w = int(h * scale), int(w * scale)
        resized = _fast_resize(img, new_w, new_h)
        y1 = (new_h - h) // 2
        x1 = (new_w - w) // 2
        return resized[y1:y1 + h, x1:x1 + w]

    return clip.transform(effect)


def _apply_pan(clip, direction="left", amount=0.06):
    """Horizontal pan — slides a cropped window left or right, then resizes back."""

    def effect(get_frame, t):
        img = get_frame(t)
        progress = t / max(clip.duration, 0.001)
        h, w = img.shape[:2]
        crop_w = int(w * (1 - amount))
        max_offset = w - crop_w
        x1 = int(max_offset * progress) if direction == "left" else int(max_offset * (1 - progress))
        cropped = img[:, x1:x1 + crop_w, :]
        return _fast_resize(cropped, w, h)

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


def pop_in(clip, pop_duration=0.08, peak_scale=1.15):
    """
    Scale-pop animation: clip starts at peak_scale and eases to 1.0
    over pop_duration seconds. Gives captions a punchy CapCut-style entrance.
    """
    from PIL import Image

    def effect(get_frame, t):
        frame = get_frame(t)
        if t >= pop_duration:
            return frame
        progress = t / pop_duration                    # 0 → 1
        scale    = peak_scale - (peak_scale - 1.0) * progress  # peak → 1.0
        h, w     = frame.shape[:2]
        new_h, new_w = int(h * scale), int(w * scale)
        pil = Image.fromarray(frame).resize((new_w, new_h), Image.LANCZOS)
        # Crop/pad back to original size from centre
        y1 = max(0, (new_h - h) // 2)
        x1 = max(0, (new_w - w) // 2)
        cropped = np.array(pil)[y1:y1 + h, x1:x1 + w]
        # If scale < 1 the crop may be smaller — pad with zeros
        if cropped.shape[0] < h or cropped.shape[1] < w:
            out = np.zeros((h, w, frame.shape[2]), dtype=np.uint8)
            out[:cropped.shape[0], :cropped.shape[1]] = cropped
            return out
        return cropped

    return clip.transform(effect)


def color_grade(clip):
    """
    Cinematic color grade: contrast boost + warm tint.
    Uses a precomputed LUT for fast per-frame table-lookup instead of float32 arithmetic.
    """
    _inp = np.arange(256, dtype=np.float32) / 255.0
    _base = np.clip(_inp * 1.10 - 0.05, 0.0, 1.0)
    _lut_r = np.clip(_base * 1.08 * 255, 0, 255).astype(np.uint8)
    _lut_g = np.clip(_base * 1.02 * 255, 0, 255).astype(np.uint8)
    _lut_b = np.clip(_base * 255, 0, 255).astype(np.uint8)

    def effect(get_frame, t):
        f = get_frame(t)
        return np.stack([_lut_r[f[:, :, 0]], _lut_g[f[:, :, 1]], _lut_b[f[:, :, 2]]], axis=2)
    return clip.transform(effect)


def transcribe_audio(audio_path: str) -> list:
    """
    Run Whisper on the voice audio and return a flat list of
    (word, start_sec, end_sec) tuples. Result is shared between
    section-boundary detection and caption generation so Whisper
    only runs once per video.
    """
    from faster_whisper import WhisperModel
    print("  Loading Whisper model...")
    model = WhisperModel("tiny", compute_type="int8")
    print("  Transcribing audio...")
    segments, _ = model.transcribe(audio_path, word_timestamps=True)
    words = []
    for segment in segments:
        for word in segment.words:
            text = word.word.strip()
            if text:
                words.append((text, float(word.start), float(word.end)))
    print(f"  Transcription complete — {len(words)} words.")
    return words


def find_section_boundaries(all_words: list, script: dict) -> tuple:
    """
    Scan the transcript to find when 'story' and 'outro' sections begin.
    Matches the first 4 words of each section against the transcript.
    Falls back to proportional splits if a cue isn't found.
    Returns (story_start_sec, outro_start_sec).
    """
    import re

    narr_dur = all_words[-1][2] if all_words else 30

    def norm(s):
        return re.sub(r"[^a-z]", "", s.lower())

    def find_cue(cue_text):
        cue_words = [norm(w) for w in cue_text.split()[:3] if norm(w)]
        trans     = [(norm(w[0]), w[1]) for w in all_words]
        for i in range(len(trans) - len(cue_words) + 1):
            if all(trans[i + j][0] == cue_words[j] for j in range(len(cue_words))):
                return trans[i][1]
        return None

    story_start = find_cue(script["story"])
    outro_start = find_cue(script["outro"])

    if story_start is None:
        print("  WARNING: story cue not found — using proportional split.")
        story_start = narr_dur * 0.20
    if outro_start is None:
        print("  WARNING: outro cue not found — using proportional split.")
        outro_start = narr_dur * 0.85

    print(f"  Sections — hook: 0–{story_start:.1f}s | story: {story_start:.1f}–{outro_start:.1f}s | outro: {outro_start:.1f}–{narr_dur:.1f}s")
    return story_start, outro_start


def build_caption_clips(all_words: list) -> list:
    """
    Build per-word TextClips with pop-in animation from a pre-transcribed
    word list. Called after transcribe_audio() so Whisper isn't run twice.
    """
    from moviepy import TextClip

    font  = FONT_PATH if os.path.exists(FONT_PATH) else _fallback_font()
    clips = []

    for text, start, end in all_words:
        duration = max(0.10, (end - start) - 0.03)
        try:
            txt = (
                TextClip(
                    text=text.upper(),
                    font_size=88,
                    color="#FFE600",
                    stroke_color="black",
                    stroke_width=6,
                    font=font,
                    method="label",
                )
                .with_start(start + 0.4)
                .with_duration(duration + 0.05)
                .with_position(("center", 1450))
            )
            clips.append(txt)
        except Exception as e:
            print(f"  Subtitle error: {e}")

    print(f"  {len(clips)} caption clips created.")
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

    import time
    _start = time.time()

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

    # ── Transcribe early — shared by section detection + captions ──
    all_words = transcribe_audio(voice_path)
    story_start, outro_start = find_section_boundaries(all_words, script)
    narr_dur = audio.duration

    # ── Background music (auto-selected by mood) ──
    mood       = detect_mood(script)
    music_path = fetch_music(mood)
    FADE_OUT = 1.5  # shared fade duration for audio and video
    from moviepy.audio.fx import AudioFadeOut
    voice = audio.with_start(title_duration).with_effects([AudioFadeOut(FADE_OUT)])

    if music_path:
        print(f"  Adding '{mood}' background music...")
        music = AudioFileClip(music_path)
        if music.duration < duration:
            loops = int(duration / music.duration) + 1
            from moviepy import concatenate_audioclips
            music = concatenate_audioclips([music] * loops)
        music = (
            music.subclipped(0, duration)
            .with_volume_scaled(0.12)
            .with_effects([AudioFadeOut(FADE_OUT)])
        )
        final_audio = CompositeAudioClip([voice, music])
        print(f"  Background music mixed in at 12% volume, both tracks fade out over last {FADE_OUT}s.")
    else:
        print("  No background music found — proceeding without music.")
        final_audio = voice

    # ── Background video ──
    bg_paths        = get_pexels_videos(script["keywords"], count=8, shuffle=False)
    fallback_colors = [(10, 4, 30), (8, 20, 12), (22, 8, 4), (4, 8, 25)]
    TRANSITION      = 0.4  # crossfade duration between scenes (seconds)

    # Section-aware durations: hook | story pt1 | story pt2 | outro
    # Add TRANSITION buffer to each so crossfade overlaps don't shorten total
    _buf       = TRANSITION
    _story_mid = (story_start + outro_start) / 2
    MIN_CLIP = 5.0  # no section clip shorter than this — prevents a rushed hook
    _story_q1 = story_start + (outro_start - story_start) * 0.25
    _story_q2 = story_start + (outro_start - story_start) * 0.50
    _story_q3 = story_start + (outro_start - story_start) * 0.75
    section_durs = [
    max(MIN_CLIP, story_start * 0.5              + _buf),   # hook pt1
    max(MIN_CLIP, story_start * 0.5              + _buf),   # hook pt2
    max(MIN_CLIP, _story_q1  - story_start       + _buf),   # story pt1
    max(MIN_CLIP, _story_q2  - _story_q1         + _buf),   # story pt2
    max(MIN_CLIP, _story_q3  - _story_q2         + _buf),   # story pt3
    max(MIN_CLIP, outro_start - _story_q3        + _buf),   # story pt4
    max(MIN_CLIP, (narr_dur - outro_start) * 0.5 + _buf),   # outro pt1
    max(MIN_CLIP, (narr_dur - outro_start) * 0.5 + _buf),   # outro pt2
]

    def _crop_and_process(path: str, seg_duration: float):
        """Load one clip, loop/trim to seg_duration, crop to 9:16, apply one smooth camera move."""
        raw = VideoFileClip(path, audio=False)
        if raw.duration < seg_duration:
            n   = int(seg_duration / raw.duration) + 1 if raw.duration > 0 else 2
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
        resized = raw.resized((VIDEO_W, VIDEO_H))
        move = random.choice(["zoom_in", "zoom_out", "pan_left", "pan_right"])
        if move == "zoom_in":
            return _apply_zoom(resized, start_scale=1.0, end_scale=1.05)
        elif move == "zoom_out":
            return _apply_zoom(resized, start_scale=1.05, end_scale=1.0)
        elif move == "pan_left":
            return _apply_pan(resized, direction="left", amount=0.04)
        else:
            return _apply_pan(resized, direction="right", amount=0.04)

    if bg_paths:
        n           = len(bg_paths)
        paired_durs = [section_durs[i % len(section_durs)] for i in range(n)]
        print(f"  Building {n} section-matched clip(s) with {TRANSITION}s dissolves...")
        segments = []
        for i, (p, d) in enumerate(zip(bg_paths, paired_durs)):
            kw = script["keywords"][i] if i < len(script["keywords"]) else "—"
            if p is not None:
                print(f"    Slot {i + 1}: '{kw}' — video ({d:.1f}s)")
                segments.append(_crop_and_process(p, d))
            else:
                print(f"    Slot {i + 1}: '{kw}' — colour fallback ({d:.1f}s)")
                segments.append(
                    ColorClip((VIDEO_W, VIDEO_H),
                               color=fallback_colors[i % len(fallback_colors)])
                    .with_duration(d)
                )
        base = color_grade(crossfade_concat(segments, TRANSITION)).with_duration(duration)
        print(f"  {n} section-matched scenes assembled.")
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
    font = FONT_PATH if os.path.exists(FONT_PATH) else _fallback_font()
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

    # ── Karaoke captions (reuse already-transcribed words — no second Whisper run) ──
    print("  Generating caption clips...")
    text_clips = build_caption_clips(all_words)
    text_clips = [c.with_start(c.start + title_duration) for c in text_clips]

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
    from moviepy.video.fx import FadeOut
    layers = [base, dark_overlay, title_bg, title_clip] + text_clips + [watermark]
    print("  Compositing and exporting (this takes 1-3 min)...")
    final = (
        CompositeVideoClip(layers, size=(VIDEO_W, VIDEO_H))
        .with_duration(duration)
        .with_effects([FadeOut(FADE_OUT)])
        .with_audio(final_audio)
    )

    encoder = _detect_encoder()
    HW_ENCODER_NAMES = {
        'h264_videotoolbox': 'Apple VideoToolbox',
        'h264_nvenc':        'NVIDIA NVENC',
        'h264_amf':          'AMD AMF',
        'h264_qsv':          'Intel Quick Sync',
    }
    if encoder in HW_ENCODER_NAMES:
        print(f"  Encoding with {HW_ENCODER_NAMES[encoder]} (hardware accelerated)...")
        final.write_videofile(
            out_path,
            fps=FPS,
            codec=encoder,
            audio_codec='aac',
            bitrate='8000k',
            threads=os.cpu_count() or 4,
            ffmpeg_params=['-allow_sw', '1'] if encoder == 'h264_videotoolbox' else [],
            logger=None,
        )
    else:
        print("  Encoding with libx264 (no hardware encoder found)...")
        final.write_videofile(
            out_path,
            fps=FPS,
            codec='libx264',
            audio_codec='aac',
            bitrate='8000k',
            threads=os.cpu_count() or 4,
            preset='faster',
            logger=None,
        )

    # Cleanup
    for tmp in ["_tmp_voice.mp3"] + [f"_tmp_bg_{i}.mp4" for i in range(8)]:
        p = os.path.join(OUTPUT_DIR, tmp)
        if os.path.exists(p):
            os.remove(p)

    elapsed = time.time() - _start
    mins, secs = divmod(int(elapsed), 60)
    print(f"\n  Saved: {os.path.abspath(out_path)}")
    print(f"  Generation time: {mins}m {secs}s")
    return out_path


def main():
    print("\n" + "=" * 52)
    print("  YouTube Shorts Bot")
    print("=" * 52)

    setup_font()

    if PEXELS_API_KEY == "YOUR_KEY_HERE":
        print("\n  NOTE: No Pexels key found.")
        print("  Get one FREE at: https://www.pexels.com/api/")
        print("  Videos will use colour backgrounds for now.\n")

    import time
    day        = datetime.now().timetuple().tm_yday
    made       = []
    total_start = time.time()

    for i in range(SHORTS_PER_DAY):
        script = SCRIPTS[(day - 1 + i) % len(SCRIPTS)]
        try:
            path = make_short(script, i)
            made.append(path)
        except Exception as e:
            print(f"\n  ERROR on Short {i + 1}: {e}")
            import traceback; traceback.print_exc()

    total_elapsed = time.time() - total_start
    total_mins, total_secs = divmod(int(total_elapsed), 60)

    print(f"\n{'=' * 52}")
    print(f"  COMPLETE — {len(made)} Short(s) ready!")
    print(f"  Total time: {total_mins}m {total_secs}s")
    print(f"  Folder: {os.path.abspath(OUTPUT_DIR)}")
    print(f"  Upload to YouTube Shorts and you're done.")
    print(f"{'=' * 52}\n")


if __name__ == "__main__":
    main()
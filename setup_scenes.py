"""
Run this cell ONCE per Kaggle session before starting ComfyUI.
Reads audio files, calculates frames, detects lip sync, writes scenes.json.
"""

import json
import math
import os
import subprocess

# ── CONFIG ────────────────────────────────────────────────────────────────────
IMAGE_FOLDER  = "/kaggle/working/ComfyUI/output"
AUDIO_FOLDER  = "/kaggle/working/ComfyUI/input/audio"
SCENES_JSON   = "/kaggle/working/ComfyUI/input/scenes.json"
FPS           = 24

# ── SCENE DEFINITIONS ─────────────────────────────────────────────────────────
# (scene_id, image_filename, audio_filename, output_name)
# Naming convention:
#   "narrator" in audio filename → lip_sync=0 (no mouth movement)
#   character name in filename   → lip_sync=1 (that character speaks)

SCENE_DEFS = [
    (1, "scene_01_00001_.png", "1_narrator.mp3",     "scene_01"),
    (2, "scene_02_00001_.png", "2_narrator.mp3",     "scene_02"),
    (3, "scene_03_00001_.png", "3_narrator.mp3",     "scene_03"),
    (4, "scene_04_00001_.png", "4_Rahul.wav",         "scene_04"),
    (5, "scene_05_00001_.png", "5_narrator.mp3",     "scene_05"),
    (6, "scene_06_00001_.png", "6_narrator.mp3",     "scene_06"),
    (7, "scene_07_00001_.png", "7_Grandfather.wav",  "scene_07"),
    (8, "scene_08_00001_.png", "8_narrator.mp3",     "scene_08"),
]

# ── HELPERS ───────────────────────────────────────────────────────────────────

def get_audio_duration(audio_path):
    """Get exact audio duration in seconds using ffprobe."""
    result = subprocess.run([
        'ffprobe', '-v', 'quiet',
        '-print_format', 'json',
        '-show_streams', audio_path
    ], capture_output=True, text=True)

    try:
        info = json.loads(result.stdout)
        for stream in info.get('streams', []):
            if 'duration' in stream:
                return float(stream['duration'])
    except Exception:
        pass

    # Fallback: format duration
    result2 = subprocess.run([
        'ffprobe', '-v', 'quiet',
        '-print_format', 'json',
        '-show_format', audio_path
    ], capture_output=True, text=True)

    info2 = json.loads(result2.stdout)
    return float(info2['format']['duration'])


def calc_frames(duration_seconds, fps=24):
    """
    Calculate valid LTX frame count from audio duration.
    Formula: frames = ceil(duration × fps) rounded UP to nearest (8n + 1)
    Valid values: 65, 73, 81, 89, 97, 105, 113, 121, 129, 137, 145, 153, 161, 169...
    """
    raw_frames = duration_seconds * fps
    n = math.ceil((raw_frames - 1) / 8)
    return int(n * 8 + 1)


def detect_lip_sync(audio_filename):
    """
    Detect lip sync from audio filename.
    'narrator' → lip_sync=0, character name → lip_sync=1
    """
    stem = os.path.splitext(audio_filename)[0]  # e.g. "7_Grandfather"
    parts = stem.split('_', 1)
    char_part = parts[1] if len(parts) > 1 else stem

    if 'narrator' in audio_filename.lower():
        return 0, 'narrator'
    else:
        return 1, char_part


# ── MAIN ──────────────────────────────────────────────────────────────────────

print("=" * 55)
print("  LTX Scene Setup — Calculating frames from audio")
print("=" * 55)

os.makedirs(os.path.dirname(SCENES_JSON), exist_ok=True)

scenes        = []
total_dur     = 0
missing_audio = []
missing_image = []

for scene_id, image_file, audio_file, output_name in SCENE_DEFS:

    audio_path = os.path.join(AUDIO_FOLDER, audio_file)
    image_path = os.path.join(IMAGE_FOLDER, image_file)

    # Check files
    if not os.path.exists(audio_path):
        missing_audio.append(audio_file)
        print(f"⚠️  Scene {scene_id}: Audio not found → using default 169 frames")
        duration = 7.0
        frames   = 169
    else:
        duration = get_audio_duration(audio_path)
        frames   = calc_frames(duration)

    if not os.path.exists(image_path):
        missing_image.append(image_file)

    lip_sync, character = detect_lip_sync(audio_file)
    total_dur += duration

    scenes.append({
        "id":        scene_id,
        "image":     image_file,
        "audio":     audio_file,
        "frames":    frames,
        "output":    output_name,
        "lip_sync":  lip_sync,
        "character": character
    })

    lip_str = f"💬 {character}" if lip_sync else "🔇 narrator"
    print(f"  Scene {scene_id}: {audio_file}")
    print(f"    {duration:.2f}s → {frames} frames | {lip_str}")

# Write scenes.json
with open(SCENES_JSON, 'w') as f:
    json.dump({"scenes": scenes}, f, indent=2)

# Summary
print()
print("=" * 55)
print(f"✅ scenes.json written → {SCENES_JSON}")
print(f"   Total scenes:   {len(scenes)}")
print(f"   Total duration: {total_dur:.1f}s ({total_dur/60:.1f} mins)")
print(f"   Est. gen time:  ~{total_dur * 1.75 / 60:.1f} hours on T4")

if missing_audio:
    print(f"\n⚠️  Missing audio files: {missing_audio}")
    print(f"   Place them in: {AUDIO_FOLDER}")

if missing_image:
    print(f"\n⚠️  Missing image files: {missing_image}")
    print(f"   Place them in: {IMAGE_FOLDER}")

print()
print("Scene summary:")
print(f"  {'ID':<4} {'Output':<12} {'Frames':<8} {'Dur':<8} {'Type'}")
print(f"  {'-'*48}")
for s in scenes:
    t   = f"💬 {s['character']}" if s['lip_sync'] else "🔇 narrator"
    dur = round(s['frames'] / FPS, 1)
    print(f"  {s['id']:<4} {s['output']:<12} {s['frames']:<8} {dur}s{'':<4} {t}")

"""
KAGGLE SETUP CELL — Run this BEFORE starting ComfyUI
=====================================================
This cell:
1. Reads all audio files from input folder
2. Calculates exact frame count per scene (audio_seconds × 24, rounded to 8n+1)
3. Detects lip_sync from filename (narrator=0, character name=1)
4. Writes updated scenes.json ready for the workflow
"""

import json
import math
import os
import subprocess

# ── CONFIG ────────────────────────────────────────────────────────────────────
AUDIO_FOLDER  = "/kaggle/working/ComfyUI/input/audio"   # audio files here
IMAGE_FOLDER  = "/kaggle/working/ComfyUI/output"         # images here
SCENES_JSON   = "/kaggle/working/ComfyUI/input/scenes.json"
FPS           = 24

# ── SCENE DEFINITIONS ─────────────────────────────────────────────────────────
# Format: (scene_id, image_file, audio_file, output_name)
# Audio filename convention:
#   "narrator" in name → lip_sync=0 (no mouth movement)
#   character name     → lip_sync=1 (mouth movement for that character)

SCENE_DEFS = [
    (1, "scene_01_00001_.png", "1_narrator.mp3",    "scene_01"),
    (2, "scene_02_00001_.png", "2_narrator.mp3",    "scene_02"),
    (3, "scene_03_00001_.png", "3_narrator.mp3",    "scene_03"),
    (4, "scene_04_00001_.png", "4_Rahul.wav",        "scene_04"),
    (5, "scene_05_00001_.png", "5_narrator.mp3",    "scene_05"),
    (6, "scene_06_00001_.png", "6_narrator.mp3",    "scene_06"),
    (7, "scene_07_00001_.png", "7_Grandfather.wav", "scene_07"),
    (8, "scene_08_00001_.png", "8_narrator.mp3",    "scene_08"),
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
    except:
        pass

    # Fallback: use format duration
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
    
    Formula:
        raw_frames = duration × fps
        frames = ceil(raw_frames) rounded UP to nearest (8n + 1)
    
    LTX requirement: frames must satisfy frames = 8n + 1
    Examples: 65, 73, 81, 89, 97, 105, 113, 121, 129, 137, 145, 153, 161, 169...
    """
    raw_frames = duration_seconds * fps
    # Find smallest valid 8n+1 that is >= raw_frames
    n = math.ceil((raw_frames - 1) / 8)
    frames = int(n * 8 + 1)
    return frames


def detect_lip_sync(audio_filename):
    """
    Detect whether lip sync is needed from audio filename.
    
    Convention:
        "narrator" in filename → lip_sync = 0 (no mouth movement)
        character name present → lip_sync = 1 (character speaks)
    
    Returns: (lip_sync: int, character: str)
    """
    name_lower = audio_filename.lower()

    # Remove extension and number prefix
    stem = os.path.splitext(audio_filename)[0]  # e.g. "7_Grandfather"
    # Remove leading number and underscore
    parts = stem.split('_', 1)
    char_part = parts[1] if len(parts) > 1 else stem

    if 'narrator' in name_lower:
        return 0, 'narrator'
    else:
        # Character name is the part after the number
        return 1, char_part


# ── MAIN ──────────────────────────────────────────────────────────────────────

print("=" * 55)
print("Auto-calculating frames from audio files...")
print("=" * 55)

scenes = []
total_duration = 0

for scene_id, image_file, audio_file, output_name in SCENE_DEFS:
    audio_path = os.path.join(AUDIO_FOLDER, audio_file)

    # Check audio exists
    if not os.path.exists(audio_path):
        print(f"⚠️  Scene {scene_id}: Audio not found → {audio_path}")
        print(f"   Using default 169 frames")
        duration = 7.0
        frames = 169
    else:
        duration = get_audio_duration(audio_path)
        frames = calc_frames(duration)

    # Detect lip sync from filename
    lip_sync, character = detect_lip_sync(audio_file)

    total_duration += duration

    scene = {
        "id": scene_id,
        "image": image_file,
        "audio": audio_file,
        "frames": frames,
        "output": output_name,
        "lip_sync": lip_sync,
        "character": character
    }
    scenes.append(scene)

    lip_str = f"💬 {character} speaks" if lip_sync else "🔇 narrator (no lip sync)"
    print(f"Scene {scene_id}: {audio_file}")
    print(f"  Duration: {duration:.2f}s  →  {frames} frames  |  {lip_str}")

# Write scenes.json
scenes_data = {"scenes": scenes}
os.makedirs(AUDIO_FOLDER, exist_ok=True)
os.makedirs(IMAGE_FOLDER, exist_ok=True)
os.makedirs(os.path.dirname(SCENES_JSON), exist_ok=True)

with open(SCENES_JSON, 'w') as f:
    json.dump(scenes_data, f, indent=2)

print()
print("=" * 55)
print(f"✅ scenes.json written to: {SCENES_JSON}")
print(f"📊 Total scenes: {len(scenes)}")
print(f"⏱️  Total audio duration: {total_duration:.1f}s ({total_duration/60:.1f} mins)")
print(f"🎬 Estimated generation time: {total_duration * 1.75 / 60:.1f} hours (at 1.75 min/sec)")
print()
print("Scenes summary:")
print(f"  {'ID':<4} {'Output':<12} {'Frames':<8} {'Duration':<10} {'Type'}")
print(f"  {'-'*50}")
for s in scenes:
    t = f"💬 {s['character']}" if s['lip_sync'] else "🔇 narrator"
    dur = s['frames'] / FPS
    print(f"  {s['id']:<4} {s['output']:<12} {s['frames']:<8} {dur:.1f}s{'':<6} {t}")

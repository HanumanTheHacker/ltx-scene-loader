"""
Run this cell ONCE per Kaggle session before starting ComfyUI.
Auto-detects audio and image files by scene number.
No manual SCENE_DEFS needed — just add files to the folders.
"""

import json
import math
import os
import re
import subprocess
import glob

# ── CONFIG ────────────────────────────────────────────────────────────────────
IMAGE_FOLDER  = "/kaggle/working/ComfyUI/output"
AUDIO_FOLDER  = "/kaggle/working/ComfyUI/input/audio"
SCENES_JSON   = "/kaggle/working/ComfyUI/input/scenes.json"
FPS           = 24

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
    'narrator' in name → lip_sync=0 (no mouth movement)
    anything else      → lip_sync=1 (character speaks)
    """
    stem = os.path.splitext(audio_filename)[0]  # e.g. "7_Grandfather"
    parts = stem.split('_', 1)
    char_part = parts[1] if len(parts) > 1 else stem

    if 'narrator' in audio_filename.lower():
        return 0, 'narrator'
    else:
        return 1, char_part


def extract_number(filename):
    """Extract the leading number from a filename. e.g. '3_narrator.mp3' → 3"""
    match = re.match(r'^(\d+)', os.path.basename(filename))
    return int(match.group(1)) if match else None


def find_image_for_scene(scene_num, image_folder):
    """
    Find image file matching scene number.
    Looks for files like: scene_01_00001_.png, scene_1_*.png etc.
    Returns (filename, full_path) or (None, None)
    """
    # Try common patterns
    patterns = [
        f"scene_{scene_num:02d}_*.png",
        f"scene_{scene_num}_*.png",
        f"scene_{scene_num:02d}.png",
        f"scene_{scene_num}.png",
        f"*scene*{scene_num:02d}*.png",
        f"*scene*{scene_num}*.png",
    ]
    for pattern in patterns:
        matches = glob.glob(os.path.join(image_folder, pattern))
        if matches:
            # Pick first match, prefer _00001_ pattern
            matches.sort()
            return os.path.basename(matches[0]), matches[0]
    return None, None


# ── AUTO-DETECT AUDIO FILES ───────────────────────────────────────────────────

print("=" * 55)
print("  LTX Scene Setup — Auto-detecting files")
print("=" * 55)

os.makedirs(os.path.dirname(SCENES_JSON), exist_ok=True)
os.makedirs(AUDIO_FOLDER, exist_ok=True)
os.makedirs(IMAGE_FOLDER, exist_ok=True)

# Find all audio files
audio_extensions = ['*.mp3', '*.wav', '*.flac', '*.aac', '*.ogg']
all_audio = []
for ext in audio_extensions:
    all_audio.extend(glob.glob(os.path.join(AUDIO_FOLDER, ext)))

# Extract scene number from each audio file and build map
audio_map = {}  # scene_num → (filename, full_path)
for audio_path in all_audio:
    num = extract_number(audio_path)
    if num is not None:
        filename = os.path.basename(audio_path)
        audio_map[num] = (filename, audio_path)

if not audio_map:
    print("❌ No audio files found in:", AUDIO_FOLDER)
    print("   Expected files like: 1_narrator.mp3, 2_narrator.mp3, etc.")
else:
    print(f"✅ Found {len(audio_map)} audio file(s):")
    for num in sorted(audio_map.keys()):
        print(f"   Scene {num}: {audio_map[num][0]}")

print()

# ── BUILD SCENES ──────────────────────────────────────────────────────────────

scenes        = []
total_dur     = 0
missing_image = []
missing_audio = []

for scene_num in sorted(audio_map.keys()):
    audio_file, audio_path = audio_map[scene_num]

    # Find matching image
    image_file, image_path = find_image_for_scene(scene_num, IMAGE_FOLDER)

    if image_file is None:
        missing_image.append(f"scene_{scene_num:02d}_*.png")
        image_file = f"scene_{scene_num:02d}_00001_.png"  # fallback name

    # Get duration and calculate frames
    duration = get_audio_duration(audio_path)
    frames   = calc_frames(duration)
    total_dur += duration

    # Detect lip sync
    lip_sync, character = detect_lip_sync(audio_file)

    output_name = f"scene_{scene_num:02d}"

    scenes.append({
        "id":        scene_num,
        "image":     image_file,
        "audio":     audio_file,
        "frames":    frames,
        "output":    output_name,
        "lip_sync":  lip_sync,
        "character": character
    })

    img_status = "✅" if image_path else "⚠️ "
    lip_str    = f"💬 {character}" if lip_sync else "🔇 narrator"
    print(f"Scene {scene_num:02d}: {audio_file}")
    print(f"  Audio:  {duration:.2f}s → {frames} frames | {lip_str}")
    print(f"  Image:  {img_status} {image_file}")

# ── WRITE scenes.json ─────────────────────────────────────────────────────────

with open(SCENES_JSON, 'w') as f:
    json.dump({"scenes": scenes}, f, indent=2)

# ── SUMMARY ───────────────────────────────────────────────────────────────────

print()
print("=" * 55)
print(f"✅ scenes.json → {SCENES_JSON}")
print(f"   Total scenes:    {len(scenes)}")
print(f"   Total duration:  {total_dur:.1f}s ({total_dur/60:.1f} mins)")
print(f"   Est. gen time:   ~{total_dur * 1.75 / 60:.1f} hours on T4")

if missing_image:
    print(f"\n⚠️  Images not found:")
    for f in missing_image:
        print(f"   {f} — place in: {IMAGE_FOLDER}")

print()
print("Scene summary:")
print(f"  {'ID':<5} {'Output':<12} {'Frames':<8} {'Dur':<8} {'Audio':<25} {'Type'}")
print(f"  {'-'*65}")
for s in scenes:
    t   = f"💬 {s['character']}" if s['lip_sync'] else "🔇 narrator"
    dur = round(s['frames'] / FPS, 1)
    print(f"  {s['id']:<5} {s['output']:<12} {s['frames']:<8} {dur}s{'':<4} {s['audio']:<25} {t}")

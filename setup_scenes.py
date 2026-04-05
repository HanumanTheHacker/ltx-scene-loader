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
    Formula: ceil(duration_seconds) x fps + 1
    Example: 2.4s -> 3x24+1 = 73 frames
    Example: 7.0s -> 7x24+1 = 169 frames
    """
    # return math.ceil(duration_seconds) * fps + 1
    return math.ceil(duration_seconds)


def detect_lip_sync(audio_filename):
    """
    Detect lip sync from audio filename.
    'narrator' in name → lip_sync=0 (no mouth movement)
    anything else      → lip_sync=1 (character speaks)
    """
    stem      = os.path.splitext(audio_filename)[0]
    parts     = stem.split('_', 1)
    char_part = parts[1] if len(parts) > 1 else stem

    if 'narrator' in audio_filename.lower():
        return 0, 'narrator'
    else:
        return 1, char_part


def extract_number(filename):
    """Extract the leading number from a filename. e.g. '3_narrator.mp3' → 3"""
    match = re.match(r'^(\d+)', os.path.basename(filename))
    return int(match.group(1)) if match else None


# def find_image_for_scene(scene_num, image_folder):
#     """
#     Find image file matching scene number.
#     Tries: scene_01_00001_.png, scene_01.png, *scene*01*.png etc.
#     Returns (filename, full_path) or (None, None).
#     """
#     patterns = [
#         f"scene_{scene_num:02d}_*.png",
#         f"scene_{scene_num}_*.png",
#         f"scene_{scene_num:02d}.png",
#         f"scene_{scene_num}.png",
#         f"*scene*{scene_num:02d}*.png",
#         f"*scene*{scene_num}*.png",
#     ]
#     for pattern in patterns:
#         matches = glob.glob(os.path.join(image_folder, pattern))
#         if matches:
#             matches.sort()
#             return os.path.basename(matches[0]), matches[0]
#     return None, None


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

# ── FIND ALL AVAILABLE IMAGES ─────────────────────────────────────────────────

# Find all scene images and extract their numbers
image_files = glob.glob(os.path.join(IMAGE_FOLDER, "scene_*.png"))
image_map_by_num = {}

for img_path in image_files:
    img_name = os.path.basename(img_path)
    # Try to extract scene number from filename (scene_0001_, scene_14_, etc.)
    match = re.match(r'^scene_(\d+)', img_name)
    if match:
        img_num = int(match.group(1))
        if img_num not in image_map_by_num:
            image_map_by_num[img_num] = (img_name, img_path)

# Get sorted list of available image numbers
sorted_img_nums = sorted(image_map_by_num.keys())

if sorted_img_nums:
    print(f"✅ Found {len(sorted_img_nums)} image(s) with scene numbers:")
    for num in sorted_img_nums:
        print(f"   Scene {num:04d}: {image_map_by_num[num][0]}")
    print()
else:
    print("❌ No scene images found in:", IMAGE_FOLDER)
    print()


# Skip already-padded files
all_audio = [f for f in all_audio if '_padded' not in os.path.basename(f)]

# Build scene_num → (filename, path) map
audio_map = {}
for audio_path in all_audio:
    num = extract_number(audio_path)
    if num is not None:
        audio_map[num] = (os.path.basename(audio_path), audio_path)

if not audio_map:
    print("❌ No audio files found in:", AUDIO_FOLDER)
    print("   Expected files like: 1_narrator.mp3, 2_narrator.mp3, etc.")
else:
    print(f"✅ Found {len(audio_map)} audio file(s):")
    for num in sorted(audio_map.keys()):
        print(f"   Scene {num}: {audio_map[num][0]}")

print()

# ── BUILD SCENES (SERIAL MAPPING) ─────────────────────────────────────────────

scenes        = []
total_dur     = 0
missing_image = []

# Map audio files serially to available images
for idx, scene_num in enumerate(sorted(audio_map.keys())):
    audio_file, audio_path = audio_map[scene_num]

    # Map to the idx-th available image (serial mapping)
    if idx < len(sorted_img_nums):
        actual_img_num = sorted_img_nums[idx]
        image_file, image_path = image_map_by_num[actual_img_num]
        img_status = "✅"
    else:
        # More audio files than images
        image_file = f"scene_{scene_num:02d}_00001_.png"
        image_path = None
        img_status = "⚠️ "
        missing_image.append(image_file)

    # Get raw duration
    duration = get_audio_duration(audio_path)

    # Calculate frames
    frames     = calc_frames(duration)
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

    lip_str = f"💬 {character}" if lip_sync else "🔇 narrator"
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
print(f"  {'ID':<5} {'Output':<12} {'Frames':<8} {'Dur':<8} {'Audio':<30} {'Type'}")
print(f"  {'-'*70}")
for s in scenes:
    t   = f"💬 {s['character']}" if s['lip_sync'] else "🔇 narrator"
    dur = round(s['frames'] / FPS, 1)
    print(f"  {s['id']:<5} {s['output']:<12} {s['frames']:<8} {dur}s{'':<4} {s['audio']:<30} {t}")

"""
KAGGLE CELL — Install LTXSceneLoader custom node (v2)
=====================================================
- image_path: full path (for LoadImageFromPath)
- audio_filename: just filename (for LoadAudio KJNodes)
- Also symlinks audio folder into ComfyUI input so LoadAudio can find files
"""

import os

NODE_DIR = '/kaggle/working/ComfyUI/custom_nodes/ltx_scene-loader'
os.makedirs(NODE_DIR, exist_ok=True)

node_code = '''
import json, os

class LTXSceneLoader:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "scenes_json_path": ("STRING", {
                    "default": "/kaggle/working/ComfyUI/input/scenes.json",
                    "multiline": False
                }),
                "image_folder": ("STRING", {
                    "default": "/kaggle/working/ComfyUI/output/",
                    "multiline": False
                }),
                "scene_index": ("INT", {
                    "default": 1, "min": 1, "max": 999, "step": 1
                }),
            }
        }

    # audio_filename is just the filename (e.g. "1_narrator.mp3")
    # LoadAudio (KJNodes) resolves it relative to ComfyUI input folder
    RETURN_TYPES  = ("STRING", "STRING", "INT", "INT", "INT")
    RETURN_NAMES  = ("image_path", "audio_filename", "frames", "lip_sync", "total_scenes")
    FUNCTION      = "load_scene"
    CATEGORY      = "LTX/Batch"
    OUTPUT_NODE   = False

    def load_scene(self, scenes_json_path, image_folder, scene_index):
        # Load JSON
        if not os.path.exists(scenes_json_path):
            raise FileNotFoundError(
                f"scenes.json not found at: {scenes_json_path}\\n"
                f"Run setup_scenes.py first."
            )

        with open(scenes_json_path) as f:
            data = json.load(f)

        scenes       = data.get("scenes", [])
        total_scenes = len(scenes)

        if total_scenes == 0:
            raise ValueError("scenes.json has no scenes defined")

        # Find scene by index (1-based)
        idx   = max(1, min(scene_index, total_scenes))
        scene = next((s for s in scenes if s["id"] == idx), scenes[idx - 1])

        # Full path for image (LoadImageFromPath needs full path)
        image_path     = image_folder.rstrip("/") + "/" + scene["image"]

        # Just filename for audio (LoadAudio resolves from ComfyUI input folder)
        audio_filename = scene["audio"]

        frames         = int(scene.get("frames",   169))
        lip_sync       = int(scene.get("lip_sync",   0))
        character      = scene.get("character", "narrator")

        print(f"[LTXSceneLoader] {idx}/{total_scenes} | {scene[chr(39)image chr(39)]} + {audio_filename} | {frames}f | {character if lip_sync else chr(39)narrator chr(39)}")

        return (image_path, audio_filename, frames, lip_sync, total_scenes)


NODE_CLASS_MAPPINGS        = {"LTXSceneLoader": LTXSceneLoader}
NODE_DISPLAY_NAME_MAPPINGS = {"LTXSceneLoader": "LTX Scene Loader 🎬"}
'''

# Fix the f-string issue with chr approach
node_code = '''
import json, os

class LTXSceneLoader:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "scenes_json_path": ("STRING", {
                    "default": "/kaggle/working/ComfyUI/input/scenes.json",
                    "multiline": False
                }),
                "image_folder": ("STRING", {
                    "default": "/kaggle/working/ComfyUI/output/",
                    "multiline": False
                }),
                "scene_index": ("INT", {
                    "default": 1, "min": 1, "max": 999, "step": 1
                }),
            }
        }

    RETURN_TYPES  = ("STRING", "STRING", "INT", "INT", "INT")
    RETURN_NAMES  = ("image_path", "audio_filename", "frames", "lip_sync", "total_scenes")
    FUNCTION      = "load_scene"
    CATEGORY      = "LTX/Batch"
    OUTPUT_NODE   = False

    def load_scene(self, scenes_json_path, image_folder, scene_index):
        if not os.path.exists(scenes_json_path):
            raise FileNotFoundError(f"scenes.json not found: {scenes_json_path}")

        with open(scenes_json_path) as f:
            data = json.load(f)

        scenes       = data.get("scenes", [])
        total_scenes = len(scenes)

        if total_scenes == 0:
            raise ValueError("scenes.json has no scenes defined")

        idx            = max(1, min(scene_index, total_scenes))
        scene          = next((s for s in scenes if s["id"] == idx), scenes[idx - 1])
        image_path     = image_folder.rstrip("/") + "/" + scene["image"]
        audio_filename = scene["audio"]   # filename only - LoadAudio resolves path
        frames         = int(scene.get("frames",   169))
        lip_sync       = int(scene.get("lip_sync",   0))
        character      = scene.get("character", "narrator")
        speaker        = character if lip_sync else "narrator"

        print(f"[LTXSceneLoader] Scene {idx}/{total_scenes}")
        print(f"  Image:  {image_path}")
        print(f"  Audio:  {audio_filename}")
        print(f"  Frames: {frames}  |  Speaker: {speaker}")

        return (image_path, audio_filename, frames, lip_sync, total_scenes)


NODE_CLASS_MAPPINGS        = {"LTXSceneLoader": LTXSceneLoader}
NODE_DISPLAY_NAME_MAPPINGS = {"LTXSceneLoader": "LTX Scene Loader 🎬"}
'''

init_code = '''
from .scene_loader_node import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
'''

with open(f'{NODE_DIR}/scene_loader_node.py', 'w') as f:
    f.write(node_code)

with open(f'{NODE_DIR}/__init__.py', 'w') as f:
    f.write(init_code)

# ── Symlink audio folder into ComfyUI input so LoadAudio can find files ───────
# LoadAudio resolves filenames relative to ComfyUI/input/
# Audio files are at ComfyUI/input/audio/
# We need them accessible as just "1_narrator.mp3" not "audio/1_narrator.mp3"

AUDIO_SRC = '/kaggle/working/ComfyUI/input/audio'
COMFY_INPUT = '/kaggle/working/ComfyUI/input'

if os.path.exists(AUDIO_SRC):
    import glob
    audio_files = glob.glob(f'{AUDIO_SRC}/*')
    print(f"\n📁 Found {len(audio_files)} audio files in {AUDIO_SRC}")
    for src_file in audio_files:
        filename = os.path.basename(src_file)
        dst_link = os.path.join(COMFY_INPUT, filename)
        if not os.path.exists(dst_link):
            os.symlink(src_file, dst_link)
            print(f"  🔗 Symlinked: {filename}")
        else:
            print(f"  ✅ Already exists: {filename}")
else:
    print(f"\n⚠️  Audio folder not found: {AUDIO_SRC}")
    print("   Create it and add your audio files before running setup_scenes.py")

print(f"\n✅ LTXSceneLoader installed at: {NODE_DIR}")
print("   Outputs:")
print("     image_path    → LoadImageFromPath  (full path)")
print("     audio_filename→ LoadAudio KJNodes  (filename only)")
print("     frames        → EmptyLTXVLatentVideo.length")
print("     lip_sync      → ImpactSwitch")
print("     total_scenes  → ImpactQueueTriggerCountdown")

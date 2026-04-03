"""
Run this cell ONCE per Kaggle session before starting ComfyUI.
Installs the LTXSceneLoader custom node.
"""

import os

NODE_DIR = '/kaggle/working/ComfyUI/custom_nodes/ltx-scene-loader'
os.makedirs(NODE_DIR, exist_ok=True)

# ── scene_loader_node.py ──────────────────────────────────────────────────────
node_code = """import json
import os


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
                "audio_folder": ("STRING", {
                    "default": "/kaggle/working/ComfyUI/input/audio/",
                    "multiline": False
                }),
                "scene_index": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": 999,
                    "step": 1
                }),
            }
        }

    RETURN_TYPES  = ("STRING", "STRING", "INT", "INT", "INT", "INT")
    RETURN_NAMES  = ("image_path", "audio_path", "frames", "lip_sync", "total_scenes", "id")
    FUNCTION      = "load_scene"
    CATEGORY      = "LTX/Batch"
    OUTPUT_NODE   = False

    def load_scene(self, scenes_json_path, image_folder, audio_folder, scene_index):

        if not os.path.exists(scenes_json_path):
            raise FileNotFoundError(
                f"scenes.json not found at: {scenes_json_path}\\n"
                f"Run setup_scenes.py first to generate it."
            )

        with open(scenes_json_path, 'r') as f:
            data = json.load(f)

        scenes       = data.get('scenes', [])
        total_scenes = len(scenes)

        if total_scenes == 0:
            raise ValueError("scenes.json has no scenes defined")

        idx   = max(1, min(scene_index, total_scenes))
        scene = next((s for s in scenes if s['id'] == idx), None)

        if scene is None:
            scene = scenes[idx - 1]

        image_path = image_folder.rstrip('/') + '/' + scene['image']
        audio_path = audio_folder.rstrip('/') + '/' + scene['audio']
        frames     = int(scene.get('frames',   169))
        lip_sync   = int(scene.get('lip_sync',   0))
        character  = scene.get('character', 'narrator')
        lip_str    = f"💬 {character} speaks" if lip_sync else "🔇 narrator"
        id         = int(scene.get('id',   0)) - 1

        print(f"\\n[LTXSceneLoader] Scene {idx}/{total_scenes}")
        print(f"  Image:    {image_path}")
        print(f"  Audio:    {audio_path}")
        print(f"  Frames:   {frames}")
        print(f"  Lip sync: {lip_str}")

        return (image_path, audio_path, frames, lip_sync, total_scenes, id)


NODE_CLASS_MAPPINGS = {
    "LTXSceneLoader": LTXSceneLoader
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LTXSceneLoader": "LTX Scene Loader 🎬"
}
"""

# ── __init__.py ───────────────────────────────────────────────────────────────
init_code = """from .scene_loader_node import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
"""

# Write files
with open(f'{NODE_DIR}/scene_loader_node.py', 'w') as f:
    f.write(node_code)

with open(f'{NODE_DIR}/__init__.py', 'w') as f:
    f.write(init_code)

print(f"✅ LTXSceneLoader installed at: {NODE_DIR}")
print()
print("Node outputs:")
print("  image_path   → LoadImageFromPath  (full image path)")
print("  audio_path   → VHS_LoadAudio      (full audio path)")
print("  frames       → EmptyLTXVLatentVideo.length")
print("  lip_sync     → ImpactSwitch       (0=narrator, 1=character)")
print("  total_scenes → ImpactQueueTriggerCountdown")
print()
print("⚠️  Restart ComfyUI after running this cell")

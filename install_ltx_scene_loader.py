"""
KAGGLE CELL — Install LTXSceneLoader custom node
=================================================
Run this once per session before starting ComfyUI
"""

import os

NODE_DIR = '/kaggle/working/ComfyUI/custom_nodes/ltx_scene_loader'
os.makedirs(NODE_DIR, exist_ok=True)

# ── Write scene_loader_node.py ────────────────────────────────────────────────
node_code = '''
import json, os

class LTXSceneLoader:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "scenes_json_path": ("STRING", {"default": "/kaggle/working/ComfyUI/input/scenes.json", "multiline": False}),
                "image_folder":     ("STRING", {"default": "/kaggle/working/ComfyUI/output/", "multiline": False}),
                "audio_folder":     ("STRING", {"default": "/kaggle/working/ComfyUI/input/audio/", "multiline": False}),
                "scene_index":      ("INT",    {"default": 1, "min": 1, "max": 999, "step": 1}),
            }
        }

    RETURN_TYPES  = ("STRING", "STRING", "INT", "INT", "INT")
    RETURN_NAMES  = ("image_path", "audio_path", "frames", "lip_sync", "total_scenes")
    FUNCTION      = "load_scene"
    CATEGORY      = "LTX/Batch"
    OUTPUT_NODE   = False

    def load_scene(self, scenes_json_path, image_folder, audio_folder, scene_index):
        if not os.path.exists(scenes_json_path):
            raise FileNotFoundError(f"scenes.json not found: {scenes_json_path}")

        with open(scenes_json_path) as f:
            data = json.load(f)

        scenes       = data.get("scenes", [])
        total_scenes = len(scenes)
        idx          = max(1, min(scene_index, total_scenes))
        scene        = next((s for s in scenes if s["id"] == idx), scenes[idx - 1])

        image_path = image_folder.rstrip("/") + "/" + scene["image"]
        audio_path = audio_folder.rstrip("/") + "/" + scene["audio"]
        frames     = int(scene.get("frames",   169))
        lip_sync   = int(scene.get("lip_sync",   0))

        char = scene.get("character", "?")
        print(f"[LTXSceneLoader] Scene {idx}/{total_scenes} | {scene[\'image\']} + {scene[\'audio\']} | {frames}f | {\'lip:\'+char if lip_sync else \'narrator\'}")

        return (image_path, audio_path, frames, lip_sync, total_scenes)

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

print(f"✅ LTXSceneLoader installed at: {NODE_DIR}")
print("   Outputs: image_path, audio_path, frames, lip_sync, total_scenes")
print("   → total_scenes connects to ImpactQueueTriggerCountdown")

"""
LTX Scene Loader — Custom ComfyUI Node
=======================================
Place this file in:
/kaggle/working/ComfyUI/custom_nodes/ltx_scene_loader/scene_loader_node.py

Also create:
/kaggle/working/ComfyUI/custom_nodes/ltx_scene_loader/__init__.py

This node:
1. Reads scenes.json
2. Takes a scene index (from PrimitiveInt increment)
3. Joins image filename with image folder path
4. Joins audio filename with audio folder path
5. Returns: image_path, audio_path, frames, lip_sync, total_scenes
   - total_scenes connects to ImpactQueueTriggerCountdown
"""

import json
import os


class LTXSceneLoader:
    """
    Loads a single scene from scenes.json by index.
    Returns image path, audio path, frames, lip_sync flag, and total scene count.
    """

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

    # Output types
    RETURN_TYPES = ("STRING", "STRING", "INT", "INT", "INT")
    RETURN_NAMES = ("image_path", "audio_path", "frames", "lip_sync", "total_scenes")

    FUNCTION     = "load_scene"
    CATEGORY     = "LTX/Batch"
    OUTPUT_NODE  = False

    def load_scene(self, scenes_json_path, image_folder, audio_folder, scene_index):
        # ── Load JSON ─────────────────────────────────────────────────────────
        if not os.path.exists(scenes_json_path):
            raise FileNotFoundError(
                f"scenes.json not found at: {scenes_json_path}\n"
                f"Run setup_scenes.py first to generate it."
            )

        with open(scenes_json_path, 'r') as f:
            data = json.load(f)

        scenes = data.get('scenes', [])
        total_scenes = len(scenes)

        if total_scenes == 0:
            raise ValueError("scenes.json has no scenes defined")

        # ── Find scene by index (1-based) ─────────────────────────────────────
        # Clamp index to valid range
        idx = max(1, min(scene_index, total_scenes))
        scene = next((s for s in scenes if s['id'] == idx), None)

        # Fallback: pick by position if id not found
        if scene is None:
            scene = scenes[idx - 1]

        # ── Build full paths ──────────────────────────────────────────────────
        # Ensure folders end with /
        img_folder = image_folder.rstrip('/') + '/'
        aud_folder = audio_folder.rstrip('/') + '/'

        image_path = img_folder + scene['image']
        audio_path = aud_folder + scene['audio']
        frames     = int(scene.get('frames', 169))
        lip_sync   = int(scene.get('lip_sync', 0))

        # ── Log ───────────────────────────────────────────────────────────────
        lip_str = f"💬 {scene.get('character','?')} speaks" if lip_sync else "🔇 narrator"
        print(f"\n[LTXSceneLoader] Scene {idx}/{total_scenes}")
        print(f"  Image:    {image_path}")
        print(f"  Audio:    {audio_path}")
        print(f"  Frames:   {frames}")
        print(f"  Lip sync: {lip_str}")

        return (image_path, audio_path, frames, lip_sync, total_scenes)


# ── Node registration ─────────────────────────────────────────────────────────
NODE_CLASS_MAPPINGS = {
    "LTXSceneLoader": LTXSceneLoader
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LTXSceneLoader": "LTX Scene Loader 🎬"
}

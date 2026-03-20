import json
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

    RETURN_TYPES  = ("STRING", "STRING", "INT", "INT", "INT")
    RETURN_NAMES  = ("image_path", "audio_path", "frames", "lip_sync", "total_scenes")
    FUNCTION      = "load_scene"
    CATEGORY      = "LTX/Batch"
    OUTPUT_NODE   = False

    def load_scene(self, scenes_json_path, image_folder, audio_folder, scene_index):

        if not os.path.exists(scenes_json_path):
            raise FileNotFoundError(
                f"scenes.json not found at: {scenes_json_path}\n"
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

        print(f"\n[LTXSceneLoader] Scene {idx}/{total_scenes}")
        print(f"  Image:    {image_path}")
        print(f"  Audio:    {audio_path}")
        print(f"  Frames:   {frames}")
        print(f"  Lip sync: {lip_str}")

        return (image_path, audio_path, frames, lip_sync, total_scenes)


NODE_CLASS_MAPPINGS = {
    "LTXSceneLoader": LTXSceneLoader
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LTXSceneLoader": "LTX Scene Loader 🎬"
}

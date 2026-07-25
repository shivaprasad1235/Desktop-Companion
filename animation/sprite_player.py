import json
import os
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt

class SpritePlayer:
    def __init__(self, character_pack: str = "slime", base_dir: str = "assets/characters"):
        self.base_dir = base_dir
        self.character_pack = character_pack
        self.current_animation = "idle"
        self.frame_index = 0
        self.time_accumulator = 0.0
        
        self.config = {}
        self.animations = {}
        self.load_character_pack(character_pack)

    def load_character_pack(self, pack_name: str):
        """Loads all frames for the specified character pack."""
        self.character_pack = pack_name
        pack_path = os.path.join(self.base_dir, pack_name)
        
        # Fallback to default slime if pack doesn't exist
        if not os.path.exists(pack_path) or not os.path.isdir(pack_path):
            print(f"Character pack '{pack_name}' not found. Falling back to default 'slime'.")
            self.character_pack = "slime"
            pack_path = os.path.join(self.base_dir, "slime")
            
        # 1. Load config
        config_path = os.path.join(pack_path, "character.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    self.config = json.load(f)
            except Exception as e:
                print(f"Error loading character config: {e}")
                self.config = {}
        else:
            self.config = {}
            
        # Default config fallbacks
        self.config.setdefault("name", self.character_pack.capitalize())
        self.config.setdefault("scale", 1.0)
        self.config.setdefault("speed", 1.0)
        self.config.setdefault("greeting", "Hello Shiva! 👋")
        self.config.setdefault("cursorFear", 150)
        self.config.setdefault("jumpHeight", 120)
        self.config.setdefault("idleChance", 0.2)
        
        # 2. Scan animation folders
        self.animations.clear()
        
        # List of subfolders representing animation states
        if os.path.exists(pack_path):
            for entry in os.scandir(pack_path):
                if entry.is_dir():
                    anim_name = entry.name
                    frames = []
                    # Load frames in order: 0.png, 1.png, 2.png, ...
                    frame_idx = 0
                    while True:
                        frame_file = os.path.join(entry.path, f"{frame_idx}.png")
                        if os.path.exists(frame_file):
                            pix = QPixmap(frame_file)
                            if not pix.isNull():
                                frames.append(pix)
                            frame_idx += 1
                        else:
                            break
                            
                    if frames:
                        self.animations[anim_name] = frames
                        
        print(f"Loaded character '{self.config['name']}' with {len(self.animations)} animations.")

    def set_animation(self, anim_name: str):
        """Switches to a different animation, resetting the frame index if it's new."""
        if anim_name not in self.animations:
            # Fallback to idle if animation doesn't exist
            anim_name = "idle"
            
        if self.current_animation != anim_name:
            self.current_animation = anim_name
            self.frame_index = 0
            self.time_accumulator = 0.0

    def get_current_frame(self) -> QPixmap:
        """Returns the QPixmap for the current frame of the active animation."""
        frames = self.animations.get(self.current_animation)
        if not frames:
            # Absolute fallback to a blank pixmap if no animations loaded
            return QPixmap(64, 64)
            
        # Bound safety
        idx = self.frame_index % len(frames)
        return frames[idx]

    def update(self, dt: float, target_fps: int = 12):
        """Advances the frame index based on delta time."""
        frames = self.animations.get(self.current_animation)
        if not frames:
            return
            
        # Custom character configuration animation multiplier
        # (e.g. fast runners can play frames faster)
        anim_speed_multiplier = 1.0
        if self.current_animation in ["run", "walk"]:
            anim_speed_multiplier = self.config.get("speed", 1.0)
            
        frame_duration = 1.0 / (target_fps * anim_speed_multiplier)
        self.time_accumulator += dt
        
        if self.time_accumulator >= frame_duration:
            advance = int(self.time_accumulator // frame_duration)
            self.frame_index = (self.frame_index + advance) % len(frames)
            self.time_accumulator %= frame_duration

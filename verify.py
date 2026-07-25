import os
import sys
import unittest
import sqlite3
import math
import shutil

# Make sure we can load packages
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from settings.settings_manager import settings_manager
from physics.physics_engine import PhysicsEngine
from utils.sound_generator import generate_all_sounds
from utils.sprite_generator import generate_frames

class TestDesktopBuddy(unittest.TestCase):
    def setUp(self):
        # Setup temporary directories for outputs
        self.test_sound_dir = "verify_test_sounds"
        self.test_sprite_dir = "verify_test_sprites"
        os.makedirs(self.test_sound_dir, exist_ok=True)
        os.makedirs(self.test_sprite_dir, exist_ok=True)

    def tearDown(self):
        # Clean up temporary folders
        if os.path.exists(self.test_sound_dir):
            shutil.rmtree(self.test_sound_dir)
        if os.path.exists(self.test_sprite_dir):
            shutil.rmtree(self.test_sprite_dir)

    def test_settings_sqlite(self):
        """Validates settings storage, reading, and correct typing conversions."""
        # Set values
        settings_manager.set("test_string", "hello")
        settings_manager.set("test_int", 42)
        settings_manager.set("test_bool", True)
        settings_manager.set("test_float", 3.14)
        
        # Query values with typings inferred from defaults
        self.assertEqual(settings_manager.get("test_string", "default"), "hello")
        self.assertEqual(settings_manager.get("test_int", 0), 42)
        self.assertEqual(settings_manager.get("test_bool", False), True)
        self.assertAlmostEqual(settings_manager.get("test_float", 0.0), 3.14)

    def test_sound_wave_headers(self):
        """Verifies synthetic sound generator produces valid wave header format."""
        generate_all_sounds(self.test_sound_dir)
        boing_path = os.path.join(self.test_sound_dir, "boing.wav")
        self.assertTrue(os.path.exists(boing_path))
        
        # Check WAV PCM Header validity
        with open(boing_path, "rb") as f:
            header = f.read(12)
            # Standard WAV starts with RIFF ... WAVE
            self.assertEqual(header[0:4], b"RIFF")
            self.assertEqual(header[8:12], b"WAVE")

    def test_physics_kinematics(self):
        """Validates physics loop updates, gravity pull, friction dampening, and bounds clamps."""
        # Spawn floating in air
        pe = PhysicsEngine(x=100.0, y=100.0, w=64, h=64)
        
        # Test Gravity (starts floating, should fall downwards)
        pe.use_gravity = True
        bounds = (0, 0, 1920, 1080)
        dt = 0.016 # 60 FPS
        
        # Run physics update 10 ticks
        for _ in range(10):
            pe.update(dt, bounds)
            
        # y position should increase under gravity
        self.assertGreater(pe.y, 100.0)
        self.assertGreater(pe.vy, 0.0)
        self.assertFalse(pe.is_on_ground)

        # Test landing ground clamp
        pe.y = 1010.0 # near bottom (1080 - height 64 = 1016 floor)
        pe.vy = 400.0  # falling fast enough to cross boundary in 1 tick
        pe.use_gravity = True
        pe.update(dt, bounds)
        self.assertEqual(pe.y, 1016.0) # clamped to floor
        
        # Test friction deceleration
        pe.vx = 100.0
        pe.is_on_ground = True
        pe.update(dt, bounds)
        self.assertLess(pe.vx, 100.0)

if __name__ == "__main__":
    unittest.main()

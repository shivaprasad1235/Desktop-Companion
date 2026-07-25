import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QTimer

# Import core modules
from engine.event_bus import event_bus
from engine.game_loop import GameLoop
from engine.state_machine import SystemStateMachine
from physics.physics_engine import PhysicsEngine
from animation.sprite_player import SpritePlayer
from ai.mood import MoodSystem
from ui.buddy_window import BuddyWindow
from ui.settings_window import SettingsWindow
from ui.tray import SystemTrayController
from ui.speech_bubble import SpeechBubbleWindow
from ui.spider_window import SpiderWindow

# Import plugins
from plugins.system_monitor import SystemMonitorPlugin
from plugins.weather import WeatherPlugin

# Import generators for bootstrapping
from utils.sprite_generator import generate_all_characters
from utils.sound_generator import generate_all_sounds

def bootstrap_assets():
    """Generates default character packs and sounds if not present."""
    print("Checking assets...")
    
    # 1. Check characters
    char_base = os.path.abspath("assets/characters")
    slime_path = os.path.join(char_base, "slime")
    cat_path = os.path.join(char_base, "cat")
    ironman_path = os.path.join(char_base, "ironman")
    robobuddy_path = os.path.join(char_base, "robobuddy")
    
    if not os.path.exists(slime_path) or not os.path.exists(cat_path) or not os.path.exists(ironman_path) or not os.path.exists(robobuddy_path):
        print("Default character packs missing. Generating...")
        generate_all_characters()
        
    # 2. Check sounds
    sound_base = os.path.abspath("assets/sounds")
    boing_path = os.path.join(sound_base, "boing.wav")
    
    if not os.path.exists(boing_path):
        print("Sound effects missing. Generating...")
        generate_all_sounds(sound_base)
        
    print("Asset verification complete.")

def main():
    # Make sure we run in the directory of main.py to keep relative paths clean
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # 1. Bootstrap Assets
    bootstrap_assets()

    # 2. Initialize Qt Application
    # Pass arguments or start app
    # Set shared attribute for high DPI scaling if using older Qt, Qt6 handles it automatically
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # keep running on system tray close

    # 3. Load user settings
    from settings.settings_manager import settings_manager
    selected_pack = settings_manager.get("character_pack", "slime")
    char_size = settings_manager.get("size", 64)
    is_paused = settings_manager.get("paused", False)
    is_muted = settings_manager.get("mute", False)

    # 4. Instantiate core engine components
    sprite_player = SpritePlayer(character_pack=selected_pack)
    
    # Spawn in center of primary screen on startup
    primary_screen = app.primaryScreen()
    screen_rect = primary_screen.availableGeometry()
    spawn_x = screen_rect.x() + (screen_rect.width() - char_size) / 2
    spawn_y = screen_rect.y() + (screen_rect.height() - char_size) - 10
    
    physics_engine = PhysicsEngine(x=spawn_x, y=spawn_y, w=char_size, h=char_size)
    mood_system = MoodSystem()
    state_machine = SystemStateMachine()

    # 5. Instantiate UI Windows
    buddy_window = BuddyWindow(sprite_player, physics_engine, mood_system)
    speech_window = SpeechBubbleWindow()
    spider_window = SpiderWindow()
    settings_window = SettingsWindow()
    tray_controller = SystemTrayController()

    # Synchronize tray states on boot
    tray_controller.sync_settings(is_paused, is_muted)
    
    # Set initial position coordinates
    buddy_window.sync_window_position()

    # 6. Instantiate Game Loop
    game_loop = GameLoop(buddy_window, physics_engine, sprite_player, mood_system, state_machine, speech_window)
    game_loop.start()

    # 7. Wire UI Events & Signals
    # Tray events
    tray_controller.open_settings_requested.connect(settings_window.show)
    tray_controller.exit_requested.connect(app.quit)
    tray_controller.pause_toggled.connect(lambda p: settings_manager.set("paused", p))
    tray_controller.mute_toggled.connect(lambda m: settings_manager.set("mute", m))
    tray_controller.character_changed.connect(lambda char_name: settings_manager.set("character_pack", char_name))
    
    # Settings change synchronization
    settings_window.settings_changed.connect(
        lambda: tray_controller.sync_settings(
            settings_manager.get("paused", False),
            settings_manager.get("mute", False)
        )
    )

    # Event Bus listeners
    event_bus.subscribe("show_settings", settings_window.show)
    event_bus.subscribe("exit_application", app.quit)
    event_bus.subscribe("setting_changed_paused", lambda v: tray_controller.sync_settings(bool(v), settings_manager.get("mute", False)))
    event_bus.subscribe("setting_changed_mute", lambda v: tray_controller.sync_settings(settings_manager.get("paused", False), bool(v)))

    # Show initial greeting speech bubble
    def play_startup_greeting():
        import random
        welcomes = [
            "👋 Welcome back, Shiva!",
            "Good to see you again!",
            "Ready for another day?",
            "Let's build something awesome today!",
            "Hi! I missed you!",
            "Hope you have a productive day!",
            "Good morning! ☀️",
            "Welcome back! 😊"
        ]
        msg = random.choice(welcomes)
        sprite_player.set_animation("happy")
        event_bus.publish("trigger_speech", msg, 3.5)
        if not settings_manager.get("mute", False):
            game_loop.play_sound("greet")
            
    if settings_manager.get("greeting_enabled", True):
        QTimer.singleShot(1000, play_startup_greeting)

    # 8. Initialize Plugins
    active_plugins = [
        SystemMonitorPlugin(),
        WeatherPlugin()
    ]
    for p in active_plugins:
        p.initialize()

    # Make tray icon visible
    tray_controller.show()

    # 9. Run Qt Application Loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

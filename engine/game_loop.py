import time
import math
import os
import random
from PySide6.QtCore import QTimer, QUrl, Qt
from PySide6.QtGui import QGuiApplication, QCursor
from PySide6.QtMultimedia import QSoundEffect
import ctypes

from engine.event_bus import event_bus
from settings.settings_manager import settings_manager
from utils.windows_api import get_system_idle_time

class GameLoop:
    def __init__(self, buddy_window, physics_engine, sprite_player, mood_system, state_machine, speech_window):
        self.buddy_window = buddy_window
        self.physics_engine = physics_engine
        self.sprite_player = sprite_player
        self.mood_system = mood_system
        self.state_machine = state_machine
        self.speech_window = speech_window
        
        # 1. State Machine Initialization
        # Valid States: "Startup", "Idle", "Wander", "Escape", "Capture", "Release", "MoveMode"
        self.current_state = "Startup"
        self.state_timer = 1.0  # 1s startup delay
        self.wander_target_pos = None
        self.move_target_pos = None
        self.playful_speech_timer = 0.0
        self.stuck_timer = 0.0

        # General context dictionary for personality queries
        self.bt_context = {}
        
        # Delta time tracking
        self.last_tick_time = time.perf_counter()
        
        # Mouse velocity tracking
        self.prev_mouse_pos = QCursor.pos()
        self.mouse_vx = 0.0
        self.mouse_vy = 0.0
        
        # QSoundEffect cache
        self.sounds = {}
        self._init_sounds()
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)
        
        event_bus.subscribe("setting_changed_mute", self._on_mute_changed)
        event_bus.subscribe("trigger_speech", self._on_trigger_speech)
        event_bus.subscribe("set_move_target", self._on_set_move_target)

    def start(self):
        self.last_tick_time = time.perf_counter()
        self.prev_mouse_pos = QCursor.pos()
        self.timer.start(16)  # ~60 FPS

    def stop(self):
        self.timer.stop()

    def _init_sounds(self):
        sound_dir = os.path.abspath("assets/sounds")
        sound_files = ["boing.wav", "whoosh.wav", "yawn.wav", "hehe.wav", "greet.wav", "caught.wav"]
        
        for sf in sound_files:
            path = os.path.join(sound_dir, sf)
            if os.path.exists(path):
                effect = QSoundEffect()
                effect.setSource(QUrl.fromLocalFile(path))
                effect.setVolume(0.12)
                self.sounds[sf.split(".")[0]] = effect

    def _on_mute_changed(self, value):
        mute = bool(value)
        for sound in self.sounds.values():
            sound.setVolume(0.0 if mute else 0.12)

    def _on_trigger_speech(self, text: str, duration: float = 2.5):
        if self.speech_window:
            self.speech_window.set_text(text, duration)

    def _on_set_move_target(self, tx, ty):
        self.move_target_pos = (tx, ty)
        self.set_state("MoveMode")

    def play_sound(self, name: str):
        if self.state_machine.is_muted():
            return
        sound = self.sounds.get(name)
        if sound:
            sound.play()

    def set_state(self, new_state):
        if self.current_state == new_state:
            return
            
        print(f"State transition: {self.current_state} -> {new_state}")
        
        # --- On Exit ---
        if self.current_state == "Wander":
            self.wander_target_pos = None
        elif self.current_state == "MoveMode":
            self.move_target_pos = None

        # Clean/cancel previous animations/speech/timers
        if self.speech_window:
            self.speech_window.hide()
            
        self.current_state = new_state
        self.stuck_timer = 0.0

        # --- On Enter ---
        if new_state == "Startup":
            self.state_timer = 1.0
            self.sprite_player.set_animation("happy")
            
        elif new_state == "Idle":
            self.state_timer = random.uniform(2.0, 5.0)
            self.sprite_player.set_animation("idle")
            
        elif new_state == "Wander":
            self.state_timer = random.uniform(4.0, 8.0)
            bounds = self.bt_context.get("bounds", (0, 0, 1920, 1080))
            x_min, y_min, x_max, y_max = bounds
            char_size = self.buddy_window.char_size
            tx = random.randint(x_min + 30, x_max - 30 - char_size)
            ty = random.randint(y_min + 30, y_max - 30 - char_size)
            self.wander_target_pos = (tx, ty)
            self.sprite_player.set_animation("walk")
            
        elif new_state == "Escape":
            self.playful_speech_timer = 0.0  # comment immediately
            self.sprite_player.set_animation("run")
            
        elif new_state == "Capture":
            self.sprite_player.set_animation("caught")
            self.play_sound("caught")
            caught_msgs = [
                "Okay, you got me!",
                "Easy!",
                "Don't drop me!"
            ]
            event_bus.publish("trigger_speech", random.choice(caught_msgs), 3.0)
            
        elif new_state == "Release":
            self.state_timer = 0.8  # landing recovery delay
            self.sprite_player.set_animation("surprised")
            self.play_sound("boing")
            
            # Spawn landing dust
            bx = self.physics_engine.x
            by = self.physics_engine.y
            char_size = self.buddy_window.char_size
            event_bus.publish("spawn_particles", "dust", bx + char_size / 2, by + char_size, 8)
            
            release_msgs = [
                "Freedom!",
                "See you!",
                "Catch me again!"
            ]
            event_bus.publish("trigger_speech", random.choice(release_msgs), 3.0)

    def tick(self):
        if self.state_machine.is_paused():
            self.last_tick_time = time.perf_counter()
            if self.buddy_window.is_drag_mode:
                self.buddy_window.sync_window_position()
            return

        now = time.perf_counter()
        dt = now - self.last_tick_time
        self.last_tick_time = now
        dt = min(0.05, dt)

        # 1. Track Mouse Position & Velocity
        curr_mouse_pos = QCursor.pos()
        dx_m = curr_mouse_pos.x() - self.prev_mouse_pos.x()
        dy_m = curr_mouse_pos.y() - self.prev_mouse_pos.y()
        self.mouse_vx = self.mouse_vx * 0.8 + (dx_m / dt) * 0.2
        self.mouse_vy = self.mouse_vy * 0.8 + (dy_m / dt) * 0.2
        self.prev_mouse_pos = curr_mouse_pos

        # 2. Monitor screen boundaries
        screen = QGuiApplication.screenAt(self.buddy_window.geometry().center())
        if not screen:
            screen = QGuiApplication.primaryScreen()
        rect = screen.availableGeometry()
        bounds = (rect.x(), rect.y(), rect.x() + rect.width(), rect.y() + rect.height())
        self.bt_context["bounds"] = bounds

        # Fetch active personality parameters
        p_name = settings_manager.get("personality", "Friendly")
        from ai.personalities import get_personality
        self.bt_context["personality"] = get_personality(p_name)

        # Global CTRL key detection (VK_CONTROL = 0x11)
        is_ctrl_held = bool(ctypes.windll.user32.GetAsyncKeyState(0x11) & 0x8000)

        # Mascot center calculations
        bx = self.physics_engine.x + self.buddy_window.char_size / 2
        by = self.physics_engine.y + self.buddy_window.char_size / 2
        cursor_dist = math.hypot(curr_mouse_pos.x() - bx, curr_mouse_pos.y() - by)
        fear_dist = self.bt_context["personality"].cursor_fear_dist

        # 3. Handle Wall Collisions (we run physics *before* we transition but check last frames)
        collisions = {
            "left": self.physics_engine.x <= bounds[0],
            "right": self.physics_engine.x + self.physics_engine.w >= bounds[2],
            "top": self.physics_engine.y <= bounds[1],
            "bottom": self.physics_engine.y + self.physics_engine.h >= bounds[3]
        }

        # 4. State Transitions Engine
        if is_ctrl_held:
            if self.current_state == "Capture":
                pass
            elif self.current_state == "Release":
                pass  # wait to complete release
            else:
                # Capture check
                if cursor_dist < self.buddy_window.char_size * 0.75:
                    self.set_state("Capture")
                else:
                    # Surrender idle (freeze in place)
                    self.set_state("Idle")
        else:
            if self.current_state == "Capture":
                self.set_state("Release")
            elif self.current_state == "Release":
                self.state_timer -= dt
                if self.state_timer <= 0.0:
                    self.set_state("Idle")
            elif self.current_state == "Startup":
                self.state_timer -= dt
                if self.state_timer <= 0.0:
                    self.set_state("Idle")
            elif self.current_state == "MoveMode":
                # Check wall collision or target arrival
                target_arrived = False
                if self.move_target_pos:
                    mbx, mby = self.physics_engine.x, self.physics_engine.y
                    mtx, mty = self.move_target_pos
                    mdist = math.hypot(mtx - mbx, mty - mby)
                    if mdist < 15:
                        target_arrived = True
                
                has_collided = (collisions["left"] or collisions["right"] or 
                                collisions["top"] or collisions["bottom"])
                
                if target_arrived or has_collided:
                    self.set_state("Idle")
                    self.sprite_player.set_animation("happy")
                    self.play_sound("greet")
                    event_bus.publish("trigger_speech", "Arrived! 😄", 2.5)
                    event_bus.publish("move_target_reached")
            else:
                # Normal modes: Escape has priority over Wander/Idle
                if cursor_dist < fear_dist:
                    self.set_state("Escape")
                else:
                    if self.current_state == "Escape":
                        self.set_state("Idle")
                    elif self.current_state == "Idle":
                        self.state_timer -= dt
                        if self.state_timer <= 0.0:
                            self.set_state("Wander")
                    elif self.current_state == "Wander":
                        self.state_timer -= dt
                        target_arrived = False
                        if self.wander_target_pos:
                            wbx, wby = self.physics_engine.x, self.physics_engine.y
                            wtx, wty = self.wander_target_pos
                            wdist = math.hypot(wtx - wbx, wty - wby)
                            if wdist < 15:
                                target_arrived = True
                                
                        has_collided = (collisions["left"] or collisions["right"] or 
                                        collisions["top"] or collisions["bottom"])
                                        
                        if self.state_timer <= 0.0 or target_arrived or has_collided:
                            self.set_state("Idle")

        # 5. Stuck Failsafe (speed < 10.0 for > 2 seconds while moving)
        is_moving_state = (self.current_state == "Wander" or self.current_state == "Escape" or self.current_state == "MoveMode")
        current_speed = math.hypot(self.physics_engine.vx, self.physics_engine.vy)
        
        if is_moving_state and current_speed < 10.0:
            self.stuck_timer += dt
            if self.stuck_timer > 2.0:
                print("Failsafe stuck detected! Resetting state to Idle.")
                self.set_state("Idle")
                self.state_timer = 0.5  # wait 0.5s in idle
        else:
            self.stuck_timer = 0.0

        # 6. Execute State Logic & Calculate Target Velocity
        target_vx = 0.0
        target_vy = 0.0
        disable_gravity = False
        
        if self.current_state == "Startup":
            target_vx = 0.0
            target_vy = 0.0
            self.sprite_player.set_animation("happy")
            
        elif self.current_state == "Idle":
            target_vx = 0.0
            target_vy = 0.0
            if is_ctrl_held:
                self.sprite_player.set_animation("surprised")
            else:
                self.sprite_player.set_animation("idle")
                
        elif self.current_state == "Wander":
            self.sprite_player.set_animation("walk")
            if self.wander_target_pos:
                wbx, wby = self.physics_engine.x, self.physics_engine.y
                wtx, wty = self.wander_target_pos
                dx = wtx - wbx
                dy = wty - wby
                wdist = math.hypot(dx, dy)
                if wdist > 0:
                    walk_speed = 75.0 * self.bt_context["personality"].speed_multiplier
                    if self.mood_system.get_current_mood_state() == "sleepy":
                        walk_speed *= 0.7
                    target_vx = (dx / wdist) * walk_speed
                    target_vy = (dy / wdist) * walk_speed
                    disable_gravity = True
                    
        elif self.current_state == "MoveMode":
            self.sprite_player.set_animation("run")
            if self.move_target_pos:
                mbx, mby = self.physics_engine.x, self.physics_engine.y
                mtx, mty = self.move_target_pos
                dx = mtx - mbx
                dy = mty - mby
                mdist = math.hypot(dx, dy)
                if mdist > 0:
                    run_speed = 220.0 if mdist > 200 else 100.0
                    target_vx = (dx / mdist) * run_speed
                    target_vy = (dy / mdist) * run_speed
                    disable_gravity = True

        elif self.current_state == "Escape":
            self.sprite_player.set_animation("run")
            
            # Escape direction calculation (ALWAYS runs away at full speed)
            dx = (self.physics_engine.x + self.buddy_window.char_size / 2) - curr_mouse_pos.x()
            dy = (self.physics_engine.y + self.buddy_window.char_size / 2) - curr_mouse_pos.y()
            edist = math.hypot(dx, dy)
            
            if edist > 0:
                dir_x = dx / edist
                dir_y = dy / edist
            else:
                dir_x = random.choice([-1.0, 1.0])
                dir_y = random.choice([-1.0, 1.0])
                
            # Wall-sliding redirects
            if collisions["left"] and dir_x < 0:
                dir_x = 0.0
                dir_y = 1.0 if dy >= 0 else -1.0
            elif collisions["right"] and dir_x > 0:
                dir_x = 0.0
                dir_y = 1.0 if dy >= 0 else -1.0
                
            if collisions["top"] and dir_y < 0:
                dir_y = 0.0
                dir_x = 1.0 if dx >= 0 else -1.0
            elif collisions["bottom"] and dir_y > 0:
                dir_y = 0.0
                dir_x = 1.0 if dx >= 0 else -1.0
                
            run_speed = 350.0 * self.bt_context["personality"].speed_multiplier
            if edist < 100:
                run_speed *= 1.4  # boost speed if very close
                
            target_vx = dir_x * run_speed
            target_vy = dir_y * run_speed
            disable_gravity = True
            
            # Escape chatter interval
            self.playful_speech_timer -= dt
            if self.playful_speech_timer <= 0.0 and not (self.speech_window and self.speech_window.is_visible()):
                escape_msgs = [
                    "Catch me if you can! 😜",
                    "Too slow!",
                    "Nice try!",
                    "Missed me!",
                    "Almost!"
                ]
                event_bus.publish("trigger_speech", random.choice(escape_msgs), 2.5)
                self.playful_speech_timer = random.uniform(2.0, 3.0)
                self.play_sound("whoosh")
                
        elif self.current_state == "Capture":
            self.sprite_player.set_animation("caught")
            
            # Lock position to mouse cursor center
            char_size = self.buddy_window.char_size
            self.physics_engine.x = float(curr_mouse_pos.x() - char_size / 2)
            self.physics_engine.y = float(curr_mouse_pos.y() - char_size / 2)
            self.physics_engine.vx = 0.0
            self.physics_engine.vy = 0.0
            self.physics_engine.use_gravity = False
            
            target_vx = 0.0
            target_vy = 0.0
            disable_gravity = True
            
        elif self.current_state == "Release":
            self.sprite_player.set_animation("surprised")
            target_vx = 0.0
            target_vy = 0.0

        # 7. Apply physics gravity toggles
        if disable_gravity:
            self.physics_engine.use_gravity = False
        elif not self.physics_engine.is_on_ground and not self.physics_engine.use_gravity:
            self.physics_engine.use_gravity = True

        # 8. Easing velocities
        accel_rate = 0.15 if self.physics_engine.is_on_ground else 0.04
        mult = settings_manager.get("movement_speed", 1.0)
        self.physics_engine.accelerate_toward(target_vx * mult, target_vy * mult, accel_rate, dt)

        # 9. Update physics calculations
        prev_vy = self.physics_engine.vy
        
        collisions_res = self.physics_engine.update(dt, bounds)
        
        # Landing dust and boing sound
        if collisions_res["bottom"] and prev_vy > 80.0:
            char_size = self.buddy_window.char_size
            event_bus.publish("spawn_particles", "dust", self.physics_engine.x + char_size/2, self.physics_engine.y + char_size, 8)
            self.play_sound("boing")
            self.mood_system.trigger_joy(0.08)

        # 10. Update Mood System
        self.mood_system.update(dt, is_moving=(abs(self.physics_engine.vx) > 15.0 or abs(self.physics_engine.vy) > 15.0), is_system_idle=(get_system_idle_time() > 40.0))

        # Adjust animations based on dominant moods if in normal Idle state
        dominant_mood = self.mood_system.get_current_mood_state()
        if self.current_state == "Idle" and not is_ctrl_held:
            if dominant_mood == "sleepy":
                self.sprite_player.set_animation("sleep")
            elif dominant_mood == "happy":
                self.sprite_player.set_animation("happy")
            elif dominant_mood == "scared":
                self.sprite_player.set_animation("surprised")

        # 11. Tick animation frame loaders
        fps_val = settings_manager.get("animation_fps", 12)
        self.sprite_player.update(dt, target_fps=fps_val)

        # Spawn particles
        if self.sprite_player.current_animation == "sleep" and random.random() < 0.02:
            event_bus.publish("spawn_particles", "zzz", self.physics_engine.x + self.buddy_window.char_size * 0.8, self.physics_engine.y + 10, 1)
        if self.sprite_player.current_animation == "happy" and random.random() < 0.04:
            event_bus.publish("spawn_particles", "sparkle", self.physics_engine.x + self.buddy_window.char_size/2, self.physics_engine.y + self.buddy_window.char_size/2, 2)

        # 12. Update UI overlays and rendering
        self.buddy_window.particle_system.update(dt)
        if self.speech_window:
            self.speech_window.update_timer(dt)
            self.speech_window.follow_buddy(int(self.physics_engine.x), int(self.physics_engine.y), self.buddy_window.width())

        # 13. Sync physical coordinates to Qt UI Window
        if not self.buddy_window.is_drag_mode:
            self.buddy_window.sync_window_position()
            
        self.buddy_window.update()

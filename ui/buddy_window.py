import sys
import math
import time
from PySide6.QtWidgets import QWidget, QMenu
from PySide6.QtCore import Qt, QPoint, QRectF, QTimer, Signal
from PySide6.QtGui import QPainter, QCursor, QMouseEvent, QAction, QTransform, QGuiApplication

from engine.event_bus import event_bus
from animation.particle_system import ParticleSystem

class ScreenOverlay(QWidget):
    screen_clicked = Signal(QPoint)

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 1);")
        
        desktop = QGuiApplication.primaryScreen().virtualGeometry()
        self.setGeometry(desktop)
        self.setCursor(Qt.CrossCursor)
        self.show()

    def mousePressEvent(self, event):
        self.screen_clicked.emit(event.globalPosition().toPoint())
        self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()

class BuddyWindow(QWidget):
    def __init__(self, sprite_player, physics_engine, mood_system, parent=None):
        # Translucent attributes MUST be set BEFORE creating handles, flags, or showing the widget
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setStyleSheet("background: transparent; border: none;")

        self.sprite_player = sprite_player
        self.physics_engine = physics_engine
        self.mood_system = mood_system
        self.particle_system = ParticleSystem()
        
        from settings.settings_manager import settings_manager
        self.char_size = settings_manager.get("size", 64)
        self.opacity_val = settings_manager.get("opacity", 1.0)
        self.click_through = settings_manager.get("click_through", False)
        self.always_on_top = settings_manager.get("always_on_top", True)
        
        self.is_selected = False
        self.move_target = None
        self.overlay = None

        self.is_drag_mode = False
        self.drag_position = QPoint()
        self.ctrl_double_click_active = False

        self._recalc_window_bounds()
        self._apply_window_flags()
        
        event_bus.subscribe("setting_changed", self._on_setting_changed)
        event_bus.subscribe("spawn_particles", self._spawn_particles_event)
        event_bus.subscribe("move_target_reached", self._on_move_target_reached)

    def _recalc_window_bounds(self):
        """Resizes window EXACTLY to character size. No invisible margins."""
        self.resize(self.char_size, self.char_size)
        self.physics_engine.w = self.char_size
        self.physics_engine.h = self.char_size

    def _apply_window_flags(self):
        flags = Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        
        if self.click_through and not self.ctrl_double_click_active and not self.is_selected:
            flags |= Qt.WindowTransparentForInput
            
        self.setWindowFlags(flags)
        self.setWindowOpacity(self.opacity_val)
        self.setMouseTracking(True)
        self.show()

    def _on_setting_changed(self, key, value):
        from settings.settings_manager import settings_manager
        if key == "size":
            self.char_size = int(value)
            self._recalc_window_bounds()
        elif key == "opacity":
            self.opacity_val = float(value)
            self.setWindowOpacity(self.opacity_val)
        elif key == "click_through":
            self.click_through = bool(value)
            self._apply_window_flags()
        elif key == "always_on_top":
            self.always_on_top = bool(value)
            self._apply_window_flags()
        elif key == "character_pack":
            self.sprite_player.load_character_pack(str(value))
            self.char_size = settings_manager.get("size", 64)
            self._recalc_window_bounds()

    def _spawn_particles_event(self, p_type: str, x: float, y: float, count: int = 5):
        local_x = self.char_size / 2
        local_y = self.char_size - 6 if p_type == "dust" else self.char_size / 2
        
        if p_type == "dust":
            self.particle_system.spawn_dust(local_x, local_y, count)
        elif p_type == "sparkle":
            self.particle_system.spawn_sparkles(local_x, local_y, count)
        elif p_type == "zzz":
            self.particle_system.spawn_zzz(local_x, local_y)

    def sync_window_position(self):
        self.move(int(self.physics_engine.x), int(self.physics_engine.y))

    # Selection & Move Mode
    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            if event.modifiers() & Qt.ControlModifier:
                self.ctrl_double_click_active = True
                self.is_drag_mode = True
                self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                self.setCursor(Qt.SizeAllCursor)
                self._apply_window_flags()
            else:
                self.is_selected = True
                event_bus.publish("trigger_speech", "Move Mode! 🎯 Click anywhere!")
                self.sprite_player.set_animation("thinking")
                
                self.overlay = ScreenOverlay()
                self.overlay.screen_clicked.connect(self._on_screen_selected)
                
            event.accept()

    def _on_screen_selected(self, point: QPoint):
        tx = point.x() - self.char_size / 2
        ty = point.y() - self.char_size / 2
        
        screen = QGuiApplication.screenAt(point)
        if not screen:
            screen = QGuiApplication.primaryScreen()
        rect = screen.availableGeometry()
        
        # Clamp target location inside available screen bounds
        tx = max(rect.x() + 10, min(rect.x() + rect.width() - self.char_size - 10, tx))
        ty = max(rect.y() + 10, min(rect.y() + rect.height() - self.char_size - 10, ty))
        
        self.move_target = (tx, ty)
        event_bus.publish("set_move_target", tx, ty)
        event_bus.publish("trigger_speech", "On my way! 🏃")
        self.sprite_player.set_animation("run")

    def _on_move_target_reached(self):
        self.move_target = None
        self.is_selected = False
        self._apply_window_flags()

    # Dragging logic
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton and self.ctrl_double_click_active:
            self.is_drag_mode = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
        elif event.button() == Qt.RightButton:
            self._show_context_menu(event.globalPosition().toPoint())

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.is_drag_mode and event.buttons() == Qt.LeftButton:
            new_pos = event.globalPosition().toPoint() - self.drag_position
            self.move(new_pos)
            self.physics_engine.x = float(new_pos.x())
            self.physics_engine.y = float(new_pos.y())
            self.physics_engine.vx = 0
            self.physics_engine.vy = 0
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton and self.is_drag_mode:
            self.is_drag_mode = False
            self.ctrl_double_click_active = False
            self.setCursor(Qt.ArrowCursor)
            self._apply_window_flags()
            event.accept()

    def _show_context_menu(self, global_pos):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #1e1e2e;
                color: #cdd6f4;
                border: 1px solid #313244;
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #b4befe;
                color: #11111b;
            }
        """)
        
        from settings.settings_manager import settings_manager
        is_paused = settings_manager.get("paused", False)
        pause_txt = "Resume AI" if is_paused else "Pause AI"
        pause_action = menu.addAction(pause_txt)
        
        is_muted = settings_manager.get("mute", False)
        mute_txt = "Unmute Sounds" if is_muted else "Mute Sounds"
        mute_action = menu.addAction(mute_txt)
        
        menu.addSeparator()
        
        settings_action = menu.addAction("Settings...")
        exit_action = menu.addAction("Exit")
        
        action = menu.exec(global_pos)
        if action == pause_action:
            settings_manager.set("paused", not is_paused)
        elif action == mute_action:
            settings_manager.set("mute", not is_muted)
        elif action == settings_action:
            event_bus.publish("show_settings")
        elif action == exit_action:
            event_bus.publish("exit_application")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 1. Paint transparent base over window canvas
        painter.setCompositionMode(QPainter.CompositionMode_Source)
        painter.fillRect(self.rect(), Qt.transparent)
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

        # 2. Draw Particles
        self.particle_system.draw(painter)
        
        # 3. Draw Character Sprite
        pixmap = self.sprite_player.get_current_frame()
        if not pixmap.isNull():
            # Scale frame to current size smoothly
            scaled = pixmap.scaled(self.char_size, self.char_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            
            # Check mirror reflection direction
            mirror = False
            if self.physics_engine.vx < -10.0:
                mirror = True
            elif self.physics_engine.vx > 10.0:
                mirror = False
            else:
                cursor_x = QCursor.pos().x()
                buddy_center_x = self.x() + self.char_size / 2
                if cursor_x < buddy_center_x:
                    mirror = True
                    
            if mirror:
                scaled = scaled.transformed(QTransform().scale(-1, 1))
                
            # Apply exact sprite mask to target widget for perfect OS pass-through hit testing
            self.setMask(scaled.mask())
            
            # Setup transformation for dangling/wobble effect when caught
            is_caught = self.sprite_player.current_animation == "caught"
            
            painter.save()
            if is_caught:
                # Rotate back and forth, bounce up and down slightly
                wobble_angle = math.sin(time.time() * 12.0) * 8.0 # 8 degrees swing
                bounce_y = math.sin(time.time() * 18.0) * 3.0     # 3px bounce
                
                painter.translate(self.char_size / 2, self.char_size / 2 + bounce_y)
                painter.rotate(wobble_angle)
                painter.drawPixmap(-self.char_size / 2, -self.char_size / 2, scaled)
            else:
                painter.drawPixmap(0, 0, scaled)
            painter.restore()
            
        painter.end()

from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor
from PySide6.QtCore import QObject, Signal, Qt

class SystemTrayController(QSystemTrayIcon):
    open_settings_requested = Signal()
    exit_requested = Signal()
    pause_toggled = Signal(bool)
    mute_toggled = Signal(bool)
    character_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setToolTip("Desktop Buddy AI")
        self._is_paused = False
        self._is_muted = False
        
        # Setup dynamic tray icon
        self.setIcon(self._create_tray_icon())
        
        # Build menu
        self.menu = QMenu()
        self._build_menu()
        self.setContextMenu(self.menu)

    def _create_tray_icon(self) -> QIcon:
        """Draws a cute, circular smiley icon dynamically for the tray."""
        pix = QPixmap(32, 32)
        pix.fill(QColor(0, 0, 0, 0)) # transparent
        
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Yellow/orange cute face circle
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(135, 206, 250)) # pastel blue
        painter.drawEllipse(2, 2, 28, 28)
        
        # Gloss highlight
        painter.setBrush(QColor(255, 255, 255, 150))
        painter.drawEllipse(6, 6, 8, 8)
        
        # Eyes
        painter.setBrush(QColor(40, 40, 40))
        painter.drawEllipse(10, 12, 3, 4)
        painter.drawEllipse(19, 12, 3, 4)
        
        # Smile arc
        painter.setPen(QColor(40, 40, 40))
        painter.setBrush(Qt.NoBrush)
        painter.drawArc(11, 15, 10, 8, 0, -180 * 16)
        
        painter.end()
        return QIcon(pix)

    def _build_menu(self):
        self.menu.clear()
        
        # Pause/Resume Action
        pause_text = "Resume" if self._is_paused else "Pause"
        self.pause_action = self.menu.addAction(pause_text)
        self.pause_action.triggered.connect(self._toggle_pause)
        
        # Mute Action
        mute_text = "Unmute Sounds" if self._is_muted else "Mute Sounds"
        self.mute_action = self.menu.addAction(mute_text)
        self.mute_action.triggered.connect(self._toggle_mute)
        
        self.menu.addSeparator()
        
        # Characters Submenu
        char_menu = self.menu.addMenu("Change Character")
        slime_action = char_menu.addAction("Slippy (Slime)")
        slime_action.triggered.connect(lambda: self.character_changed.emit("slime"))
        cat_action = char_menu.addAction("Neko (Cat)")
        cat_action.triggered.connect(lambda: self.character_changed.emit("cat"))
        ironman_action = char_menu.addAction("Iron Buddy (Iron Man)")
        ironman_action.triggered.connect(lambda: self.character_changed.emit("ironman"))
        robobuddy_action = char_menu.addAction("Robo Buddy (Original)")
        robobuddy_action.triggered.connect(lambda: self.character_changed.emit("robobuddy"))
        
        self.menu.addSeparator()
        
        # Settings Action
        settings_action = self.menu.addAction("Settings...")
        settings_action.triggered.connect(self.open_settings_requested.emit)
        
        # Exit Action
        exit_action = self.menu.addAction("Exit")
        exit_action.triggered.connect(self.exit_requested.emit)

    def _toggle_pause(self):
        self._is_paused = not self._is_paused
        self.pause_toggled.emit(self._is_paused)
        self._build_menu()

    def _toggle_mute(self):
        self._is_muted = not self._is_muted
        self.mute_toggled.emit(self._is_muted)
        self._build_menu()
        
    def sync_settings(self, is_paused: bool, is_muted: bool):
        """Allows main window to sync internal tray states."""
        self._is_paused = is_paused
        self._is_muted = is_muted
        self._build_menu()

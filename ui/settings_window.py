from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QSlider, QCheckBox, QComboBox, QPushButton, 
                               QGroupBox, QFormLayout, QWidget)
from PySide6.QtCore import Qt, Signal
from settings.settings_manager import settings_manager

class SettingsWindow(QDialog):
    settings_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Buddy Settings")
        self.setMinimumSize(420, 560)
        # Frameless or standard dialog
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        self._setup_ui()
        self._load_current_settings()
        self._apply_qss()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Header Title
        self.header = QLabel("Desktop Buddy Configuration")
        self.header.setObjectName("headerLabel")
        self.header.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.header)

        # 1. Appearance Group
        appearance_group = QGroupBox("Appearance")
        form1 = QFormLayout(appearance_group)
        form1.setSpacing(10)

        self.char_combo = QComboBox()
        self.char_combo.addItems(["slime", "cat", "ironman", "robobuddy"])
        form1.addRow("Character Pack:", self.char_combo)

        # Size slider (40px to 120px)
        self.size_slider = QSlider(Qt.Horizontal)
        self.size_slider.setRange(40, 120)
        self.size_label = QLabel("64px")
        self.size_slider.valueChanged.connect(lambda v: self.size_label.setText(f"{v}px"))
        
        size_layout = QHBoxLayout()
        size_layout.addWidget(self.size_slider)
        size_layout.addWidget(self.size_label)
        form1.addRow("Buddy Size:", size_layout)

        # Opacity slider (20% to 100%)
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(20, 100)
        self.opacity_label = QLabel("100%")
        self.opacity_slider.valueChanged.connect(lambda v: self.opacity_label.setText(f"{v}%"))
        
        op_layout = QHBoxLayout()
        op_layout.addWidget(self.opacity_slider)
        op_layout.addWidget(self.opacity_label)
        form1.addRow("Opacity:", op_layout)

        main_layout.addWidget(appearance_group)

        # 2. Behavior Group
        behavior_group = QGroupBox("Behavior & Physics")
        form2 = QFormLayout(behavior_group)
        form2.setSpacing(10)

        # Personality
        self.personality_combo = QComboBox()
        self.personality_combo.addItems(["Friendly", "Shy", "Playful", "Lazy", "Hyper"])
        form2.addRow("Personality:", self.personality_combo)

        # Speed slider (50% to 200%)
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(50, 200)
        self.speed_label = QLabel("100%")
        self.speed_slider.valueChanged.connect(lambda v: self.speed_label.setText(f"{v}%"))
        
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(self.speed_slider)
        speed_layout.addWidget(self.speed_label)
        form2.addRow("Movement Speed:", speed_layout)

        # Animation FPS
        self.fps_combo = QComboBox()
        self.fps_combo.addItems(["8", "12", "16", "24"])
        form2.addRow("Animation FPS:", self.fps_combo)

        main_layout.addWidget(behavior_group)

        # 3. Toggles Group
        toggles_group = QGroupBox("System Preferences")
        grid_layout = QVBoxLayout(toggles_group)
        grid_layout.setSpacing(8)

        self.greet_chk = QCheckBox("Show Speeches/Greetings")
        self.always_on_top_chk = QCheckBox("Always On Top")
        self.click_through_chk = QCheckBox("Click Through (No Mouse Inputs)")
        self.auto_start_chk = QCheckBox("Start with Windows")
        self.mute_chk = QCheckBox("Mute Sounds")

        grid_layout.addWidget(self.greet_chk)
        grid_layout.addWidget(self.always_on_top_chk)
        grid_layout.addWidget(self.click_through_chk)
        grid_layout.addWidget(self.auto_start_chk)
        grid_layout.addWidget(self.mute_chk)

        main_layout.addWidget(toggles_group)

        # 4. Buttons (Save / Cancel)
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.save_btn = QPushButton("Save Settings")
        self.save_btn.clicked.connect(self._save_settings)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        
        main_layout.addLayout(btn_layout)

    def _load_current_settings(self):
        # Character
        self.char_combo.setCurrentText(settings_manager.get("character_pack", "slime"))
        
        # Size
        sz = settings_manager.get("size", 64)
        self.size_slider.setValue(sz)
        self.size_label.setText(f"{sz}px")
        
        # Opacity
        op = int(settings_manager.get("opacity", 1.0) * 100)
        self.opacity_slider.setValue(op)
        self.opacity_label.setText(f"{op}%")
        
        # Personality
        self.personality_combo.setCurrentText(settings_manager.get("personality", "Friendly"))
        
        # Speed
        spd = int(settings_manager.get("movement_speed", 1.0) * 100)
        self.speed_slider.setValue(spd)
        self.speed_label.setText(f"{spd}%")
        
        # FPS
        fps = str(settings_manager.get("animation_fps", 12))
        self.fps_combo.setCurrentText(fps)
        
        # Toggles
        self.greet_chk.setChecked(settings_manager.get("greeting_enabled", True))
        self.always_on_top_chk.setChecked(settings_manager.get("always_on_top", True))
        self.click_through_chk.setChecked(settings_manager.get("click_through", False))
        self.auto_start_chk.setChecked(settings_manager.get("auto_start", False))
        self.mute_chk.setChecked(settings_manager.get("mute", False))

    def _save_settings(self):
        # Save to sqlite manager
        settings_manager.set("character_pack", self.char_combo.currentText())
        settings_manager.set("size", self.size_slider.value())
        settings_manager.set("opacity", self.opacity_slider.value() / 100.0)
        settings_manager.set("personality", self.personality_combo.currentText())
        settings_manager.set("movement_speed", self.speed_slider.value() / 100.0)
        settings_manager.set("animation_fps", int(self.fps_combo.currentText()))
        
        settings_manager.set("greeting_enabled", self.greet_chk.isChecked())
        settings_manager.set("always_on_top", self.always_on_top_chk.isChecked())
        settings_manager.set("click_through", self.click_through_chk.isChecked())
        
        # Handle registry auto-start changes
        prev_auto = settings_manager.get("auto_start", False)
        new_auto = self.auto_start_chk.isChecked()
        if prev_auto != new_auto:
            from utils.windows_api import set_auto_start
            set_auto_start(new_auto)
            settings_manager.set("auto_start", new_auto)
            
        settings_manager.set("mute", self.mute_chk.isChecked())
        
        # Trigger global refresh
        self.settings_changed.emit()
        self.accept()

    def _apply_qss(self):
        """Applies a premium, modern dark stylesheet (CSS) for maximum visual appeal."""
        qss = """
        QDialog {
            background-color: #181825;
            color: #cdd6f4;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 13px;
        }
        
        #headerLabel {
            font-size: 18px;
            font-weight: bold;
            color: #b4befe;
            padding-bottom: 5px;
            border-bottom: 2px solid #313244;
        }
        
        QGroupBox {
            background-color: #1e1e2e;
            border: 1px solid #313244;
            border-radius: 8px;
            margin-top: 12px;
            font-weight: bold;
            color: #cdd6f4;
            padding: 15px;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 12px;
            padding: 0 4px;
            color: #b4befe;
        }
        
        QLabel {
            color: #a6adc8;
        }
        
        QComboBox {
            background-color: #313244;
            border: 1px solid #45475a;
            border-radius: 5px;
            padding: 5px 10px;
            color: #cdd6f4;
            min-width: 140px;
        }
        
        QComboBox::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 20px;
            border-left-width: 0px;
        }
        
        QSlider::groove:horizontal {
            border: 1px solid #45475a;
            height: 6px;
            background: #313244;
            margin: 2px 0;
            border-radius: 3px;
        }
        
        QSlider::handle:horizontal {
            background: #b4befe;
            border: none;
            width: 14px;
            height: 14px;
            margin: -4px 0;
            border-radius: 7px;
        }
        
        QSlider::handle:horizontal:hover {
            background: #a6e3a1;
        }
        
        QCheckBox {
            color: #cdd6f4;
            spacing: 8px;
        }
        
        QCheckBox::indicator {
            width: 18px;
            height: 18px;
            border-radius: 4px;
            border: 1px solid #45475a;
            background-color: #313244;
        }
        
        QCheckBox::indicator:checked {
            background-color: #b4befe;
            image: url(no_image_needed_draw_color);
            border-color: #b4befe;
        }
        
        QPushButton {
            background-color: #313244;
            color: #cdd6f4;
            border: 1px solid #45475a;
            border-radius: 6px;
            padding: 8px 16px;
            font-weight: bold;
        }
        
        QPushButton:hover {
            background-color: #b4befe;
            color: #11111b;
            border-color: #b4befe;
        }
        
        QPushButton#save_btn {
            background-color: #b4befe;
            color: #11111b;
        }
        
        QPushButton#save_btn:hover {
            background-color: #a6e3a1;
            color: #11111b;
        }
        """
        self.setStyleSheet(qss)
        self.save_btn.setObjectName("save_btn")

import sys
import math
import time
import random
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer, QPoint, QRect
from PySide6.QtGui import QPainter, QColor, QPixmap, QPen, QBrush, QCursor, QTransform, QGuiApplication, QRegion, QPainterPath

class SpiderWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setStyleSheet("background: transparent; border: none;")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        
        # Position window in the top-right corner
        self.window_w = 460
        self.window_h = 600
        self.resize(self.window_w, self.window_h)
        self.reposition_window()
        
        self.spider_pixmap = QPixmap("assets/characters/spider/spider.png")
        if self.spider_pixmap.isNull():
            self.spider_pixmap = QPixmap(64, 64)
            self.spider_pixmap.fill(Qt.transparent)
            painter = QPainter(self.spider_pixmap)
            painter.setBrush(QColor(30, 30, 30))
            painter.drawEllipse(16, 16, 32, 32)
            painter.end()
            
        self.spider_w = 72
        self.spider_h = 72
        
        # Anchor point for web thread
        self.anchor_x = 230.0
        self.anchor_y = 0.0
        
        # Resting kinematics states
        self.rest_len = 160.0
        self.sx = 230.0
        self.sy = self.rest_len
        self.vx = 0.0
        self.vy = 0.0
        
        # Spring coefficients
        self.k = 220.0      # Base spring constant (Hooke's Law stiffness)
        self.c = 3.8        # Damping coefficient (momentum decay)
        self.mass = 1.0     # Mass
        self.gravity = 250.0
        
        # Interaction states
        self.grab_mode = False
        self.is_dragging = False
        self.drag_offset_x = 0.0
        self.drag_offset_y = 0.0
        
        # Animation states
        self.blink_timer = random.uniform(2.0, 5.0)
        self.is_blinking = False
        self.blink_duration = 0.0
        
        # Loop ticker
        self.last_time = time.perf_counter()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_physics)
        self.timer.start(16)
        
        QGuiApplication.primaryScreen().geometryChanged.connect(self.reposition_window)
        self.show()

    def reposition_window(self):
        screen = QGuiApplication.primaryScreen()
        rect = screen.availableGeometry()
        self.move(rect.x() + rect.width() - self.window_w, rect.y())

    def update_physics(self):
        now = time.perf_counter()
        dt = now - self.last_time
        self.last_time = now
        dt = min(0.05, dt)
        
        # Blink animation timer
        self.blink_timer -= dt
        if self.blink_timer <= 0.0:
            if not self.is_blinking:
                self.is_blinking = True
                self.blink_duration = 0.12
            else:
                self.blink_duration -= dt
                if self.blink_duration <= 0.0:
                    self.is_blinking = False
                    self.blink_timer = random.uniform(2.5, 6.0)

        # Physics simulation
        if self.is_dragging:
            raw_mouse = self.mapFromGlobal(QCursor.pos())
            target_x = raw_mouse.x() - self.drag_offset_x
            target_y = raw_mouse.y() - self.drag_offset_y
            
            # Non-linear pull resistance calculations
            dx = target_x - self.anchor_x
            dy = target_y - self.anchor_y
            dist = math.hypot(dx, dy)
            
            # Clamp bounds
            max_stretch = 280.0
            if dist > max_stretch:
                # Progressive stiffening resistance
                resistance = 0.12
                elastic_dist = max_stretch + (dist - max_stretch) * resistance
                # Hard limit
                elastic_dist = min(360.0, elastic_dist)
                
                self.sx = self.anchor_x + (dx / dist) * elastic_dist
                self.sy = self.anchor_y + (dy / dist) * elastic_dist
            else:
                self.sx = target_x
                self.sy = target_y
                
            self.vx = 0.0
            self.vy = 0.0
        else:
            # Anchor pull vectors
            dx = self.sx - self.anchor_x
            dy = self.sy - self.anchor_y
            dist = math.hypot(dx, dy)
            
            if dist > 0.0:
                extension = dist - self.rest_len
                # Non-linear spring stiffness (hardening spring force)
                # Small pull: easy to stretch. Large pull: extremely stiff.
                spring_stiffness = self.k
                if extension > 50.0:
                    spring_stiffness *= (1.0 + ((extension - 50.0) / 100.0) ** 2)
                    
                f_spring = -spring_stiffness * extension
                fx_spring = f_spring * (dx / dist)
                fy_spring = f_spring * (dy / dist)
            else:
                fx_spring = 0.0
                fy_spring = 0.0
                
            # c * v damping resistance forces
            fx_damping = -self.c * self.vx
            fy_damping = -self.c * self.vy
            
            # Gravity
            fy_gravity = self.gravity
            
            # Gentle perpetual idle breeze
            wind_x = math.sin(time.time() * 2.2) * 12.0
            wind_y = math.cos(time.time() * 1.6) * 5.0
            
            ax = (fx_spring + fx_damping + wind_x) / self.mass
            ay = (fy_spring + fy_damping + fy_gravity + wind_y) / self.mass
            
            self.vx += ax * dt
            self.vy += ay * dt
            self.sx += self.vx * dt
            self.sy += self.vy * dt
            
        self.update_mask()
        self.update()

    def update_mask(self):
        """Dynamic masking region updates for perfect pass-through click mapping."""
        # Spider bounding box with a margin for rotation/squash stretching
        margin = 25
        sp_rect = QRect(
            int(self.sx - self.spider_w / 2 - margin),
            int(self.sy - self.spider_h / 2 - margin),
            self.spider_w + margin * 2,
            self.spider_h + margin * 2
        )
        
        # Thread bounding area
        min_x = int(min(self.anchor_x, self.sx) - 6)
        max_x = int(max(self.anchor_x, self.sx) + 6)
        min_y = int(min(self.anchor_y, self.sy))
        max_y = int(max(self.anchor_y, self.sy))
        thread_rect = QRect(min_x, min_y, max(1, max_x - min_x), max(1, max_y - min_y))
        
        region = QRegion(sp_rect).united(QRegion(thread_rect))
        self.setMask(region)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            local_pos = event.position()
            dist = math.hypot(local_pos.x() - self.sx, local_pos.y() - self.sy)
            if dist < self.spider_w / 2 + 15:
                self.grab_mode = True
                self.is_dragging = True
                self.drag_offset_x = local_pos.x() - self.sx
                self.drag_offset_y = local_pos.y() - self.sy
                self.last_double_click_time = time.time()
                self.setCursor(Qt.ClosedHandCursor)
                event.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            local_pos = event.position()
            dist = math.hypot(local_pos.x() - self.sx, local_pos.y() - self.sy)
            
            # If already dragging (sticky mode), click drops it
            if self.is_dragging:
                self.is_dragging = False
                self.grab_mode = False
                self.setCursor(Qt.ArrowCursor)
                event.accept()
                return
                
            # If in Grab Mode, click-hold grabs it
            if self.grab_mode:
                if dist < self.spider_w / 2 + 15:
                    self.is_dragging = True
                    self.drag_offset_x = local_pos.x() - self.sx
                    self.drag_offset_y = local_pos.y() - self.sy
                    self.setCursor(Qt.ClosedHandCursor)
                    event.accept()

    def mouseMoveEvent(self, event):
        if self.grab_mode and self.is_dragging:
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.is_dragging:
            # Pattern A release: drop only if not the immediate release of the double-click
            double_click_dt = time.time() - getattr(self, "last_double_click_time", 0.0)
            if double_click_dt < 0.25:
                # Keep active dragging, let it follow mouse without holding (Pattern B sticky mode)
                event.accept()
                return
                
            # Normal release ending a long drag
            self.is_dragging = False
            self.grab_mode = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Transparent base
        painter.setCompositionMode(QPainter.CompositionMode_Source)
        painter.fillRect(self.rect(), Qt.transparent)
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        
        dx = self.sx - self.anchor_x
        dy = self.sy - self.anchor_y
        thread_len = math.hypot(dx, dy)
        
        # Silk thread gets thinner under tension
        base_thickness = 2.2
        stretched_thickness = max(0.5, base_thickness - max(0.0, thread_len - self.rest_len) * 0.004)
        
        # Calculate angle perpendicular to thread for oscillations
        perp_dx = -dy / thread_len if thread_len > 0 else 0.0
        perp_dy = dx / thread_len if thread_len > 0 else 1.0
        
        # High frequency oscillations proportional to tension
        tension = max(0.0, thread_len - self.rest_len)
        osc_amp = min(5.0, tension * 0.03) * math.sin(time.time() * 32.0)
        
        # Generate thread path with gravity sag, velocity inertia, and vibration oscillations
        path = QPainterPath()
        path.moveTo(self.anchor_x, self.anchor_y)
        
        N = 24
        for i in range(1, N + 1):
            t = i / N
            px = self.anchor_x + dx * t
            py = self.anchor_y + dy * t
            
            # sag offsets (max in middle)
            sag = 4.0 * t * (1.0 - t)
            curve_offset_x = -self.vx * 0.04 * sag
            curve_offset_y = 6.0 * sag
            
            # Vibration wave
            vibration = math.sin(t * math.pi * 3.0) * osc_amp * sag
            
            path.lineTo(px + curve_offset_x + perp_dx * vibration, py + curve_offset_y + perp_dy * vibration)
            
        # Draw silk thread line
        pen = QPen(QColor(220, 220, 220, 185))
        pen.setWidthF(stretched_thickness)
        painter.setPen(pen)
        painter.drawPath(path)
        
        # Calculate Squash and Stretch ratios (body deformation under tension)
        scale_x = 1.0
        scale_y = 1.0
        
        if thread_len > self.rest_len:
            ratio = thread_len / self.rest_len
            scale_y = 1.0 + min(0.28, (ratio - 1.0) * 0.35)  # stretch along thread
            scale_x = 1.0 - min(0.14, (ratio - 1.0) * 0.18)  # squash perpendicular
            
        # Get thread rotation angle
        angle = 0.0
        if dy > 0.0:
            angle = math.degrees(math.atan2(dy, dx) - math.pi/2)
            
        # Draw Soft Drop Shadow
        painter.save()
        painter.translate(self.sx + 6, self.sy + 6)
        painter.rotate(angle)
        painter.scale(scale_x, scale_y)
        # Apply extra high speed wiggling scaling to legs
        leg_wiggle = 0.0
        if self.is_dragging or math.hypot(self.vx, self.vy) > 35.0:
            leg_wiggle = math.sin(time.time() * 26.0) * 0.04
        painter.scale(1.0 + leg_wiggle, 1.0)
        
        painter.setOpacity(0.16)
        painter.drawPixmap(-self.spider_w / 2, -self.spider_h / 2, self.spider_pixmap)
        painter.restore()
        
        # Draw Spider body
        painter.save()
        painter.translate(self.sx, self.sy)
        painter.rotate(angle)
        painter.scale(scale_x, scale_y)
        painter.scale(1.0 + leg_wiggle, 1.0)
        
        painter.drawPixmap(-self.spider_w / 2, -self.spider_h / 2, self.spider_pixmap)
        
        # Cute Blinking Overlay
        if self.is_blinking:
            painter.setPen(QPen(QColor(20, 20, 20), 3.2, Qt.SolidLine, Qt.RoundCap))
            painter.setBrush(Qt.NoBrush)
            painter.drawArc(-14, -6, 10, 8, 0, 180 * 16)
            painter.drawArc(4, -6, 10, 8, 0, 180 * 16)
            
        painter.restore()
        painter.end()

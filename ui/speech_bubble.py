from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QFont, QPen, QBrush
from PySide6.QtCore import QRectF, Qt, QPointF

class SpeechBubbleWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Frameless, always on top, tool window (no taskbar presence)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)  # Clicks pass through
        self.setStyleSheet("background: transparent; border: none;")
        
        self.text = ""
        self.lifetime = 0.0
        self.max_lifetime = 2.0
        self.opacity = 0.0
        
        self.font = QFont("Segoe UI", 9, QFont.Bold)
        self.padding_h = 10
        self.padding_v = 6
        self.arrow_height = 8
        self.hide()
        
    def set_text(self, text: str, duration: float = 2.0):
        self.text = text
        self.lifetime = duration
        self.max_lifetime = duration
        self.opacity = 1.0
        
        # Calculate sizing boundaries
        from PySide6.QtGui import QFontMetrics
        metrics = QFontMetrics(self.font)
        text_w = metrics.horizontalAdvance(self.text)
        text_h = metrics.height()
        
        # Horizontal clamp
        bubble_w = text_w + self.padding_h * 2
        bubble_h = text_h + self.padding_v * 2
        
        max_bubble_w = 180
        if bubble_w > max_bubble_w:
            bubble_w = max_bubble_w
            from PySide6.QtCore import QRect
            rect = metrics.boundingRect(QRect(0, 0, int(bubble_w - self.padding_h*2), 200), int(Qt.TextWordWrap), self.text)
            bubble_h = rect.height() + self.padding_v * 2
            
        self.bubble_w = bubble_w
        self.bubble_h = bubble_h
        
        self.resize(self.bubble_w + 10, self.bubble_h + self.arrow_height + 10)
        self.show()
        self.update()

    def is_visible(self) -> bool:
        return self.lifetime > 0.0

    def update_timer(self, dt: float):
        if self.lifetime > 0.0:
            self.lifetime -= dt
            if self.lifetime <= 0.0:
                self.lifetime = 0.0
                self.opacity = 0.0
                self.hide()
            elif self.lifetime < 0.4:
                self.opacity = self.lifetime / 0.4
            else:
                self.opacity = 1.0
            self.update()

    def follow_buddy(self, buddy_x: int, buddy_y: int, buddy_w: int):
        """Positions speech bubble dynamically centered above the buddy window."""
        if not self.isVisible() or self.lifetime <= 0.0:
            return
            
        bx = buddy_x + buddy_w / 2
        by = buddy_y
        
        bubble_x = int(bx - self.width() / 2)
        bubble_y = int(by - self.height() - 4)
        
        self.move(bubble_x, bubble_y)

    def paintEvent(self, event):
        if self.lifetime <= 0.0 or not self.text:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setOpacity(self.opacity)
        
        body_x = 2
        body_y = 2
        body_w = self.width() - 4
        body_h = self.height() - self.arrow_height - 4
        
        border_pen = QPen(QColor(40, 40, 40, 240), 2)
        bubble_brush = QBrush(QColor(255, 255, 255, 245))
        
        painter.setPen(border_pen)
        painter.setBrush(bubble_brush)
        
        # Draw rounded body
        body_rect = QRectF(body_x, body_y, body_w, body_h)
        painter.drawRoundedRect(body_rect, 8.0, 8.0)
        
        # Draw pointer arrow
        arrow_x = self.width() / 2
        arrow_pts = [
            QPointF(arrow_x - 6, body_y + body_h),
            QPointF(arrow_x + 6, body_y + body_h),
            QPointF(arrow_x, body_y + body_h + self.arrow_height)
        ]
        
        painter.setPen(Qt.NoPen)
        painter.drawPolygon(arrow_pts)
        
        painter.setPen(border_pen)
        painter.drawLine(arrow_pts[0], arrow_pts[2])
        painter.drawLine(arrow_pts[1], arrow_pts[2])
        
        # Draw text
        painter.setPen(QColor(30, 30, 30))
        painter.setFont(self.font)
        text_rect = QRectF(body_x + self.padding_h, body_y + self.padding_v, body_w - self.padding_h*2, body_h - self.padding_v*2)
        painter.drawText(text_rect, Qt.AlignCenter | Qt.TextWordWrap, self.text)
        
        painter.end()

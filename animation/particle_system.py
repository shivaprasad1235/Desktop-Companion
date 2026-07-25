import random
import math
from PySide6.QtGui import QPainter, QColor, QFont
from PySide6.QtCore import QPointF, Qt

class Particle:
    def __init__(self, x: float, y: float, vx: float, vy: float, size: float, color: QColor, lifetime: float, p_type: str = "dust", text: str = ""):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.size = size
        self.color = color
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.p_type = p_type
        self.text = text

class ParticleSystem:
    def __init__(self):
        self.particles = []

    def spawn_dust(self, x: float, y: float, count: int = 5):
        """Spawns light grey dust puffs at the bottom of the character."""
        for _ in range(count):
            vx = random.uniform(-40.0, 40.0)
            vy = random.uniform(-10.0, -30.0)
            size = random.uniform(3.0, 7.0)
            lifetime = random.uniform(0.4, 0.8)
            color = QColor(240, 240, 240, 180)
            self.particles.append(Particle(x, y, vx, vy, size, color, lifetime, "dust"))

    def spawn_sparkles(self, x: float, y: float, count: int = 6):
        """Spawns golden sparkling stars/diamonds bursting outwards."""
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(30.0, 90.0)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed - 20.0  # boost upwards slightly
            size = random.uniform(4.0, 8.0)
            lifetime = random.uniform(0.5, 1.0)
            # Golden palette
            color = QColor(255, random.choice([215, 223, 230]), 0, 255)
            self.particles.append(Particle(x, y, vx, vy, size, color, lifetime, "sparkle"))

    def spawn_zzz(self, x: float, y: float):
        """Spawns a floating 'Z' character for the sleeping state."""
        vx = random.uniform(-15.0, 15.0)
        vy = random.uniform(-25.0, -45.0)
        size = random.uniform(10.0, 16.0)
        lifetime = random.uniform(1.5, 2.5)
        # Lavender/purple sleep color
        color = QColor(180, 160, 255, 200)
        self.particles.append(Particle(x, y, vx, vy, size, color, lifetime, "zzz", "Z"))

    def update(self, dt: float):
        """Ticks particles and removes expired ones."""
        active = []
        for p in self.particles:
            p.lifetime -= dt
            if p.lifetime > 0:
                p.x += p.vx * dt
                p.y += p.vy * dt
                
                # Apply small drag/gravity modifications based on type
                if p.p_type == "dust":
                    p.vy += 10.0 * dt  # drift down slowly
                elif p.p_type == "zzz":
                    # Wave float
                    p.vx += math.sin(p.lifetime * 5.0) * 1.5
                    
                active.append(p)
        self.particles = active

    def draw(self, painter: QPainter):
        """Draws all active particles on the buddy canvas."""
        # Enable anti-aliasing
        painter.setRenderHint(QPainter.Antialiasing)
        
        for p in self.particles:
            alpha = int(max(0, min(255, (p.lifetime / p.max_lifetime) * p.color.alpha())))
            color = QColor(p.color.red(), p.color.green(), p.color.blue(), alpha)
            
            painter.setPen(Qt.NoPen)
            painter.setBrush(color)
            
            if p.p_type == "dust":
                # Draw soft circles
                painter.drawEllipse(QPointF(p.x, p.y), p.size, p.size)
                
            elif p.p_type == "sparkle":
                # Draw 4-point stars or diamond shapes
                half = p.size / 2.0
                pts = [
                    QPointF(p.x, p.y - p.size),
                    QPointF(p.x + half, p.y),
                    QPointF(p.x, p.y + p.size),
                    QPointF(p.x - half, p.y)
                ]
                painter.drawPolygon(pts)
                
            elif p.p_type == "zzz":
                # Draw text
                painter.setPen(color)
                font = QFont("Arial", int(p.size), QFont.Bold)
                painter.setFont(font)
                # Adjust offset for letters
                painter.drawText(QPointF(p.x, p.y), p.text)

import time

class MoodSystem:
    def __init__(self):
        self.joy = 0.5        # 0.0 (sad/angry) to 1.0 (ecstatic)
        self.fear = 0.0       # 0.0 (calm) to 1.0 (terrified)
        self.fatigue = 0.0    # 0.0 (energetic) to 1.0 (exhausted)
        self.last_update = time.time()

    def update(self, dt: float, is_moving: bool, is_system_idle: bool):
        """Ticks mood values over time."""
        # Fatigue increases when moving, decays when resting or system is idle
        if is_moving:
            self.fatigue = min(1.0, self.fatigue + 0.015 * dt)
        else:
            # resting decays fatigue
            self.fatigue = max(0.0, self.fatigue - 0.02 * dt)
            
        if is_system_idle:
            # decays fatigue even faster, joy returns to neutral
            self.fatigue = max(0.0, self.fatigue - 0.05 * dt)
            
        # Fear decays naturally
        self.fear = max(0.0, self.fear - 0.15 * dt)
        
        # Joy slowly approaches neutral (0.5) over time
        if self.joy > 0.5:
            self.joy = max(0.5, self.joy - 0.01 * dt)
        elif self.joy < 0.5:
            self.joy = min(0.5, self.joy + 0.01 * dt)

    def trigger_fear(self, intensity: float):
        self.fear = min(1.0, self.fear + intensity)
        self.joy = max(0.0, self.joy - intensity * 0.5)

    def trigger_joy(self, intensity: float):
        self.joy = min(1.0, self.joy + intensity)
        self.fear = max(0.0, self.fear - intensity * 0.8)

    def get_current_mood_state(self) -> str:
        """Returns the dominant mood string for animation selector."""
        if self.fear > 0.4:
            return "scared"
        if self.fatigue > 0.75:
            return "sleepy"
        if self.joy > 0.75:
            return "happy"
        if self.joy < 0.25:
            return "sad"
        return "normal"

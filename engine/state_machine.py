from settings.settings_manager import settings_manager

class SystemStateMachine:
    def __init__(self):
        # Sync with database settings
        self.paused = settings_manager.get("paused", False)
        self.mute = settings_manager.get("mute", False)

    def is_paused(self) -> bool:
        self.paused = settings_manager.get("paused", False)
        return self.paused

    def is_muted(self) -> bool:
        self.mute = settings_manager.get("mute", False)
        return self.mute

    def toggle_pause(self):
        new_state = not self.is_paused()
        settings_manager.set("paused", new_state)
        self.paused = new_state

    def toggle_mute(self):
        new_state = not self.is_muted()
        settings_manager.set("mute", new_state)
        self.mute = new_state

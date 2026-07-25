from engine.event_bus import event_bus

class BasePlugin:
    def __init__(self, name: str):
        self.name = name
        self.event_bus = event_bus
        self.enabled = True

    def initialize(self):
        """Called on plugin load. Override to setup timers or subscribe to events."""
        pass

    def shutdown(self):
        """Called on application exit. Clean up resources here."""
        pass

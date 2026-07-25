class EventBus:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EventBus, cls).__new__(cls)
            cls._instance._listeners = {}
        return cls._instance

    def subscribe(self, event_type: str, callback):
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        if callback not in self._listeners[event_type]:
            self._listeners[event_type].append(callback)

    def unsubscribe(self, event_type: str, callback):
        if event_type in self._listeners and callback in self._listeners[event_type]:
            self._listeners[event_type].remove(callback)

    def publish(self, event_type: str, *args, **kwargs):
        if event_type in self._listeners:
            # Create a copy of listeners to prevent issues if listeners subscribe/unsubscribe during notification
            for callback in list(self._listeners[event_type]):
                try:
                    callback(*args, **kwargs)
                except Exception as e:
                    print(f"Error executing callback for event {event_type}: {e}")

# Global instance for easy import
event_bus = EventBus()

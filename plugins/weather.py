import urllib.request
import json
import random
from PySide6.QtCore import QThread, Signal, QTimer
from plugins.base_plugin import BasePlugin
from engine.event_bus import event_bus

class WeatherFetcherThread(QThread):
    finished = Signal(str)

    def run(self):
        try:
            # Fetch simple text format from wttr.in (e.g. "Paris: ⛅ +14°C")
            # wttr.in format=3 is very compact
            req = urllib.request.Request(
                "https://wttr.in/?format=3",
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            with urllib.request.urlopen(req, timeout=4.0) as response:
                result = response.read().decode('utf-8').strip()
                if result:
                    self.finished.emit(result)
        except Exception as e:
            # Fail silently, fallback to simulated
            self.finished.emit("")

class WeatherPlugin(BasePlugin):
    def __init__(self):
        super().__init__("Weather")
        self.timer = None
        self.fetcher = None
        self.last_weather = ""

    def initialize(self):
        # Initial check after 5 seconds to let app boot smoothly
        QTimer.singleShot(5000, self.fetch_weather)
        
        # Check every 40 minutes
        self.timer = QTimer()
        self.timer.timeout.connect(self.fetch_weather)
        self.timer.start(40 * 60 * 1000)

    def shutdown(self):
        if self.timer:
            self.timer.stop()
        if self.fetcher and self.fetcher.isRunning():
            self.fetcher.wait()

    def fetch_weather(self):
        self.fetcher = WeatherFetcherThread()
        self.fetcher.finished.connect(self.on_weather_fetched)
        self.fetcher.start()

    def on_weather_fetched(self, weather_str: str):
        if weather_str:
            self.last_weather = weather_str
            # Cute greeting with weather info
            if random.random() < 0.3:
                event_bus.publish("trigger_speech", f"Outside check: {weather_str}! 🌦️")
        else:
            # Simulated weather fallback based on time of day
            from datetime import datetime
            hour = datetime.now().hour
            simulated = "Sunny sky ☀️"
            if 18 <= hour or hour < 6:
                simulated = "Clear night sky 🌌"
            elif 12 <= hour < 16:
                simulated = "Bright and sunny ☀️"
            elif 6 <= hour < 9:
                simulated = "Beautiful morning breeze 🌅"
                
            self.last_weather = simulated
            if random.random() < 0.2:
                event_bus.publish("trigger_speech", f"Simulated report: {simulated}!")

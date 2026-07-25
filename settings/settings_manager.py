import json
import os
import sqlite3

class SettingsManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SettingsManager, cls).__new__(cls)
            cls._instance._init_db()
        return cls._instance

    def _init_db(self):
        # We put settings.db in the root folder or appdata
        self.db_path = "settings.db"
        self.config_path = "config.json"
        
        # Load defaults from config.json if available
        self.defaults = {}
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    self.defaults = json.load(f)
            except Exception as e:
                print(f"Error loading defaults from config.json: {e}")

        # Connect to DB and run schema
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Read and execute schema
        schema_path = os.path.join("database", "schema.sql")
        if os.path.exists(schema_path):
            with open(schema_path, "r") as f:
                schema_sql = f.read()
            cursor.executescript(schema_sql)
        else:
            # Fallback inline schema
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
        conn.commit()
        conn.close()

    def get(self, key: str, default=None):
        # First check database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        conn.close()
        
        if row is not None:
            val = row[0]
            # Infer type based on default value or original setting
            # We map types accordingly
            fallback_val = default if default is not None else self.defaults.get(key)
            if fallback_val is not None:
                if isinstance(fallback_val, bool):
                    return val in ("1", "true", "True")
                elif isinstance(fallback_val, int):
                    try:
                        return int(val)
                    except ValueError:
                        pass
                elif isinstance(fallback_val, float):
                    try:
                        return float(val)
                    except ValueError:
                        pass
            return val
            
        # Fallback to config.json
        if default is not None:
            return default
        return self.defaults.get(key)

    def set(self, key: str, value):
        # Convert type to string for storage
        if isinstance(value, bool):
            str_val = "1" if value else "0"
        else:
            str_val = str(value)
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str_val))
        conn.commit()
        conn.close()
        
        # Also notify via Event Bus if imported (to avoid circular imports, import locally or publish)
        # Event Bus can be notified about changes
        try:
            from engine.event_bus import event_bus
            event_bus.publish(f"setting_changed_{key}", value)
            event_bus.publish("setting_changed", key, value)
        except Exception:
            pass

# Global instance
settings_manager = SettingsManager()

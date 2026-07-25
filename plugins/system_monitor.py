import ctypes
import random
from PySide6.QtCore import QTimer
from plugins.base_plugin import BasePlugin
from engine.event_bus import event_bus

# Windows API Structures
class SYSTEM_POWER_STATUS(ctypes.Structure):
    _fields_ = [
        ("ACLineStatus", ctypes.c_byte),
        ("BatteryFlag", ctypes.c_byte),
        ("BatteryLifePercent", ctypes.c_byte),
        ("Reserved1", ctypes.c_byte),
        ("BatteryLifeTime", ctypes.c_ulong),
        ("BatteryFullLifeTime", ctypes.c_ulong)
    ]

class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong)
    ]

class FILETIME(ctypes.Structure):
    _fields_ = [
        ("dwLowDateTime", ctypes.c_ulong),
        ("dwHighDateTime", ctypes.c_ulong)
    ]

class SystemMonitorPlugin(BasePlugin):
    def __init__(self):
        super().__init__("SystemMonitor")
        self.timer = None
        
        # CPU tracking state
        self.prev_idle = 0
        self.prev_kernel = 0
        self.prev_user = 0
        
        # Low battery warning trigger flag
        self.warned_low_battery = False

    def initialize(self):
        # Initial call to CPU times
        self._get_cpu_times()
        
        # Check every 25 seconds
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_system)
        self.timer.start(25000)

    def shutdown(self):
        if self.timer:
            self.timer.stop()

    def check_system(self):
        # 1. Get RAM load
        ram_load = self._get_ram_load()
        
        # 2. Get Battery percentage
        battery_pct, is_charging = self._get_battery_status()
        
        # 3. Get CPU load
        cpu_load = self._get_cpu_load()

        # Trigger speech comments based on metrics
        # Low Battery Check
        if battery_pct < 20 and not is_charging and not self.warned_low_battery:
            self.warned_low_battery = True
            event_bus.publish("trigger_speech", f"Low battery! ({battery_pct}%) Charge me... I mean your laptop! 😂")
        elif is_charging:
            self.warned_low_battery = False # reset warning
            
        # High memory warning
        elif ram_load > 85:
            if random.random() < 0.5:
                event_bus.publish("trigger_speech", f"Woah, RAM is at {ram_load}%! Coding hard or Chrome tabs? 💻")
                
        # High CPU check
        elif cpu_load > 80:
            event_bus.publish("trigger_speech", f"Phew! CPU is working hot at {int(cpu_load)}%! ⚡")
            
        # Random status check (5% chance every 25s)
        elif random.random() < 0.05:
            if random.random() < 0.5:
                event_bus.publish("trigger_speech", f"Everything looks smooth! RAM: {ram_load}%.")

    def _get_ram_load(self) -> int:
        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
            return stat.dwMemoryLoad
        return 0

    def _get_battery_status(self) -> tuple:
        """Returns (percent, is_charging)."""
        status = SYSTEM_POWER_STATUS()
        if ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(status)):
            # ACLineStatus: 1 means online/charging
            is_charging = status.ACLineStatus == 1
            return int(status.BatteryLifePercent), is_charging
        return 100, True

    def _get_cpu_times(self) -> tuple:
        idle = FILETIME()
        kernel = FILETIME()
        user = FILETIME()
        
        if ctypes.windll.kernel32.GetSystemTimes(ctypes.byref(idle), ctypes.byref(kernel), ctypes.byref(user)):
            # Convert FILETIME structures to 64-bit integers
            idle_val = (idle.dwHighDateTime << 32) + idle.dwLowDateTime
            kernel_val = (kernel.dwHighDateTime << 32) + kernel.dwLowDateTime
            user_val = (user.dwHighDateTime << 32) + user.dwLowDateTime
            return idle_val, kernel_val, user_val
        return 0, 0, 0

    def _get_cpu_load(self) -> float:
        idle, kernel, user = self._get_cpu_times()
        
        # Calculate delta
        d_idle = idle - self.prev_idle
        d_kernel = kernel - self.prev_kernel
        d_user = user - self.prev_user
        
        # Update cache
        self.prev_idle = idle
        self.prev_kernel = kernel
        self.prev_user = user
        
        total = d_kernel + d_user
        if total == 0:
            return 0.0
            
        # CPU Load = (Total - Idle) / Total
        cpu = ((total - d_idle) / total) * 100.0
        return max(0.0, min(100.0, cpu))

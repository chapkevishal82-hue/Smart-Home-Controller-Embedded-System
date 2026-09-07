"""
Smart Home Controller - Core Automation State Machine

Simulates the embedded logic that would run on the Arduino/ESP32:
PIR motion + LDR + temperature sensor reads, automatic light/fan control,
security alarm, and manual override — with the same priority rules as
the real firmware: SECURITY > MANUAL > AUTOMATIC.
"""

import csv
import os
import threading
import time
from datetime import datetime

CSV_PATH = os.path.join(os.path.dirname(__file__), "event_log.csv")

# ---- Thresholds (mirrors firmware constants) ----
DARK_THRESHOLD = 40          # light_level (%) below this = "dark"
TEMP_ON_THRESHOLD = 28.0     # fan turns ON above this
TEMP_OFF_THRESHOLD = 26.0    # fan turns OFF below this (hysteresis gap)
MOTION_LIGHT_TIMEOUT = 6     # seconds light stays on after last motion


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class SmartHomeState:
    def __init__(self):
        self.lock = threading.Lock()

        # Sensor inputs (simulated)
        self.light_level = 55.0      # % brightness, 0=dark 100=bright
        self.temperature = 24.0      # deg C
        self.motion = False
        self.last_motion_at = 0.0

        # Modes
        self.security_mode = False
        self.manual_override = False
        self.manual_light = False
        self.manual_fan = False

        # Outputs
        self.light_on = False
        self.fan_on = False
        self.buzzer = False
        self.security_alert = False
        self.status_message = "System nominal"

        self.events = []
        self._init_csv()
        self._log_event("SYSTEM_START", "Smart Home Controller initialized.")
        self._apply_rules()

    def _init_csv(self):
        if not os.path.exists(CSV_PATH):
            with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow(["timestamp", "event", "detail"])

    def _log_event(self, event, detail):
        row = {"timestamp": _now(), "event": event, "detail": detail}
        self.events.insert(0, row)
        self.events = self.events[:50]
        with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([row["timestamp"], row["event"], row["detail"]])

    # ---------------- Sensor input setters ----------------
    def set_light_level(self, value):
        with self.lock:
            self.light_level = max(0.0, min(100.0, float(value)))
            self._apply_rules()
            return self.snapshot()

    def set_temperature(self, value):
        with self.lock:
            self.temperature = max(-10.0, min(60.0, float(value)))
            self._apply_rules()
            return self.snapshot()

    def trigger_motion(self):
        with self.lock:
            self.motion = True
            self.last_motion_at = time.time()
            self._apply_rules()
            return self.snapshot()

    def set_security_mode(self, enabled):
        with self.lock:
            self.security_mode = bool(enabled)
            self._log_event(
                "SECURITY_MODE", f"Security mode turned {'ON' if enabled else 'OFF'}."
            )
            self._apply_rules()
            return self.snapshot()

    def set_manual_override(self, enabled):
        with self.lock:
            self.manual_override = bool(enabled)
            self._log_event(
                "MANUAL_OVERRIDE", f"Manual override turned {'ON' if enabled else 'OFF'}."
            )
            self._apply_rules()
            return self.snapshot()

    def set_manual_device(self, device, state):
        with self.lock:
            if device == "light":
                self.manual_light = bool(state)
            elif device == "fan":
                self.manual_fan = bool(state)
            self._apply_rules()
            return self.snapshot()

    def reset(self):
        with self.lock:
            self.light_level = 55.0
            self.temperature = 24.0
            self.motion = False
            self.last_motion_at = 0.0
            self.security_mode = False
            self.manual_override = False
            self.manual_light = False
            self.manual_fan = False
            self._log_event("MANUAL_RESET", "System reset to default state.")
            self._apply_rules()
            return self.snapshot()

    # ---------------- Core control logic ----------------
    def _apply_rules(self):
        now = time.time()

        # Motion decays after timeout (mirrors PIR "no motion" transition)
        if self.motion and (now - self.last_motion_at) > MOTION_LIGHT_TIMEOUT:
            self.motion = False

        prev_light, prev_fan, prev_buzzer, prev_alert = (
            self.light_on, self.fan_on, self.buzzer, self.security_alert,
        )

        # ---- PRIORITY 1: SECURITY (always wins) ----
        if self.security_mode and self.motion:
            self.security_alert = True
            self.buzzer = True
            self.status_message = "INTRUDER ALERT"
        else:
            self.security_alert = False
            self.buzzer = False

        # ---- PRIORITY 2: MANUAL OVERRIDE ----
        if self.manual_override:
            self.light_on = self.manual_light
            self.fan_on = self.manual_fan
            if not self.security_alert:
                self.status_message = "Manual control active"
        else:
            # ---- PRIORITY 3: AUTOMATIC RULES ----
            # Rule 1: automatic light -> motion AND dark
            if self.motion and self.light_level < DARK_THRESHOLD:
                self.light_on = True
            elif not self.motion:
                self.light_on = False

            # Rule 2: automatic fan with hysteresis
            if self.temperature > TEMP_ON_THRESHOLD:
                self.fan_on = True
            elif self.temperature < TEMP_OFF_THRESHOLD:
                self.fan_on = False

            if not self.security_alert:
                self.status_message = "Automatic mode"

        # ---- Event logging on state transitions ----
        if self.light_on != prev_light:
            self._log_event("LIGHT", f"Light turned {'ON' if self.light_on else 'OFF'}.")
        if self.fan_on != prev_fan:
            self._log_event("FAN", f"Fan turned {'ON' if self.fan_on else 'OFF'}.")
        if self.security_alert and not prev_alert:
            self._log_event("INTRUDER_ALERT", "Motion detected while security mode ON.")
        if (not self.security_alert) and prev_alert:
            self._log_event("ALERT_CLEARED", "Security alert cleared.")

    def tick(self):
        with self.lock:
            self._apply_rules()

    def snapshot(self):
        return {
            "light_level": round(self.light_level, 1),
            "temperature": round(self.temperature, 1),
            "motion": self.motion,
            "security_mode": self.security_mode,
            "manual_override": self.manual_override,
            "manual_light": self.manual_light,
            "manual_fan": self.manual_fan,
            "light_on": self.light_on,
            "fan_on": self.fan_on,
            "buzzer": self.buzzer,
            "security_alert": self.security_alert,
            "status_message": self.status_message,
            "is_dark": self.light_level < DARK_THRESHOLD,
            "events": self.events[:15],
        }


home = SmartHomeState()


def background_ticker():
    while True:
        home.tick()
        time.sleep(1)

# 🏡 Smart Home Controller — Embedded Systems

A motion, light, and temperature-aware home automation controller with automatic lighting, temperature-based fan control, security alerting, and manual override — built as **both** real Arduino/ESP32 firmware and a **live interactive dashboard**.

![status](https://img.shields.io/badge/status-active-brightgreen) ![python](https://img.shields.io/badge/python-3.9+-blue) ![flask](https://img.shields.io/badge/flask-simulation-black) ![arduino](https://img.shields.io/badge/arduino-C%2FC%2B%2B-00979D) ![render](https://img.shields.io/badge/deployed-render-46E3B7)

**🔴 Live demo:** *(https://smart-home-controller-embedded-system.onrender.com)*

---

## 📌 Objective

Design a cost-effective, scalable home automation system that:
- Automatically controls lights based on motion + darkness
- Automatically controls a fan based on temperature (with hysteresis)
- Raises a security alert if motion is detected while security mode is armed
- Allows manual override of light/fan at any time
- Displays live status on an LCD/OLED and logs every event

## 🏭 Industry Relevance

This mirrors real systems from Google Nest, Amazon Alexa, Philips Hue, and Samsung SmartThings. Applicable across smart homes, offices, hotels, hospitals, and industrial building management systems — anywhere energy efficiency and automated safety monitoring matter.

## 🧠 Automation Logic (Priority Order)

```
1. SECURITY      — always wins. Motion + security armed = alarm, overrides everything.
2. MANUAL         — if no active alert, manual override takes control of light/fan.
3. AUTOMATIC      — otherwise, sensor-driven rules apply:
                     Light  = Motion AND Dark (light_level < 40%)
                     Fan    = Temperature > 28°C ON, < 26°C OFF (hysteresis)
```

## 🧩 Architecture

```
PIR Sensor ───────────┐
LDR ──────────────────┤
Temperature Sensor ───┤
Manual Switches ──────┤
Security Mode ────────┤
                      ↓
              Arduino / ESP32
                      ↓
              Control Algorithm
               ↓      ↓      ↓
             Light   Fan   Security
               ↓      ↓      ↓
             Relay   Relay  Buzzer
                      ↓
                 LCD / OLED
```

## 🛠 Hardware (Option B — Recommended)

| Component | Role |
|---|---|
| Arduino UNO / ESP32 | Microcontroller running the automation logic |
| PIR Motion Sensor | Detects human presence |
| LDR | Measures room brightness (voltage divider + ADC) |
| DHT11 / DHT22 | Temperature sensing |
| Relay Modules / LEDs | Light and fan actuation (low-voltage simulated loads) |
| Buzzer + Red LED | Security alarm indicators |
| 16x2 LCD | Live status display |
| Manual Switches | Security mode toggle, manual override, manual light/fan buttons |

Full firmware: [`arduino_code/smart_home_controller.ino`](./arduino_code/smart_home_controller.ino)

## 💻 Virtual Simulation (run this now — no hardware needed)

The dashboard mirrors the firmware's exact logic (`simulation/smart_home_state.py`), so what you see in the browser is what the real hardware would do.

**Features:**
- Illustrated room view with glowing lamp, spinning fan icon, and motion ripple animation
- Interactive sliders to simulate LDR (light level) and DHT (temperature) sensor readings
- One-click PIR motion trigger
- Security mode + manual override toggles, with per-device manual switches
- Live radial gauges for temperature and light level
- Live temperature history chart
- Real-time, timestamped event log

### Run locally in VS Code

```bash
cd simulation
pip install -r requirements.txt
python app.py
```

Open **http://localhost:5000**.

### Deploy on Render

`Procfile` and `render.yaml` are already set up.

1. Push this repo to GitHub.
2. On [render.com](https://render.com) → **New +** → **Web Service** → connect the repo.
3. If not auto-detected: Root Directory = `simulation`, Build Command = `pip install -r requirements.txt`, Start Command = `gunicorn app:app`.
4. Deploy, then paste your live `.onrender.com` URL into the top of this README.

> Free-tier note: Render's free plan spins down when idle, so the first load after inactivity can take 30–50 seconds, and `event_log.csv` resets on redeploy — expected behavior, not a bug.

## 📁 Folder Structure

```
Smart-Home-Controller-Embedded-System/
├── arduino_code/
│   └── smart_home_controller.ino   # Real hardware firmware
├── simulation/
│   ├── app.py                      # Flask backend + API
│   ├── smart_home_state.py         # Core automation state machine
│   ├── templates/dashboard.html    # Interactive dashboard UI
│   ├── requirements.txt
│   ├── Procfile
│   └── render.yaml
├── circuit_diagram/
├── test_cases/
├── docs/
├── reports/
├── screenshots/
└── README.md
```

## 🧪 Test Scenarios

```
| Scenario | Input | Expected Output |
|---|---|---|
| Bright room, no motion | light=80%, motion=off | Light OFF |
| Dark room + motion | light=20%, motion=trigger | Light ON |
| High temperature | temp=32°C | Fan ON |
| Normal temperature | temp=22°C | Fan OFF |
| Security armed + motion | security=on, motion=trigger | Alarm + red LED + "INTRUDER ALERT" |
| Manual override | manual=on, light=on | Light ON regardless of sensors |
```
👤 Author
VISHAL CHAPKE 
[GitHub] https://github.com/chapkevishal82-hue/Smart-Home-Controller-Embedded-System
[LinkedIn] https://www.linkedin.com/in/vishal-chapke-9bb3b0344?utm_source=share_via&utm_content=profile&utm_medium=member_android

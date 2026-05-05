# SereneHome — AI Smart Energy Optimisation Agent

> **Reinforcement Learning meets real-world IoT** — A Q-Learning agent that reads live sensor data from an Arduino Uno and autonomously decides which home appliances (AC, Geyser, Lights) to switch ON or OFF to balance comfort against energy cost.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0-black?style=flat-square&logo=flask)
![Arduino](https://img.shields.io/badge/Arduino-Uno-teal?style=flat-square&logo=arduino)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## Table of Contents

- [What This Project Does](#what-this-project-does)
- [System Architecture](#system-architecture)
- [How the RL Agent Works](#how-the-rl-agent-works)
- [Hardware Required](#hardware-required)
- [Wiring Guide](#wiring-guide)
- [Arduino Sketch](#arduino-sketch)
- [Project Structure](#project-structure)
- [Installation & Setup](#installation--setup)
- [Running the System](#running-the-system)
- [Frontend Pages](#frontend-pages)
- [API Reference](#api-reference)
- [State Space & Reward Design](#state-space--reward-design)
- [Team](#team)

---

## What This Project Does

SereneHome is an end-to-end smart home energy optimisation system built as an academic project (Subgroup 3F22). It uses **Q-Learning** (a model-free Reinforcement Learning algorithm) to learn the optimal policy for controlling three home appliances based on real-time environmental conditions:

| Sensor | Measures | Maps To |
|--------|----------|---------|
| DHT11 | Temperature (°C), Humidity (%) | `temperature` state: cold / comfortable / hot |
| RCWL-0516 | Microwave motion (occupancy) | `occupancy` state: occupied / empty |
| KY-018 LDR | Ambient light level | `light_level` state: dark / dim / bright |
| System clock | Time of day | `time_of_day` state: morning / afternoon / night |
| PSPCL tariff model | Electricity price tier | `electricity_price` state: cheap / moderate / expensive |

The agent picks one of **8 possible appliance combinations** every cycle and is rewarded or penalised based on energy efficiency and occupant comfort.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        HARDWARE LAYER                           │
│   DHT11 ──┐                                                     │
│  RCWL ────┼──► Arduino Uno ──USB──► PC                         │
│  KY-018 ──┘                                                     │
└─────────────────────────────────────────────────────────────────┘
                              │ Serial (9600 baud)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      run_real_system.py                         │
│   Reads JSON from COM port → HTTP POST → Flask /api/sensor_push │
└─────────────────────────────────────────────────────────────────┘
                              │ HTTP POST JSON
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         app.py (Flask)                          │
│                                                                 │
│  /api/sensor_push                                               │
│       │                                                         │
│       ├─► build_state_from_sensors()  [smart_home_environment]  │
│       │        └─► discrete MDP state dict                      │
│       │                                                         │
│       ├─► best_action(state)          [Q-table lookup]          │
│       │        └─► optimal appliance combination                │
│       │                                                         │
│       ├─► get_reward(state, action)   [reward function]         │
│       │                                                         │
│       ├─► online_update()             [live Q-learning]         │
│       │                                                         │
│       └─► log_to_db()                [SQLite]                   │
│                                                                 │
│  Background threads:                                            │
│    • train_agent_thread()     — offline warm-start (1000 eps)   │
│    • simulation_fallback()    — fires only when no hardware      │
└─────────────────────────────────────────────────────────────────┘
                              │ JSON polled every 5s
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Browser Frontend                            │
│   Dashboard │ AI Control │ Analytics │ History │ Insights       │
└─────────────────────────────────────────────────────────────────┘
```

**Key design decision:** The system uses a **warm-start** strategy — it pre-trains a Q-table offline on a simulated environment, then continuously refines it with real sensor data via online Q-learning. This means it works from Day 1 even before collecting real-world experience.

---

## How the RL Agent Works

### Q-Learning in one paragraph

The agent maintains a table (`Q_table`) mapping every (state, action) pair to an expected cumulative reward. At each step it either **explores** (picks a random action, probability = ε = 0.3) or **exploits** (picks the action with the highest Q-value). After receiving a reward it updates the table with:

```
Q(s,a) ← Q(s,a) + α × [r + γ × max Q(s',a') − Q(s,a)]
```

where α = 0.1 (learning rate) and γ = 0.9 (discount factor).

### State space

3 temperatures × 3 times × 2 occupancies × 3 price tiers = **54 discrete states**

### Action space

8 combinations of {AC ON/OFF} × {Geyser ON/OFF} × {Lights ON/OFF}

### Reward signal

| Condition | Reward |
|-----------|--------|
| All appliances off | +3 |
| Lights ON when occupied | +1 |
| AC ON when empty | −5 |
| Hot + occupied + AC OFF | −6 |
| Expensive tariff + AC ON | −3 |
| Expensive tariff + Geyser ON | −2 |
| Lights ON when empty | −2 |
| Geyser ON at night when occupied | +1.5 |

---

## Hardware Required

| Component | Quantity | Purpose |
|-----------|----------|---------|
| Arduino Uno (or compatible) | 1 | Microcontroller |
| DHT11 Temperature & Humidity Sensor | 1 | Reads temp + humidity |
| RCWL-0516 Microwave Radar Sensor | 1 | Detects room occupancy |
| KY-018 LDR Light Sensor Module | 1 | Measures ambient light |
| 10kΩ resistor | 1 | DHT11 pull-up |
| USB-A to USB-B cable | 1 | Arduino → PC |
| Jumper wires + breadboard | — | Connections |

---

## Wiring Guide

```
DHT11
  Pin 1 (VCC)  ──────────────── Arduino 5V
  Pin 2 (DATA) ──┬─────────────  Arduino Digital Pin 4
                 └── 10kΩ ──── Arduino 5V   ← pull-up resistor
  Pin 4 (GND)  ──────────────── Arduino GND

RCWL-0516
  VCC  ──────────────────────── Arduino 5V
  GND  ──────────────────────── Arduino GND
  OUT  ──────────────────────── Arduino Digital Pin 2

KY-018 LDR
  VCC  ──────────────────────── Arduino 5V
  GND  ──────────────────────── Arduino GND
  AO   ──────────────────────── Arduino A0
```

> **Note:** RCWL-0516 has a detection range of ~3–7 metres and can trigger through walls — place it facing the room entrance for best results.

---

## Arduino Sketch

Upload this to your Arduino Uno via Arduino IDE. The sketch reads all three sensors using non-blocking `millis()` timers and prints JSON to Serial every 8 seconds.

```cpp
/*
 * SmartEnergyAgent — Arduino Uno Sensor Sketch
 * Sensors: DHT11 (D4) | RCWL-0516 (D2) | KY-018 LDR (A0)
 * Output : JSON via Serial at 9600 baud every 8 seconds
 * Format : {"temp_c":31.5,"humidity":63.0,"occupied":true,"light_raw":720}
 *
 * Library required: DHT sensor library by Adafruit
 * Install via: Arduino IDE → Tools → Manage Libraries → search "DHT sensor"
 */

#include <DHT.h>

#define DHT_PIN   4
#define DHT_TYPE  DHT11
#define RCWL_PIN  2
#define LDR_PIN   A0

DHT dht(DHT_PIN, DHT_TYPE);

float   g_temp     = NAN;
float   g_humidity = NAN;
bool    g_occupied = false;
int     g_light    = 0;

uint8_t rcwl_high  = 0;
uint8_t rcwl_low   = 0;

unsigned long t_dht  = 0;
unsigned long t_send = 0;

void setup() {
  Serial.begin(9600);
  pinMode(RCWL_PIN, INPUT);
  dht.begin();
  delay(2000);  // DHT11 warm-up — one time only
}

void loop() {
  unsigned long now = millis();

  // Read DHT11 every 2 seconds
  if (now - t_dht >= 2000) {
    t_dht = now;
    float t = dht.readTemperature();
    float h = dht.readHumidity();
    if (!isnan(t) && !isnan(h)) { g_temp = t; g_humidity = h; }
  }

  // Poll RCWL with 3-reading debounce
  bool raw = digitalRead(RCWL_PIN) == HIGH;
  if (raw) { rcwl_high = min(rcwl_high+1,10); rcwl_low=0;
             if (rcwl_high >= 3) g_occupied = true; }
  else     { rcwl_low  = min(rcwl_low+1,10);  rcwl_high=0;
             if (rcwl_low  >= 3) g_occupied = false; }

  // Read LDR (invert: higher = brighter)
  g_light = 1023 - analogRead(LDR_PIN);

  // Send JSON every 8 seconds
  if (now - t_send >= 8000) {
    t_send = now;
    if (!isnan(g_temp)) {
      Serial.print("{\"temp_c\":"); Serial.print(g_temp, 1);
      Serial.print(",\"humidity\":"); Serial.print(g_humidity, 1);
      Serial.print(",\"occupied\":"); Serial.print(g_occupied ? "true":"false");
      Serial.print(",\"light_raw\":"); Serial.print(g_light);
      Serial.println("}");
    }
  }

  delay(200);
}
```

**After uploading:** Open Serial Monitor (baud 9600). You should see output like:
```
{"temp_c":31.5,"humidity":63.0,"occupied":false,"light_raw":720}
```
every 8 seconds. **Verify this works before starting the Python backend.**

---

## Project Structure

```
smart-energy-agent/
│
├── arduino/
│   └── uno_sensors.ino          ← Arduino sketch (upload this to Uno)
│
├── backend/
│   ├── templates/
│   │   ├── base.html            ← Shared layout (nav, header, Tailwind config)
│   │   ├── dashboard.html       ← Live sensor readings + AI decision
│   │   ├── ai_control.html      ← Manual appliance override controls
│   │   ├── analytics.html       ← Q-learning training curve + reward chart
│   │   ├── history.html         ← Paginated log of all sensor readings
│   │   └── insights.html        ← MDP state + sensor freshness display
│   │
│   ├── app.py                   ← Flask server (main entry point)
│   ├── smart_home_environment.py ← MDP: state space, actions, reward function
│   ├── q_learning_agent.py      ← Q-table, training loop, online update
│   ├── run_real_system.py       ← Serial bridge: Arduino COM → Flask POST
│   ├── energy_log.db            ← SQLite database (auto-created)
│   └── qtable.json              ← Pre-trained Q-table (auto-saved after training)
│
└── requirements.txt
```

---

## Installation & Setup

### Prerequisites

- Python 3.10 or higher
- Arduino IDE (for uploading the sketch)
- Arduino Uno connected via USB

### Step 1 — Clone the repository

```bash
git clone https://github.com/yashigauri/SmartEnergyAgent.git
cd SmartEnergyAgent/backend
```

### Step 2 — Create virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Mac / Linux
source .venv/bin/activate
```

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

`requirements.txt` contents:
```
Flask==3.0.0
flask-cors==4.0.0
pyserial==3.5
requests==2.31.0
```

### Step 4 — Upload Arduino sketch

1. Open Arduino IDE
2. Open `arduino/uno_sensors.ino`
3. Install **DHT sensor library by Adafruit** (Tools → Manage Libraries → search "DHT sensor library")
4. Select your board: Tools → Board → Arduino Uno
5. Select your COM port: Tools → Port → COM5 (or whatever appears)
6. Click Upload
7. Open Serial Monitor at 9600 baud — verify JSON output appears

### Step 5 — Set your COM port

Open `run_real_system.py` and change the port if needed:

```python
ser.port = 'COM5'   # Windows: COM3, COM4, COM5, etc.
                    # Mac/Linux: /dev/ttyUSB0 or /dev/ttyACM0
```

To find your port: Device Manager → Ports (Windows) or `ls /dev/tty*` (Mac/Linux).

---

## Running the System

You need **two terminals** open simultaneously:

### Terminal 1 — Start the Flask server

```bash
cd backend
python app.py
```

Expected output:
```
Server running at http://localhost:5000
  Training started...
  Episode  100 | Avg Reward (last 100):   12.34
  ...
```

The server starts offline Q-learning training in a background thread. The dashboard is immediately accessible even before training completes.

### Terminal 2 — Start the Arduino serial bridge

```bash
cd backend
python run_real_system.py
```

Expected output:
```
Connecting to COM5...
Connected to COM5!
Sending data to Flask...

Sent: {'temp_c': 31.5, 'humidity': 63.0, 'occupied': False}
```

### Open the dashboard

Go to: **http://127.0.0.1:5000/dashboard**

The Source indicator on the dashboard will show **`arduino`** once real sensor data is flowing, and **`simulated`** when no hardware is connected (the simulation fallback automatically takes over).

---

## Frontend Pages

| URL | Page | What it shows |
|-----|------|---------------|
| `/dashboard` | Dashboard | Live temp, humidity, occupancy, AI decision, recent readings table |
| `/ai-control` | AI Control | Manual ON/OFF/Auto toggle for each appliance |
| `/analytics` | Analytics | Q-learning training curve (episodes vs reward) + rolling reward bar chart |
| `/history-page` | History | Full paginated table of all logged sensor readings with search/filter |
| `/insights` | Insights | Current MDP state breakdown, sensor freshness bar, Q-table size |

All pages auto-refresh via JavaScript polling (every 2–8 seconds depending on page). No WebSocket required.

---

## API Reference

All endpoints return JSON.

### GET `/api/state`
Returns the current system snapshot.

```json
{
  "sensor": {
    "temp_c": 31.5,
    "humidity": 63.0,
    "occupied": false,
    "source": "arduino"
  },
  "state": {
    "temperature": "hot",
    "time_of_day": "afternoon",
    "occupancy": "empty",
    "electricity_price": "moderate",
    "_season": "summer"
  },
  "decision": {
    "action": "AC_OFF|GEYSER_OFF|LIGHTS_OFF",
    "reward": 3.0,
    "q_value": 20.72
  },
  "training_done": true,
  "q_states": 54,
  "sensor_age_s": 4.2
}
```

### POST `/api/sensor_push`
Receives sensor data (called by `run_real_system.py`).

```json
// Request body
{ "temp_c": 31.5, "humidity": 63.0, "occupied": false }

// Response
{ "ok": true }
```

### POST `/api/override`
Manually override an appliance (used by AI Control page).

```json
// Request body — set AC to ON
{ "appliance": "ac", "value": true }

// value: true = force ON, false = force OFF, null = return to AI control
```

### GET `/api/history?limit=30`
Returns the last N logged readings.

### GET `/api/training`
Returns Q-learning training progress (episode, avg_reward per 100 episodes).

### GET `/api/analytics`
Returns per-action statistics and recent reward trend.

### GET `/api/health`
Health check: `{ "status": "ok", "ts": "2025-05-01T14:22:00" }`

---

## State Space & Reward Design

### State variables

```python
{
  "temperature":       "cold" | "comfortable" | "hot",
  "time_of_day":       "morning" | "afternoon" | "night",
  "occupancy":         "occupied" | "empty",
  "electricity_price": "cheap" | "moderate" | "expensive"
}
```

### Temperature thresholds (tuned for Punjab/North India)

| Raw °C | Category |
|--------|----------|
| < 22°C | cold |
| 22–30°C | comfortable |
| > 30°C | hot |

### Electricity tariff model (approximate PSPCL tiers)

| Time | Tariff |
|------|--------|
| 18:00–22:59 | expensive (peak) |
| 10:00–17:59 | moderate (shoulder) |
| 00:00–09:59 | cheap (off-peak) |

### Fallback simulation

When no Arduino is connected (or data is older than 15 seconds), the server automatically generates simulated sensor readings so the system keeps working and the dashboard stays live. The source field will show `simulated` vs `arduino` so you always know which mode is active.

---

## Troubleshooting

**`serial.SerialException: [Errno 13] Permission denied`** (Linux/Mac)
```bash
sudo usermod -a -G dialout $USER   # then log out and back in
```

**`ModuleNotFoundError: No module named 'flask_cors'`**
```bash
pip install flask-cors
```

**Dashboard shows `—` everywhere**
- Make sure `app.py` is running first, then start `run_real_system.py`
- Check that your COM port is correct in `run_real_system.py`
- Open Serial Monitor in Arduino IDE to confirm the sketch is outputting JSON

**`json.JSONDecodeError` in run_real_system.py**
- The Arduino sketch takes ~10 seconds after power-on before first output (DHT11 warm-up + first 8s timer)
- Ensure baud rate matches: `9600` in both sketch and `run_real_system.py`

**DHT11 reads `nan`**
- Check the 10kΩ pull-up resistor is connected between DHT11 Data and 5V
- DHT11 needs 2 seconds after power-on before it gives valid readings

---

## Team

**Subgroup 3F22**

Built as part of an academic IoT + AI project demonstrating real-world reinforcement learning deployment on embedded hardware.

**Tech stack:** Python · Flask · SQLite · Q-Learning · Arduino C++ · Tailwind CSS · Vanilla JS

---

## License

MIT License — feel free to use, modify, and distribute with attribution.

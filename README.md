# SereneHome — Smart Energy Optimisation Agent

> A course project that combines IoT sensor input, a Flask dashboard, SQLite logging, and Q-Learning-style decision making to recommend ON/OFF states for AC, geyser, and lights.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Flask](https://img.shields.io/badge/Backend-Flask-green)
![SQLite](https://img.shields.io/badge/Database-SQLite-lightgrey)
![RL](https://img.shields.io/badge/AI-Q--Learning-purple)
![Hardware](https://img.shields.io/badge/Hardware-Arduino%20Serial-teal)

---

## Table of Contents

* [Overview](#overview)
* [What the Project Actually Does](#what-the-project-actually-does)
* [Technology Stack](#technology-stack)
* [System Architecture](#system-architecture)
* [Reinforcement Learning Logic](#reinforcement-learning-logic)
* [Sensor Input Format](#sensor-input-format)
* [Project Structure](#project-structure)
* [Installation and Setup](#installation-and-setup)
* [Running the Project](#running-the-project)
* [Dashboard Pages](#dashboard-pages)
* [API Endpoints](#api-endpoints)
* [Database Logging](#database-logging)
* [Known Limitations](#known-limitations)
* [Recommended Repository Cleanup](#recommended-repository-cleanup)
* [Future Improvements](#future-improvements)
* [Team](#team)

---

## Overview

**SereneHome** is an academic smart-home energy optimisation project. It takes environmental readings such as temperature, humidity, and occupancy, converts them into a discrete state, and selects an appliance-control action for three devices:

* AC
* Geyser
* Lights

The backend is built with Flask. It serves multiple dashboard pages, exposes JSON API endpoints, logs readings to SQLite, and uses Q-table based decision logic to choose appliance actions.

The project currently supports two input modes:

1. **Serial hardware input** through `run_real_system.py`, which reads JSON from a serial device connected on `COM5` by default.
2. **Simulation fallback** inside `app.py`, which generates sample readings when no fresh sensor data has been received.

---

## What the Project Actually Does

The project performs the following tasks:

* Runs a Flask web server.
* Starts a background Q-learning training thread inside `app.py`.
* Starts a simulation fallback thread when real sensor data is unavailable.
* Receives sensor readings through `/api/sensor_push`.
* Converts readings into a discrete state using `smart_home_environment.py`.
* Selects the best appliance action from an in-memory Q-table.
* Applies manual overrides for AC, geyser, and lights.
* Calculates reward using the reward function.
* Logs readings and decisions into `backend/energy_log.db`.
* Displays live state, history, analytics, and insights through HTML dashboard pages.

Important: the repository currently contains `q_learning_agent.py`, but the Flask app mainly contains its own Q-learning implementation inside `app.py`. So, for the web application, `app.py` is the main executable file.

---

## Technology Stack

| Layer                  | Technology                               |
| ---------------------- | ---------------------------------------- |
| Language               | Python                                   |
| Backend                | Flask                                    |
| CORS Support           | flask-cors                               |
| Hardware Communication | pyserial                                 |
| HTTP Client            | requests                                 |
| Database               | SQLite                                   |
| Frontend               | HTML templates served by Flask           |
| AI Method              | Tabular Q-Learning style policy learning |

Dependencies are listed in `requirements.txt`.

---

## System Architecture

```text
Serial Sensor Device / Arduino-compatible board
        │
        │ JSON over serial at 9600 baud
        ▼
backend/run_real_system.py
        │
        │ HTTP POST
        ▼
Flask Backend: backend/app.py
        │
        ├── Builds discrete state
        ├── Selects appliance action from Q-table
        ├── Applies manual overrides
        ├── Calculates reward
        ├── Logs data into SQLite
        └── Serves dashboard/API routes
        │
        ▼
Browser Dashboard
```

When the serial bridge is not sending fresh readings, the Flask app generates simulated readings so that the dashboard and APIs still work.

---

## Reinforcement Learning Logic

The project uses a tabular Q-learning approach.

### State Representation

A state is represented using four values:

| State Field         | Possible Values                  |
| ------------------- | -------------------------------- |
| `temperature`       | `cold`, `comfortable`, `hot`     |
| `time_of_day`       | `morning`, `afternoon`, `night`  |
| `occupancy`         | `occupied`, `empty`              |
| `electricity_price` | `cheap`, `moderate`, `expensive` |

Total possible states:

```text
3 × 3 × 2 × 3 = 54 states
```

### Temperature Mapping

The current code maps temperature as:

| Raw Temperature  | Category      |
| ---------------- | ------------- |
| `< 20°C`         | `cold`        |
| `20°C to < 28°C` | `comfortable` |
| `>= 28°C`        | `hot`         |

### Time Mapping

The current code maps time as:

| Hour          | Category    |
| ------------- | ----------- |
| `05:00–11:59` | `morning`   |
| `12:00–19:59` | `afternoon` |
| `20:00–04:59` | `night`     |

### Electricity Price Mapping

The current tariff model is a simple time-based approximation:

| Time          | Price Category |
| ------------- | -------------- |
| `18:00–22:59` | `expensive`    |
| `10:00–17:59` | `moderate`     |
| Other hours   | `cheap`        |

This is not a live electricity tariff integration. It is a manually coded approximation.

### Action Space

The action space contains all ON/OFF combinations for AC, geyser, and lights:

```text
AC_ON|GEYSER_ON|LIGHTS_ON
AC_ON|GEYSER_ON|LIGHTS_OFF
AC_ON|GEYSER_OFF|LIGHTS_ON
AC_ON|GEYSER_OFF|LIGHTS_OFF
AC_OFF|GEYSER_ON|LIGHTS_ON
AC_OFF|GEYSER_ON|LIGHTS_OFF
AC_OFF|GEYSER_OFF|LIGHTS_ON
AC_OFF|GEYSER_OFF|LIGHTS_OFF
```

Total actions:

```text
2 × 2 × 2 = 8 actions
```

### Training Parameters

The training parameters used in `app.py` are:

| Parameter                  |  Value |
| -------------------------- | -----: |
| Learning rate `ALPHA`      |  `0.1` |
| Discount factor `GAMMA`    |  `0.9` |
| Exploration rate `EPSILON` |  `0.3` |
| Episodes                   | `1000` |
| Steps per episode          |   `24` |

### Reward Function

The current reward function gives:

| Condition                                            | Reward / Penalty |
| ---------------------------------------------------- | ---------------: |
| AC, geyser, and lights are all OFF                   |             `+3` |
| Lights ON while occupied                             |             `+1` |
| AC or geyser ON during expensive price period        |             `-3` |
| AC ON while room is empty                            |             `-5` |
| AC OFF while temperature is hot and room is occupied |             `-6` |

---

## Sensor Input Format

`run_real_system.py` currently expects the serial device to output JSON using these keys:

```json
{
  "temp": 31.5,
  "hum": 63.0,
  "motion": 1
}
```

The script converts this into the format expected by Flask:

```json
{
  "temp_c": 31.5,
  "humidity": 63.0,
  "occupied": true
}
```

The serial bridge posts this converted payload to:

```text
http://127.0.0.1:5000/api/sensor_push
```

Current default serial settings:

| Setting   | Value      |
| --------- | ---------- |
| Port      | `COM5`     |
| Baud rate | `9600`     |
| Timeout   | `1 second` |

If your board uses a different port, update this line in `backend/run_real_system.py`:

```python
ser.port = 'COM5'
```

---

## Project Structure

Current visible repository structure:

```text
SmartEnergyAgent/
│
├── .venv/                  # Should not be committed
├── __pycache__/             # Should not be committed
├── backend/
│   ├── __pycache__/         # Should not be committed
│   ├── templates/
│   ├── app.py               # Main Flask backend and dashboard server
│   ├── energy_log.db        # Generated SQLite database; should not be committed
│   ├── q_learning_agent.py  # Standalone Q-learning training script
│   ├── run_real_system.py   # Serial-to-Flask bridge
│   └── smart_home_environment.py
│
├── energy_log.db            # Generated SQLite database; should not be committed
├── README.md
└── requirements.txt
```

There is currently no committed `arduino/` folder in the visible repository. If an Arduino sketch is part of the project, add it explicitly, for example:

```text
arduino/
└── uno_sensors.ino
```

---

## Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yashigauri/SmartEnergyAgent.git
cd SmartEnergyAgent
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
```

Activate it:

**Windows**

```bash
.venv\Scripts\activate
```

**macOS / Linux**

```bash
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Running the Project

### Terminal 1 — Start the Flask App

From the repository root:

```bash
cd backend
python app.py
```

Expected server URL:

```text
http://127.0.0.1:5000/dashboard
```

The Flask app starts:

* the web server,
* a background training thread,
* a simulation fallback thread.

### Terminal 2 — Start the Serial Bridge

Open a second terminal:

```bash
cd backend
python run_real_system.py
```

This script reads serial JSON from the configured COM port and posts it to the Flask backend.

If no serial data is available, the Flask app can still run using simulated readings.

---

## Dashboard Pages

| Route           | Purpose                        |
| --------------- | ------------------------------ |
| `/`             | Opens the dashboard            |
| `/dashboard`    | Main live dashboard            |
| `/ai-control`   | Manual appliance override page |
| `/analytics`    | Analytics page                 |
| `/history-page` | History page                   |
| `/insights`     | Insights page                  |

---

## API Endpoints

| Endpoint                | Method | Purpose                                                                         |
| ----------------------- | ------ | ------------------------------------------------------------------------------- |
| `/api/state`            | GET    | Returns latest sensor, state, decision, training, override, and sensor-age data |
| `/api/live`             | GET    | Returns the same live state snapshot as `/api/state`                            |
| `/api/sensor_push`      | POST   | Accepts sensor readings from the serial bridge                                  |
| `/api/override`         | POST   | Sets manual override for `ac`, `geyser`, or `lights`                            |
| `/api/training`         | GET    | Returns training log data                                                       |
| `/api/history?limit=30` | GET    | Returns recent readings from SQLite                                             |
| `/api/analytics`        | GET    | Returns action statistics and reward trend                                      |

### Example `/api/sensor_push` Request

```json
{
  "temp_c": 31.5,
  "humidity": 63.0,
  "occupied": true
}
```

### Example `/api/override` Request

```json
{
  "appliance": "ac",
  "value": true
}
```

Override values:

| Value   | Meaning                               |
| ------- | ------------------------------------- |
| `true`  | Force appliance ON                    |
| `false` | Force appliance OFF                   |
| `null`  | Return appliance to automatic control |

---

## Database Logging

The Flask app creates and uses a SQLite database named:

```text
backend/energy_log.db
```

The logged fields include:

* timestamp
* temperature
* humidity
* occupancy
* season
* temperature category
* time of day
* occupancy category
* electricity price category
* selected action
* reward
* Q-value

This database is generated at runtime and should not be committed to Git.

---

## Known Limitations

These are not weaknesses to hide. They are important for honest course-project documentation.

1. **The repository currently does not include an Arduino sketch.**
   `run_real_system.py` expects serial JSON, but the code that produces that JSON is not committed.

2. **The serial input keys and Flask API keys are different.**
   The serial bridge expects `temp`, `hum`, and `motion`, then converts them to `temp_c`, `humidity`, and `occupied`.

3. **The project does not physically switch appliances.**
   It recommends/outputs appliance states in software. No relay-control code is currently included.

4. **The electricity price model is not a real tariff API.**
   It is a simple time-based rule coded in `smart_home_environment.py`.

5. **The web app uses an in-memory Q-table.**
   The Q-table is trained at runtime and is not persisted as a committed model file.

6. **`q_learning_agent.py` is mostly standalone.**
   The Flask app has its own training logic inside `app.py` instead of directly using `q_learning_agent.py`.

7. **Generated files are committed.**
   `.venv`, `__pycache__`, and SQLite database files should be removed from Git tracking.

---

## Recommended Repository Cleanup

Add this `.gitignore` file:

```gitignore
.venv/
__pycache__/
*/__pycache__/
*.pyc
*.pyo
*.pyd
.env
.DS_Store
energy_log.db
backend/energy_log.db
```

Then remove generated files from Git tracking:

```bash
git rm -r --cached .venv __pycache__ backend/__pycache__
git rm --cached energy_log.db backend/energy_log.db
git add .gitignore README.md
git commit -m "Clean repository and update README"
git push
```

If Git says a file path does not exist, remove that path from the command and run it again.

---

## Future Improvements

* Add the missing Arduino sketch to the repository.
* Make the serial JSON format consistent across Arduino, `run_real_system.py`, and `/api/sensor_push`.
* Add relay-control support if actual appliance switching is required.
* Persist the trained Q-table to a JSON or pickle file.
* Move duplicated Q-learning logic into one reusable module.
* Add tests for the reward function and state-conversion logic.
* Replace the hardcoded electricity price rule with a configurable tariff table.
* Add screenshots of the dashboard for easier evaluation.

---

## Team

**Subgroup 3F22**

Academic course project on smart-home energy optimisation using IoT sensor readings and Q-learning-style decision logic.

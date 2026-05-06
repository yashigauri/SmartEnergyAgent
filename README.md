# SereneHome — Smart Energy Optimisation Agent

SereneHome is a course project that uses sensor readings, Flask, SQLite, and Q-learning-style logic to recommend energy-efficient ON/OFF states for AC, geyser, and lights.

---

## Overview

The system takes temperature, humidity, and occupancy readings, converts them into a smart-home state, and selects an appliance action using a Q-table based policy.

It includes:

- Flask web dashboard
- SQLite-based history logging
- Serial sensor input support
- Simulation fallback when live sensor data is unavailable
- Manual override for appliances
- Q-learning-style action selection

---

## Tech Stack

| Component | Technology |
|---|---|
| Backend | Flask |
| Language | Python |
| Database | SQLite |
| Sensor Communication | Serial + HTTP POST |
| AI Logic | Tabular Q-learning-style policy |
| Frontend | HTML templates |

---

## Workflow

```text
Sensor / Serial Input
        ↓
Flask Backend
        ↓
State Conversion
        ↓
Q-table Action Selection
        ↓
Dashboard + SQLite Log
```

The serial bridge reads sensor data and sends it to the Flask backend. The backend then updates the dashboard, records the reading, and shows the recommended appliance state.

---

## Q-Learning Logic

The system uses a discrete state made from:

- Temperature: `cold`, `comfortable`, `hot`
- Time of day: `morning`, `afternoon`, `night`
- Occupancy: `occupied`, `empty`
- Electricity price: `cheap`, `moderate`, `expensive`

The action space contains all ON/OFF combinations for:

- AC
- Geyser
- Lights

Total actions:

```text
2 × 2 × 2 = 8
```

The reward logic encourages energy-saving decisions while avoiding uncomfortable or wasteful appliance usage.

> The current system uses Q-learning-style training and live sensor-based decision making. It is designed as a course-level smart energy optimisation prototype.

---

## Project Structure

```text
SmartEnergyAgent/
│
├── backend/
│   ├── templates/
│   ├── app.py
│   ├── q_learning_agent.py
│   ├── run_real_system.py
│   ├── smart_home_environment.py
│   └── energy_log.db
│
├── requirements.txt
└── README.md
```

---

## Setup

Clone the repository:

```bash
git clone https://github.com/yashigauri/SmartEnergyAgent.git
cd SmartEnergyAgent
```

Create a virtual environment:

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

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Run the Project

Start the Flask app:

```bash
cd backend
python app.py
```

Open the dashboard:

```text
http://127.0.0.1:5000/dashboard
```

For live serial input, run this in another terminal:

```bash
cd backend
python run_real_system.py
```

If live sensor data is not available, the app continues with simulated readings.

---

## Main Pages

| Page | Route |
|---|---|
| Dashboard | `/dashboard` |
| AI Control | `/ai-control` |
| Analytics | `/analytics` |
| History | `/history-page` |
| Insights | `/insights` |

---

## API Endpoints

| Endpoint | Purpose |
|---|---|
| `/api/state` | Returns current sensor state and AI decision |
| `/api/sensor_push` | Receives sensor data |
| `/api/override` | Applies manual appliance override |
| `/api/history` | Returns recent logged readings |
| `/api/analytics` | Returns reward and action statistics |

---


---

## Team

**Subgroup 3F22**

Course project on smart-home energy optimisation using sensor readings and Q-learning-style decision logic.

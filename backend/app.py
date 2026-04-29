import threading
import time
import datetime
import random
import sqlite3
import os

from flask import Flask, jsonify, request, render_template
from flask_cors import CORS

from smart_home_environment import (
    actions, get_reward, build_state_from_sensors,
    temperature_options, time_options, occupancy_options
)

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "energy_log.db")   # FIX: was relative → breaks if cwd changes

app = Flask(__name__, template_folder=os.path.join(BASE_DIR, "templates"))
CORS(app)

# ── Shared state ───────────────────────────────────────────────────────────────
lock = threading.Lock()

latest_sensor   = {"temp_c": None, "humidity": None, "occupied": None, "source": "waiting"}
latest_state    = {}
latest_decision = {"action": "—", "reward": 0, "q_value": 0}
training_log    = []
Q_table         = {}
training_done   = False
last_sensor_ts  = None
manual_overrides = {"ac": None, "geyser": None, "lights": None}

VALID_APPLIANCES = {"ac", "geyser", "lights"}   # FIX: whitelist for override validation

# ── UI Routes ──────────────────────────────────────────────────────────────────
@app.route("/")
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/ai-control")
def ai_control():
    return render_template("ai_control.html")

@app.route("/analytics")
def analytics():
    return render_template("analytics.html")

@app.route("/history-page")          # FIX: kept distinct name to avoid clash with /api/history
def history_page():
    return render_template("history.html")

@app.route("/insights")
def insights():
    return render_template("insights.html")


# ── Database ───────────────────────────────────────────────────────────────────
def init_db():
    con = sqlite3.connect(DB_PATH)
    con.execute("""
        CREATE TABLE IF NOT EXISTS readings (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            ts        TEXT,
            temp_c    REAL,
            humidity  REAL,
            occupied  INTEGER,
            season    TEXT,
            temp_cat  TEXT,
            time_of_day TEXT,
            occupancy TEXT,
            price     TEXT,
            action    TEXT,
            reward    REAL,
            q_value   REAL
        )
    """)
    con.commit()
    con.close()


def log_to_db(sensor, state, decision):
    # FIX: column list (12) and VALUES placeholders (12) now match exactly
    try:
        con = sqlite3.connect(DB_PATH)
        con.execute(
            """INSERT INTO readings
               (ts, temp_c, humidity, occupied, season, temp_cat,
                time_of_day, occupancy, price, action, reward, q_value)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                datetime.datetime.now().isoformat(),
                sensor.get("temp_c"),
                sensor.get("humidity"),
                1 if sensor.get("occupied") else 0,
                state.get("_season", ""),
                state.get("temperature"),          # stored in temp_cat column
                state.get("time_of_day"),
                state.get("occupancy"),
                state.get("electricity_price"),
                decision.get("action"),
                decision.get("reward"),
                decision.get("q_value"),
            ),
        )
        con.commit()
        con.close()
    except Exception as e:
        print(f"DB error: {e}")


def get_history(limit: int = 30):
    con  = sqlite3.connect(DB_PATH)
    rows = con.execute(
        """SELECT ts, temp_c, humidity, occupied, season,
                  occupancy, price, action, reward
           FROM   readings
           ORDER  BY id DESC
           LIMIT  ?""",
        (limit,),
    ).fetchall()
    con.close()
    keys = ["ts", "temp_c", "humidity", "occupied", "season",
            "occupancy", "price", "action", "reward"]
    return [dict(zip(keys, r)) for r in rows]


def get_analytics_summary():
    """Aggregate stats used by the /analytics page."""
    con = sqlite3.connect(DB_PATH)
    rows = con.execute(
        """SELECT action, COUNT(*) as cnt,
                  AVG(reward) as avg_reward,
                  SUM(CASE WHEN reward > 0 THEN 1 ELSE 0 END) as positive
           FROM   readings
           GROUP  BY action"""
    ).fetchall()
    recent = con.execute(
        """SELECT ts, reward FROM readings ORDER BY id DESC LIMIT 50"""
    ).fetchall()
    con.close()

    action_stats = [
        {"action": r[0], "count": r[1],
         "avg_reward": round(r[2], 3), "positive": r[3]}
        for r in rows
    ]
    reward_trend = [{"ts": r[0], "reward": r[1]} for r in recent]
    return {"action_stats": action_stats, "reward_trend": reward_trend}


# ── Reinforcement Learning ─────────────────────────────────────────────────────
ALPHA           = 0.1
GAMMA           = 0.9
EPSILON         = 0.3
EPISODES        = 1000
STEPS_PER_EPISODE = 24


def state_to_key(state: dict) -> tuple:
    return (
        state["temperature"],
        state["time_of_day"],
        state["occupancy"],
        state["electricity_price"],
    )


def get_q(sk: tuple, ai: int) -> float:
    if sk not in Q_table:
        Q_table[sk] = [0.0] * len(actions)
    return Q_table[sk][ai]


def set_q(sk: tuple, ai: int, v: float):
    if sk not in Q_table:
        Q_table[sk] = [0.0] * len(actions)
    Q_table[sk][ai] = v


def choose_action_epsilon(sk: tuple) -> int:
    if random.random() < EPSILON or sk not in Q_table:
        return random.randint(0, len(actions) - 1)
    return Q_table[sk].index(max(Q_table[sk]))


def random_train_state() -> dict:
    return {
        "temperature":       random.choice(temperature_options),
        "time_of_day":       random.choice(time_options),
        "occupancy":         random.choice(occupancy_options),
        "electricity_price": random.choice(["cheap", "moderate", "expensive"]),
    }


def best_action(state: dict):
    sk = state_to_key(state)
    if sk not in Q_table:
        return actions[random.randint(0, len(actions) - 1)], 0.0
    ai = Q_table[sk].index(max(Q_table[sk]))
    return actions[ai], round(max(Q_table[sk]), 3)


def apply_overrides(action_str: str, overrides: dict) -> str:
    parts = {
        "ac":     "AC_ON"     if "AC_ON"     in action_str else "AC_OFF",
        "geyser": "GEYSER_ON" if "GEYSER_ON" in action_str else "GEYSER_OFF",
        "lights": "LIGHTS_ON" if "LIGHTS_ON" in action_str else "LIGHTS_OFF",
    }
    for appliance, val in overrides.items():
        if val is True:
            parts[appliance] = appliance.upper() + "_ON"
        elif val is False:
            parts[appliance] = appliance.upper() + "_OFF"
    return f"{parts['ac']}|{parts['geyser']}|{parts['lights']}"


# ── Background Threads ─────────────────────────────────────────────────────────
def train_agent_thread():
    global training_done
    episode_rewards = []

    for episode in range(1, EPISODES + 1):
        state = random_train_state()
        total = 0

        for _ in range(STEPS_PER_EPISODE):
            sk = state_to_key(state)
            ai = choose_action_epsilon(sk)

            r      = get_reward(state, actions[ai])
            total += r

            nxt = random_train_state()
            nsk = state_to_key(nxt)

            cq = get_q(sk, ai)
            mq = max(Q_table.get(nsk, [0.0] * len(actions)))
            set_q(sk, ai, cq + ALPHA * (r + GAMMA * mq - cq))
            state = nxt

        episode_rewards.append(total)

        if episode % 100 == 0:
            avg = sum(episode_rewards[-100:]) / 100
            with lock:
                training_log.append({"episode": episode, "avg_reward": round(avg, 2)})

    training_done = True
    print("Training complete!")


def simulation_fallback_thread():
    # FIX: declare all globals at the TOP of the function, before any logic
    global latest_sensor, latest_state, latest_decision, last_sensor_ts

    while True:
        time.sleep(8)

        with lock:
            stale = last_sensor_ts is None or (time.time() - last_sensor_ts) > 15

        if not stale:
            continue

        now      = datetime.datetime.now()
        temp_c   = round(28 + random.uniform(-3, 3), 1)
        humidity = round(random.uniform(50, 75), 1)
        occupied = 8 <= now.hour < 22

        state         = build_state_from_sensors(temp_c, humidity, occupied, now)
        action, qv    = best_action(state)

        # FIX: read overrides inside the lock so we get a consistent snapshot
        with lock:
            ov = manual_overrides.copy()

        final_action = apply_overrides(action, ov)
        reward       = get_reward(state, final_action)

        sensor   = {"temp_c": temp_c, "humidity": humidity,
                    "occupied": occupied, "source": "simulated"}
        decision = {"action": final_action, "reward": round(reward, 2), "q_value": qv}

        with lock:
            latest_sensor   = sensor
            latest_state    = state
            latest_decision = decision
            last_sensor_ts  = time.time()   # FIX: keep timestamp fresh for simulated ticks too

        log_to_db(sensor, state, decision)


# ── Shared state snapshot (used by multiple API routes) ───────────────────────
def _state_snapshot() -> dict:
    """Return a consistent copy of shared state under the lock."""
    with lock:
        return {
            "sensor":       dict(latest_sensor),
            "state":        dict(latest_state),
            "decision":     dict(latest_decision),
            "training_done": training_done,
            "q_states":     len(Q_table),
            "overrides":    dict(manual_overrides),
            "sensor_age_s": (
                round(time.time() - last_sensor_ts, 1)
                if last_sensor_ts else None
            ),
        }


# ── API Routes ─────────────────────────────────────────────────────────────────
@app.route("/api/state")
def api_state():
    return jsonify(_state_snapshot())


@app.route("/api/live")
def api_live():
    # FIX: was calling the route function directly; now calls shared helper instead
    return jsonify(_state_snapshot())


@app.route("/api/sensor_push", methods=["POST"])
def sensor_push():
    # FIX: all globals declared at the TOP of the function
    global latest_sensor, latest_state, latest_decision, last_sensor_ts

    data     = request.get_json(force=True)
    temp_c   = float(data["temp_c"])
    humidity = float(data["humidity"])
    occupied = bool(data.get("occupied", False))

    now   = datetime.datetime.now()
    state = build_state_from_sensors(temp_c, humidity, occupied, now)

    # FIX: read manual_overrides inside the lock for thread-safety
    with lock:
        ov = manual_overrides.copy()

    action, qv   = best_action(state)
    final_action = apply_overrides(action, ov)
    reward       = get_reward(state, final_action)

    sensor   = {"temp_c": temp_c, "humidity": humidity,
                "occupied": occupied, "source": "esp8266"}
    decision = {"action": final_action, "reward": round(reward, 2), "q_value": qv}

    with lock:
        last_sensor_ts  = time.time()
        latest_sensor   = sensor
        latest_state    = state
        latest_decision = decision

    log_to_db(sensor, state, decision)
    return jsonify({"ok": True})


@app.route("/api/override", methods=["POST"])
def api_override():
    data      = request.get_json(force=True)
    appliance = data.get("appliance")
    value     = data.get("value")          # True | False | None

    # FIX: validate appliance to prevent arbitrary key injection
    if appliance not in VALID_APPLIANCES:
        return jsonify({"ok": False, "error": f"Unknown appliance '{appliance}'"}), 400

    if value is not None and not isinstance(value, bool):
        return jsonify({"ok": False, "error": "value must be true, false, or null"}), 400

    with lock:
        manual_overrides[appliance] = value

    return jsonify({"ok": True, "appliance": appliance, "value": value})


@app.route("/api/training")
def api_training():
    # FIX: return a copy so the caller can't mutate the live list
    with lock:
        snapshot = list(training_log)
    return jsonify(snapshot)


@app.route("/api/history")
def api_history():
    limit = request.args.get("limit", 30, type=int)
    limit = max(1, min(limit, 500))    # clamp between 1 and 500
    return jsonify(get_history(limit))


@app.route("/api/analytics")
def api_analytics():
    return jsonify(get_analytics_summary())


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    threading.Thread(target=train_agent_thread,        daemon=True).start()
    threading.Thread(target=simulation_fallback_thread, daemon=True).start()

    print("Server running at http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)